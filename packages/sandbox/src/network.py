import structlog
from typing import Optional, List, Dict, Any

from sandbox.docker_client import DockerClient

logger = structlog.get_logger(__name__)


class NetworkManager:
    def __init__(self, docker_client: DockerClient):
        self.docker_client = docker_client

    def create_isolated_network(self, name: str, driver: str = "bridge", internal: bool = True) -> Optional[str]:
        try:
            network = self.docker_client.client.networks.create(
                name=name,
                driver=driver,
                internal=internal,
                enable_ipv6=False,
                attachable=True,
            )
            logger.info("Isolated network created", network_id=network.id[:12], name=name, internal=internal)
            return network.id
        except Exception as e:
            logger.error("Failed to create isolated network", name=name, error=str(e))
            return None

    def connect_container(self, container_id: str, network_id: str, aliases: Optional[List[str]] = None) -> bool:
        try:
            network = self.docker_client.client.networks.get(network_id)
            network.connect(container_id, aliases=aliases)
            logger.info("Container connected to network", container_id=container_id[:12], network_id=network_id[:12])
            return True
        except Exception as e:
            logger.error("Failed to connect container to network", container_id=container_id[:12], network_id=network_id[:12], error=str(e))
            return False

    def disconnect_container(self, container_id: str, network_id: str) -> bool:
        try:
            network = self.docker_client.client.networks.get(network_id)
            network.disconnect(container_id)
            logger.info("Container disconnected from network", container_id=container_id[:12], network_id=network_id[:12])
            return True
        except Exception as e:
            logger.error("Failed to disconnect container from network", container_id=container_id[:12], network_id=network_id[:12], error=str(e))
            return False

    def ensure_no_egress(self, container_id: str) -> bool:
        try:
            container = self.docker_client.client.containers.get(container_id)
            for network_name, network_info in container.attrs["NetworkSettings"]["Networks"].items():
                network = self.docker_client.client.networks.get(network_info["NetworkID"])
                if not network.attrs.get("Internal", False):
                    logger.warning("Container connected to non-internal network", container_id=container_id[:12], network=network_name)
                    return False
            return True
        except Exception as e:
            logger.error("Failed to verify network isolation", container_id=container_id[:12], error=str(e))
            return False

    def cleanup_network(self, network_id: str) -> bool:
        try:
            network = self.docker_client.client.networks.get(network_id)
            network.remove()
            logger.info("Network removed", network_id=network_id[:12])
            return True
        except Exception as e:
            logger.error("Failed to remove network", network_id=network_id[:12], error=str(e))
            return False