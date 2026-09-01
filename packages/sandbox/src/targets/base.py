from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class TargetConfig:
    docker_image: str
    docker_tag: str = "latest"
    environment: Dict[str, str] = field(default_factory=dict)
    health_check_path: str = "/"
    health_check_interval: int = 30
    reset_script: Optional[str] = None
    exposed_ports: Dict[str, int] = field(default_factory=dict)


class BaseTargetApp(ABC):
    def __init__(self, config: TargetConfig):
        self.config = config

    @property
    @abstractmethod
    def target_type(self) -> str:
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        pass

    @abstractmethod
    def get_default_config(self) -> TargetConfig:
        pass

    @abstractmethod
    def get_reset_script(self) -> Optional[str]:
        pass

    @abstractmethod
    def get_health_check_config(self) -> Dict[str, Any]:
        pass

    def validate_config(self, config: TargetConfig) -> bool:
        return bool(config.docker_image)

    def get_docker_image_full(self) -> str:
        return f"{self.config.docker_image}:{self.config.docker_tag}"

    def get_environment(self) -> Dict[str, str]:
        return self.config.environment

    def get_exposed_ports(self) -> Dict[str, int]:
        return self.config.exposed_ports

    def get_health_check_command(self) -> List[str]:
        return ["curl", "-f", f"http://localhost{self.config.health_check_path}"]

    def get_reset_command(self) -> Optional[List[str]]:
        if self.config.reset_script:
            return ["sh", "-c", self.config.reset_script]
        return None