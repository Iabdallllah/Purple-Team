import structlog
from typing import Optional, Dict, Any

from sandbox.docker_client import DockerClient
from sandbox.schemas import SnapshotInfo

logger = structlog.get_logger(__name__)


class SnapshotManager:
    def __init__(self, docker_client: DockerClient):
        self.docker_client = docker_client

    def create_snapshot(self, container_id: str, repository: str, tag: str = "latest") -> Optional[SnapshotInfo]:
        try:
            image_id = self.docker_client.commit_container(container_id, repository, tag)
            snapshot = SnapshotInfo(
                container_id=container_id,
                image_id=image_id,
                repository=repository,
                tag=tag,
            )
            logger.info("Snapshot created", snapshot=snapshot.model_dump())
            return snapshot
        except Exception as e:
            logger.error("Failed to create snapshot", container_id=container_id[:12], error=str(e))
            return None

    def restore_snapshot(self, repository: str, tag: str, new_container_name: str, network: str, **kwargs) -> Optional[str]:
        try:
            container = self.docker_client.create_container(
                image=f"{repository}:{tag}",
                name=new_container_name,
                network=network,
                **kwargs
            )
            if self.docker_client.start_container(container.id):
                logger.info("Snapshot restored", container_id=container.id[:12], repository=repository, tag=tag)
                return container.id
            return None
        except Exception as e:
            logger.error("Failed to restore snapshot", repository=repository, tag=tag, error=str(e))
            return None

    def get_snapshot_info(self, repository: str, tag: str = "latest") -> Optional[Dict[str, Any]]:
        try:
            image = self.docker_client.client.images.get(f"{repository}:{tag}")
            return {
                "id": image.id,
                "tags": image.tags,
                "created": image.attrs["Created"],
                "size": image.attrs["Size"],
                "labels": image.attrs.get("Config", {}).get("Labels", {}),
            }
        except Exception as e:
            logger.error("Failed to get snapshot info", repository=repository, tag=tag, error=str(e))
            return None

    def list_snapshots(self, repository_prefix: str = "purple-") -> list[Dict[str, Any]]:
        try:
            images = self.docker_client.client.images.list()
            snapshots = []
            for image in images:
                for tag in image.tags:
                    if tag.startswith(repository_prefix):
                        snapshots.append({
                            "id": image.id,
                            "tag": tag,
                            "created": image.attrs["Created"],
                            "size": image.attrs["Size"],
                        })
            return snapshots
        except Exception as e:
            logger.error("Failed to list snapshots", error=str(e))
            return []

    def delete_snapshot(self, repository: str, tag: str = "latest") -> bool:
        try:
            self.docker_client.client.images.remove(f"{repository}:{tag}", force=True)
            logger.info("Snapshot deleted", repository=repository, tag=tag)
            return True
        except Exception as e:
            logger.error("Failed to delete snapshot", repository=repository, tag=tag, error=str(e))
            return False