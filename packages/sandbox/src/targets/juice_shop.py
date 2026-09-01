from sandbox.targets.base import BaseTargetApp, TargetConfig


class JuiceShopTarget(BaseTargetApp):
    @property
    def target_type(self) -> str:
        return "juice_shop"

    @property
    def display_name(self) -> str:
        return "OWASP Juice Shop"

    def get_default_config(self) -> TargetConfig:
        return TargetConfig(
            docker_image="bkimminich/juice-shop",
            docker_tag="latest",
            environment={
                "NODE_ENV": "unsafe",
            },
            health_check_path="/",
            health_check_interval=10,
            exposed_ports={"3000": 3000},
        )

    def get_reset_script(self) -> str:
        return """
            # Juice Shop uses SQLite database, reset by removing the database file
            rm -f /juice-shop/data/juiceshop.sqlite
            # Restart the application to reinitialize
            npm start &
        """

    def get_health_check_config(self) -> Dict[str, Any]:
        return {
            "path": "/",
            "interval": 10,
            "timeout": 5,
            "retries": 10,
        }

    def get_supported_scenarios(self) -> List[str]:
        return ["idor", "injection", "ssrf", "broken_auth", "business_logic"]

    def get_owasp_coverage(self) -> List[str]:
        return ["A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A10"]