import docker
from docker.errors import DockerException, NotFound, APIError
from typing import Optional, List, Dict, Any
import structlog

from sandbox.schemas import ContainerStatus

logger = structlog.get_logger(__name__)


class DockerClient:
    def __init__(self, host: str = "unix:///var/run/docker.sock"):
        self.client = docker.DockerClient(base_url=host)
        self._verify_connection()

    def _verify_connection(self) -> None:
        try:
            self.client.ping()
            logger.info("Docker client connected successfully")
        except DockerException as e:
            logger.error("Failed to connect to Docker", error=str(e))
            raise

    def create_container(
        self,
        image: str,
        name: str,
        network: str,
        environment: Optional[Dict[str, str]] = None,
        ports: Optional[Dict[str, int]] = None,
        volumes: Optional[Dict[str, Dict[str, str]]] = None,
        cpu_limit: Optional[str] = None,
        memory_limit: Optional[str] = None,
        command: Optional[str] = None,
        detach: bool = True,
    ) -> docker.models.containers.Container:
        try:
            host_config = self.client.api.create_host_config(
                network_mode=network,
                cpu_quota=int(float(cpu_limit) * 100000) if cpu_limit else None,
                mem_limit=memory_limit,
                port_bindings={f"{port}/tcp": host_port for port, host_port in (ports or {}).items()} if ports else None,
                binds=[f"{host}:{container}:{mode}" for host, config in (volumes or {}).items() for container, mode in [(config.get("bind"), config.get("mode", "rw"))]] if volumes else None,
            )

            container = self.client.api.create_container(
                image=image,
                name=name,
                environment=environment,
                host_config=host_config,
                command=command,
                detach=detach,
            )

            container_obj = self.client.containers.get(container["Id"])
            logger.info("Container created", container_id=container_obj.id[:12], name=name)
            return container_obj

        except APIError as e:
            logger.error("Failed to create container", name=name, error=str(e))
            raise

    def start_container(self, container_id: str) -> bool:
        try:
            container = self.client.containers.get(container_id)
            container.start()
            logger.info("Container started", container_id=container_id[:12])
            return True
        except (NotFound, APIError) as e:
            logger.error("Failed to start container", container_id=container_id[:12], error=str(e))
            return False

    def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            logger.info("Container stopped", container_id=container_id[:12])
            return True
        except (NotFound, APIError) as e:
            logger.error("Failed to stop container", container_id=container_id[:12], error=str(e))
            return False

    def remove_container(self, container_id: str, force: bool = False) -> bool:
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            logger.info("Container removed", container_id=container_id[:12])
            return True
        except (NotFound, APIError) as e:
            logger.error("Failed to remove container", container_id=container_id[:12], error=str(e))
            return False

    def get_container_status(self, container_id: str) -> Optional[ContainerStatus]:
        try:
            container = self.client.containers.get(container_id)
            container.reload()
            return ContainerStatus(
                id=container.id,
                name=container.name,
                status=container.status,
                image=container.image.tags[0] if container.image.tags else "unknown",
                created_at=container.attrs["Created"],
                started_at=container.attrs["State"].get("StartedAt"),
                finished_at=container.attrs["State"].get("FinishedAt"),
                exit_code=container.attrs["State"].get("ExitCode"),
                ports=container.attrs["NetworkSettings"]["Ports"],
            )
        except NotFound:
            return None
        except APIError as e:
            logger.error("Failed to get container status", container_id=container_id[:12], error=str(e))
            return None

    def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, stdout=True, stderr=True).decode("utf-8")
            return logs
        except (NotFound, APIError) as e:
            logger.error("Failed to get container logs", container_id=container_id[:12], error=str(e))
            return ""

    def exec_command(self, container_id: str, command: List[str]) -> tuple[int, str, str]:
        try:
            container = self.client.containers.get(container_id)
            exec_result = container.exec_run(command, stdout=True, stderr=True, demux=True)
            stdout = exec_result.output[0].decode("utf-8") if exec_result.output[0] else ""
            stderr = exec_result.output[1].decode("utf-8") if exec_result.output[1] else ""
            return exec_result.exit_code, stdout, stderr
        except (NotFound, APIError) as e:
            logger.error("Failed to exec command", container_id=container_id[:12], error=str(e))
            return -1, "", str(e)

    def commit_container(self, container_id: str, repository: str, tag: str = "latest") -> str:
        try:
            container = self.client.containers.get(container_id)
            image = container.commit(repository=repository, tag=tag)
            logger.info("Container committed", image_id=image.id[:12], repository=repository, tag=tag)
            return image.id
        except (NotFound, APIError) as e:
            logger.error("Failed to commit container", container_id=container_id[:12], error=str(e))
            raise

    def list_containers(self, filters: Optional[Dict[str, Any]] = None) -> List[docker.models.containers.Container]:
        return self.client.containers.list(all=True, filters=filters)

    def pull_image(self, image: str, tag: str = "latest") -> docker.models.images.Image:
        try:
            image_obj = self.client.images.pull(image, tag=tag)
            logger.info("Image pulled", image=f"{image}:{tag}")
            return image_obj
        except APIError as e:
            logger.error("Failed to pull image", image=f"{image}:{tag}", error=str(e))
            raise

    def image_exists(self, image: str, tag: str = "latest") -> bool:
        try:
            self.client.images.get(f"{image}:{tag}")
            return True
        except NotFound:
            return False