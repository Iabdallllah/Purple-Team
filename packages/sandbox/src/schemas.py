from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class SandboxConfig(BaseModel):
    max_containers: int = 10
    default_cpu_limit: str = "2"
    default_memory_limit: str = "4g"
    network: str = "purple-network"
    docker_host: str = "unix:///var/run/docker.sock"

    def get_target_config(self, target_type: str) -> Optional[TargetConfig]:
        from sandbox.targets import create_target
        try:
            target = create_target(target_type)
            return target.config
        except ValueError:
            return None


class TargetConfig(BaseModel):
    docker_image: str
    docker_tag: str = "latest"
    environment: Dict[str, str] = Field(default_factory=dict)
    health_check_path: str = "/"
    health_check_interval: int = 30
    reset_script: Optional[str] = None
    exposed_ports: Dict[str, int] = Field(default_factory=dict)


class ContainerStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: str
    image: str
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    exit_code: Optional[int] = None
    ports: Dict[str, Any] = Field(default_factory=dict)


class EpisodeResult(BaseModel):
    episode_id: UUID
    container_id: str
    target_type: str
    success: bool
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    logs: str = ""
    attacks_executed: int = 0
    detections_triggered: int = 0
    responses_applied: int = 0


class SnapshotInfo(BaseModel):
    container_id: str
    image_id: str
    repository: str
    tag: str
    created_at: datetime = Field(default_factory=datetime.utcnow)