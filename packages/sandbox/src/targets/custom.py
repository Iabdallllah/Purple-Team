from sandbox.targets.base import BaseTargetApp, TargetConfig
from typing import List


class CustomTarget(BaseTargetApp):
    @property
    def target_type(self) -> str:
        return "custom"

    @property
    def display_name(self) -> str:
        return "Custom Target Application"

    def get_default_config(self) -> TargetConfig:
        return TargetConfig(
            docker_image="",
            docker_tag="latest",
            environment={},
            health_check_path="/",
            health_check_interval=30,
            exposed_ports={"80": 80, "443": 443},
        )

    def get_reset_script(self) -> Optional[str]:
        return self.config.reset_script

    def get_health_check_config(self) -> Dict[str, Any]:
        return {
            "path": self.config.health_check_path,
            "interval": self.config.health_check_interval,
            "timeout": 10,
            "retries": 5,
        }

    def get_supported_scenarios(self) -> List[str]:
        return ["idor", "injection", "business_logic", "ssrf", "broken_auth"]

    def get_owasp_coverage(self) -> List[str]:
        return ["A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A10"]

    def validate_config(self, config: TargetConfig) -> bool:
        return bool(config.docker_image)