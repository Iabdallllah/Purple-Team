from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
import re

from agents.schemas import EpisodeContext, DetectionResult, ResponseAction
from agents.rag.memory import RAGMemory

logger = structlog.get_logger(__name__)


INJECTION_HARDENING_RESPONSES = {
    "sql_injection_union": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "block_union_select", "pattern": "(?i)union.*select"}},
            {"action_type": "block_ip", "parameters": {"duration": "24h"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "parameterized_queries", "endpoint": "all"}},
            {"action_type": "add_auth_check", "parameters": {"check": "input_validation_sql"}},
            {"action_type": "disable_endpoint", "parameters": {"endpoint": "vulnerable", "temporary": True}},
        ],
    },
    "sql_injection_blind": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "block_time_based", "pattern": "(?i)(sleep|pg_sleep|waitfor.*delay)"}},
            {"action_type": "rate_limit", "parameters": {"endpoint": "vulnerable", "limit": 10, "window": "1m"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "prepared_statements"}},
            {"action_type": "add_header", "parameters": {"header": "X-Content-Type-Options", "value": "nosniff"}},
        ],
    },
    "sql_injection_error": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "block_error_based", "pattern": "(?i)(extractvalue|floor.*rand|updatexml)"}},
            {"action_type": "block_ip", "parameters": {"duration": "24h"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "error_handling_no_leak"}},
            {"action_type": "add_auth_check", "parameters": {"check": "sanitize_error_messages"}},
        ],
    },
    "nosql_injection": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "block_nosql_operators", "pattern": r"\$ne|\$gt|\$where|\$regex"}},
            {"action_type": "revoke_session", "parameters": {"all_user_sessions": True}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "schema_validation", "strict": True}},
            {"action_type": "add_auth_check", "parameters": {"check": "nosql_type_checking"}},
        ],
    },
    "command_injection": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "block_shell_metacharacters", "pattern": r"[;&|`$()]+"}},
            {"action_type": "block_ip", "parameters": {"duration": "48h"}},
            {"action_type": "revoke_session", "parameters": {"all_user_sessions": True}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "command_allowlist", "endpoint": "vulnerable"}},
            {"action_type": "disable_endpoint", "parameters": {"endpoint": "vulnerable", "temporary": True}},
            {"action_type": "add_header", "parameters": {"header": "X-Content-Type-Options", "value": "nosniff"}},
        ],
    },
    "template_injection": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "block_ssti", "pattern": r"\{\{.*\}\}|#\{.*\}|\$\{.*\}"}},
            {"action_type": "block_ip", "parameters": {"duration": "48h"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "sandbox_template_engine"}},
            {"action_type": "add_auth_check", "parameters": {"check": "template_input_validation"}},
        ],
    },
    "ldap_injection": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "block_ldap_metacharacters", "pattern": r"[\(\)\*\&\|]"}},
            {"action_type": "block_ip", "parameters": {"duration": "24h"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "ldap_escape_input"}},
            {"action_type": "add_auth_check", "parameters": {"check": "ldap_filter_validation"}},
        ],
    },
    "xpath_injection": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "block_xpath_injection", "pattern": r"['\"|\[\]"} },
            {"action_type": "block_ip", "parameters": {"duration": "24h"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "xpath_parameterized"}},
            {"action_type": "add_auth_check", "parameters": {"check": "xpath_input_validation"}},
        ],
    },
}


INJECTION_DETECTION_PATTERNS = {
    "sql_injection_union": {
        "indicators": [
            r"(?i)union.*select",
            r"(?i)information_schema",
            r"(?i)sqlite_version",
            r"(?i)@@version",
            r"(?i)table_name",
            r"(?i)column_name",
        ],
        "response_signals": [
            r"username|password|email|user",
            r"admin|root|superuser",
            r"credit|card|ssn",
        ],
        "status_codes": [200],
    },
    "sql_injection_blind": {
        "indicators": [
            r"(?i)sleep\s*\(",
            r"(?i)pg_sleep",
            r"(?i)waitfor.*delay",
            r"(?i)benchmark\s*\(",
        ],
        "response_signals": [],
        "time_based": True,
        "threshold_seconds": 4.0,
        "status_codes": [200, 500],
    },
    "sql_injection_error": {
        "indicators": [
            r"(?i)extractvalue",
            r"(?i)updatexml",
            r"(?i)floor.*rand",
            r"(?i)sql syntax",
            r"(?i)mysql.*error",
            r"(?i)postgresql.*error",
            r"(?i)sqlite.*error",
        ],
        "response_signals": [
            r"version\(\)",
            r"database.*name",
            r"table.*column",
        ],
        "status_codes": [500, 200],
    },
    "nosql_injection": {
        "indicators": [
            r"(?i)\$ne|\$gt|\$lt|\$regex|\$where|\$exists",
            r"(?i)injection",
        ],
        "response_signals": [
            r"token|authenticated|welcome|dashboard",
            r"login.*success",
        ],
        "status_codes": [200],
    },
    "command_injection": {
        "indicators": [
            r"(?i)(;|&&|\|\||`|\$\(|\<\()",
            r"(?i)cat\s+/etc/passwd",
            r"(?i)whoami|id\s*$",
            r"(?i)ls\s+-la",
            r"(?i)uname\s+-a",
        ],
        "response_signals": [
            r"root:|uid=|gid=",
            r"bin/bash|bin/sh",
            r"total\s+\d+",
            r"drwx",
        ],
        "status_codes": [200, 500],
    },
    "template_injection": {
        "indicators": [
            r"\{\{.*\}\}",
            r"#\{.*\}",
            r"\$\{.*\}",
            r"<%.*%>",
        ],
        "response_signals": [
            r"49",
            r"__class__|__mro__|__subclasses__",
            r"config|globals|builtins",
        ],
        "status_codes": [200],
    },
    "ldap_injection": {
        "indicators": [
            r"\(\*\$uid|\(\|\(password",
            r"(?i)ldap",
        ],
        "response_signals": [
            r"cn=|ou=|dc=",
            r"objectclass",
        ],
        "status_codes": [200],
    },
    "xpath_injection": {
        "indicators": [
            r"' or '1'='1",
            r"\]\s*\|\s*//",
        ],
        "response_signals": [
            r"user|password",
            r"login|auth",
        ],
        "status_codes": [200],
    },
}


class InjectionHardeningDetectionAgent:
    def __init__(
        self,
        rag_memory: Optional[RAGMemory] = None,
        scenario: str = "injection",
        target_type: str = "juice_shop",
    ):
        self.rag = rag_memory
        self.scenario = scenario
        self.target_type = target_type
        self.patterns = INJECTION_DETECTION_PATTERNS
        self.responses = INJECTION_HARDENING_RESPONSES
        self.applied_hardenings: List[str] = []

    async def analyze(self, attack: Dict[str, Any], state: EpisodeContext) -> DetectionResult:
        attack_type = attack.get("attack_type", "")
        technique_id = attack.get("technique_id", "")
        result = attack.get("result", {})

        if not result.get("success"):
            return DetectionResult(
                detected=False,
                detection_type="none",
                confidence=0.0,
                details={"reason": "Attack failed"},
            )

        response_body = result.get("response_body", "")
        status_code = result.get("status_code", 0)
        response_time = result.get("response_time_ms", 0)

        pattern_config = self.patterns.get(attack_type, {})
        indicators = pattern_config.get("indicators", [])
        response_signals = pattern_config.get("response_signals", [])
        expected_status = pattern_config.get("status_codes", [200])
        time_based = pattern_config.get("time_based", False)
        threshold = pattern_config.get("threshold_seconds", 4.0)

        detection_score = 0.0
        matched_patterns = []

        for indicator in indicators:
            if re.search(indicator, response_body, re.IGNORECASE):
                detection_score += 0.35
                matched_patterns.append(f"indicator:{indicator}")

        for signal in response_signals:
            if re.search(signal, response_body, re.IGNORECASE):
                detection_score += 0.4
                matched_patterns.append(f"signal:{signal}")

        if status_code in expected_status:
            detection_score += 0.15

        if time_based and response_time > threshold * 1000:
            detection_score += 0.5
            matched_patterns.append(f"time_based:{response_time}ms")

        detection_score = min(detection_score, 1.0)

        rag_boost = self._check_rag_history(technique_id, response_body)
        detection_score = min(detection_score + rag_boost, 1.0)

        detected = detection_score >= 0.5

        return DetectionResult(
            detected=detected,
            detection_type=attack_type if detected else "none",
            confidence=detection_score,
            matched_patterns=matched_patterns,
            details={
                "technique_id": technique_id,
                "attack_type": attack_type,
                "status_code": status_code,
                "response_time_ms": response_time,
                "response_preview": response_body[:500],
                "rag_boost": rag_boost,
            },
        )

    def _check_rag_history(self, technique_id: str, response_body: str) -> float:
        if not self.rag:
            return 0.0

        similar = self.rag.retrieve_by_technique(technique_id, n_results=3)
        if not similar:
            return 0.0

        boost = 0.0
        for episode in similar:
            metadata = episode.get("metadata", {})
            if metadata.get("success") and metadata.get("detection_rate", 0) > 0.7:
                boost += 0.1

        return min(boost, 0.3)

    async def generate_response(
        self,
        detection: DetectionResult,
        attack: Dict[str, Any],
        state: EpisodeContext,
    ) -> ResponseAction:
        attack_type = attack.get("attack_type", "")

        if attack_type not in self.responses:
            return ResponseAction(
                action_type="add_header",
                parameters={"header": "X-Content-Type-Options", "value": "nosniff"},
                target=attack.get("target_endpoint"),
                description="Generic security header",
            )

        response_config = self.responses[attack_type]
        immediate = response_config.get("immediate", [])
        hardening = response_config.get("hardening", [])

        all_actions = immediate + [h for h in hardening if h["action_type"] not in self.applied_hardenings]

        if not all_actions:
            all_actions = immediate

        chosen = all_actions[0]
        self.applied_hardenings.append(chosen["action_type"])

        return ResponseAction(
            action_type=chosen["action_type"],
            parameters=chosen["parameters"],
            target=attack.get("target_endpoint"),
            description=f"Injection hardening: {chosen['action_type']} for {attack_type}",
        )

    async def apply_hardening(self, action: ResponseAction, target_url: str) -> Dict[str, Any]:
        logger.info("Applying injection hardening", action=action.action_type, target=action.target)
        return {
            "success": True,
            "action": action.action_type,
            "parameters": action.parameters,
            "details": f"Hardening {action.action_type} applied to {action.target}",
            "timestamp": datetime.utcnow().isoformat(),
        }