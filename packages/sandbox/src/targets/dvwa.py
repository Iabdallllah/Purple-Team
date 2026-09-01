from sandbox.targets.base import BaseTargetApp, TargetConfig


class DVWATarget(BaseTargetApp):
    @property
    def target_type(self) -> str:
        return "dvwa"

    @property
    def display_name(self) -> str:
        return "DVWA (Damn Vulnerable Web App)"

    def get_default_config(self) -> TargetConfig:
        return TargetConfig(
            docker_image="vulnerables/web-dvwa",
            docker_tag="latest",
            environment={
                "MYSQL_ROOT_PASSWORD": "dvwa",
                "MYSQL_DATABASE": "dvwa",
                "MYSQL_USER": "dvwa",
                "MYSQL_PASSWORD": "dvwa",
            },
            health_check_path="/setup.php",
            health_check_interval=10,
            exposed_ports={"80": 80},
        )

    def get_reset_script(self) -> str:
        return """
            # DVWA reset - recreate the database
            mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "DROP DATABASE IF EXISTS dvwa; CREATE DATABASE dvwa;"
            mysql -u root -p${MYSQL_ROOT_PASSWORD} dvwa < /var/www/html/setup.php
            # Reset DVWA config
            php /var/www/html/setup.php --create
        """

    def get_health_check_config(self) -> Dict[str, Any]:
        return {
            "path": "/setup.php",
            "interval": 10,
            "timeout": 5,
            "retries": 10,
        }

    def get_supported_scenarios(self) -> List[str]:
        return ["idor", "injection", "broken_auth"]

    def get_owasp_coverage(self) -> List[str]:
        return ["A01", "A03", "A07"]