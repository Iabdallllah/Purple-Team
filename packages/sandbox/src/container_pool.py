import asyncio
from collections import deque
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import structlog

from sandbox.docker_client import DockerClient
from sandbox.schemas import ContainerStatus, SandboxConfig

logger = structlog.get_logger(__name__)


@dataclass
class PooledContainer:
    container_id: str
    target_type: str
    in_use: bool = False
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())


class ContainerPool:
    def __init__(
        self,
        docker_client: DockerClient,
        max_containers: int = 10,
        default_cpu_limit: str = "2",
        default_memory_limit: str = "4g",
        network: str = "purple-network",
    ):
        self.docker_client = docker_client
        self.max_containers = max_containers
        self.default_cpu_limit = default_cpu_limit
        self.default_memory_limit = default_memory_limit
        self.network = network
        self._pools: Dict[str, deque[PooledContainer]] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, target_type: str, config: SandboxConfig) -> Optional[str]:
        async with self._lock:
            if target_type not in self._pools:
                self._pools[target_type] = deque()

            pool = self._pools[target_type]

            while pool:
                pooled = pool.popleft()
                status = self.docker_client.get_container_status(pooled.container_id)
                if status and status.status == "running":
                    pooled.in_use = True
                    logger.info("Acquired container from pool", container_id=pooled.container_id[:12], target_type=target_type)
                    return pooled.container_id
                else:
                    logger.warning("Container in pool is not running, removing", container_id=pooled.container_id[:12])

            if sum(len(p) for p in self._pools.values()) >= self.max_containers:
                logger.warning("Max containers reached, cannot create new one", max_containers=self.max_containers)
                return None

            return await self._create_new_container(target_type, config)

    async def _create_new_container(self, target_type: str, config: SandboxConfig) -> Optional[str]:
        try:
            target_config = config.get_target_config(target_type)
            if not target_config:
                logger.error("Unknown target type", target_type=target_type)
                return None

            container = self.docker_client.create_container(
                image=target_config.docker_image,
                name=f"purple-{target_type}-{asyncio.get_event_loop().time():.0f}",
                network=self.network,
                environment=target_config.environment,
                ports=target_config.exposed_ports,
                cpu_limit=self.default_cpu_limit,
                memory_limit=self.default_memory_limit,
            )

            if self.docker_client.start_container(container.id):
                logger.info("Created and started new container", container_id=container.id[:12], target_type=target_type)
                return container.id
            else:
                self.docker_client.remove_container(container.id, force=True)
                return None

        except Exception as e:
            logger.error("Failed to create new container", target_type=target_type, error=str(e))
            return None

    async def release(self, container_id: str, target_type: str) -> bool:
        async with self._lock:
            status = self.docker_client.get_container_status(container_id)
            if not status or status.status != "running":
                logger.warning("Cannot release container, not running", container_id=container_id[:12])
                await self._cleanup_container(container_id)
                return False

            if target_type not in self._pools:
                self._pools[target_type] = deque()

            self._pools[target_type].append(PooledContainer(container_id=container_id, target_type=target_type))
            logger.info("Released container back to pool", container_id=container_id[:12], target_type=target_type)
            return True

    async def _cleanup_container(self, container_id: str) -> None:
        self.docker_client.stop_container(container_id)
        self.docker_client.remove_container(container_id, force=True)

    async def pre_warm(self, target_types: List[str], config: SandboxConfig, count: int = 2) -> Dict[str, int]:
        results = {}
        for target_type in target_types:
            created = 0
            for _ in range(count):
                container_id = await self._create_new_container(target_type, config)
                if container_id:
                    await self.release(container_id, target_type)
                    created += 1
            results[target_type] = created
        return results

    async def cleanup_all(self) -> None:
        async with self._lock:
            for target_type, pool in self._pools.items():
                while pool:
                    pooled = pool.popleft()
                    await self._cleanup_container(pooled.container_id)
            self._pools.clear()
            logger.info("All containers cleaned up")

    def get_pool_stats(self) -> Dict[str, Dict[str, int]]:
        stats = {}
        for target_type, pool in self._pools.items():
            stats[target_type] = {
                "available": len(pool),
                "in_use": sum(1 for p in pool if p.in_use),
            }
        return stats