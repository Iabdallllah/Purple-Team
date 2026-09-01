from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
import re

from agents.schemas import EpisodeContext, DetectionResult, ResponseAction
from agents.rag.memory import RAGMemory

logger = structlog.get_logger(__name__)


SSRF_DETECTION_PATTERNS = {
    "basic_ssrf": {
        "indicators": [
            r"(?i)169\.254\.169\.254",
            r"(?i)metadata\.google\.internal",
            r"(?i)metadata\.azure\.com",
            r"(?i)iam/security-credentials",
            r"(?i)instance-id",
            r"(?i)ami-id",
            r"(?i)instance-type",
            r"(?i)local-ipv4",
            r"(?i)user-data",
        ],
        "response_signals": [
            r"internal",
            r"private",
            r"metadata",
            r"credentials",
        ],
        "headers_to_check": ["X-Forwarded-For", "X-Real-IP", "X-Forwarded-Host"],
    },
    "blind_ssrf": {
        "indicators": [
            r"(?i)attacker\.com",
            r"(?i)callback",
            r"(?i)dnslog",
        ],
        "response_signals": [],
        "headers_to_check": ["User-Agent", "Referer", "X-Forwarded-For"],
    },
    "cloud_metadata": {
        "indicators": [
            r"(?i)computeMetadata",
            r"(?i)metadata\.google",
            r"(?i)metadata\.azure",
            r"(?i)169\.254\.169\.254",
            r"(?i)iam/security-credentials",
        ],
        "response_signals": [
            r"access_token",
            r"private_key",
            r"service_account",
        ],
        "headers_to_check": [],
    },
    "internal_port_scan": {
        "indicators": [
            r"(?i)localhost",
            r"(?i)127\.0\.0\.1",
            r":22|:3306|:5432|:6379|:8080|:9200",
        ],
        "response_signals": [
            r"ssh",
            r"mysql",
            r"postgresql",
            r"redis",
            r"elasticsearch",
            r"open",
            r"listening",
        ],
        "headers_to_check": [],
    },
    "file_scheme": {
        "indicators": [
            r"(?i)file://",
            r"(?i)phar://",
        ],
        "response_signals": [
            r"root:",
            r"daemon:",
            r"password",
            r"<?php",
            r"database",
            r"ssh",
        ],
        "headers_to_check": [],
    },
    "gopher_redis": {
        "indicators": [
            r"(?i)gopher://",
            r"(?i)dict://",
            r"redis",
        ],
        "response_signals": [
            r"flushall",
            r"redis",
            r"flush",
        ],
        "headers_to_check": [],
    },
}


SSRF_HARDENING_RESPONSES = {
    "basic_ssrf": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "block_private_ips", "pattern": r"(?i)(169\.254\.169\.254|127\.0\.0\.1|localhost|metadata\.google|metadata\.azure)"}},
            {"action_type": "block_ip", "parameters": {"duration": "24h"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "allowlist_urls", "endpoint": "fetch"}},
            {"action_type": "add_auth_check", "parameters": {"check": "validate_url_scheme"}},
            {"action_type": "disable_endpoint", "parameters": {"endpoint": "fetch", "temporary": True}},
        ],
    },
    "blind_ssrf": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "monitor_callback_urls", "pattern": r"(?i)(attacker|callback|dnslog)"}},
            {"action_type": "block_ip", "parameters": {"duration": "1h"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "validate_callback_urls"}},
            {"action_type": "add_auth_check", "parameters": {"check": "allowlist_domains"}},
        ],
    },
    "cloud_metadata": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "block_cloud_metadata", "pattern": r"(?i)(169\.254\.169\.254|metadata\.google|metadata\.azure|iam/security-credentials)"}},
            {"action_type": "block_ip", "parameters": {"duration": "48h"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "block_metadata_endpoints"}},
            {"action_type": "disable_endpoint", "parameters": {"endpoint": "fetch", "temporary": True}},
            {"action_type": "add_header", "parameters": {"header": "X-Content-Type-Options", "value": "nosniff"}},
        ],
    },
    "internal_port_scan": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "block_internal_ports", "pattern": r"(?i)(localhost|127\.0\.0\.1|:22|:3306|:5432|:6379|:8080|:9200)"}},
            {"action_type": "block_ip", "parameters": {"duration": "24h"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "block_private_ips"}},
            {"action_type": "add_auth_check", "parameters": {"check": "block_internal_networks"}},
        ],
    },
    "file_scheme": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "block_file_scheme", "pattern": r"(?i)file://"}},
            {"action_type": "block_ip", "parameters": {"duration": "24h"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "disable_file_scheme"}},
            {"action_type": "add_auth_check", "parameters": {"check": "validate_url_scheme"}},
        ],
    },
    "gopher_redis": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "block_gopher_dict", "pattern": r"(?i)(gopher://|dict://)"}},
            {"action_type": "block_ip", "parameters": {"duration": "48h"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "disable_gopher_dict_protocols"}},
            {"action_type": "add_header", "parameters": {"header": "X-Content-Type-Options", "value": "nosniff"}},
        ],
    },
}


class SSRFHardeningDetectionAgent:
    def __init__(
        self,
        rag_memory: Optional[RAGMemory] = None,
        scenario: str = "ssrf",
        target_type: str = "juice_shop",
    ):
        self.rag = rag_memory
        self.scenario = scenario
        self.target_type = target_type
        self.patterns = SSRF_DETECTION_PATTERNS
        self.responses = SSRF_HARDENING_RESPONSES
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
        response_headers = result.get("response_headers", {})
        status_code = result.get("status_code", 0)

        pattern_config = self.patterns.get(attack_type, {})
        indicators = pattern_config.get("indicators", [])
        response_signals = pattern_config.get("response_signals", [])
        check_headers = pattern_config.get("headers_to_check", [])

        detection_score = 0.0
        matched_patterns = []

        for indicator in indicators:
            if re.search(indicator, response_body, re.IGNORECASE):
                detection_score += 0.35
                matched_patterns.append(f"body:{indicator}")

        for signal in response_signals:
            if re.search(signal, response_body, re.IGNORECASE):
                detection_score += 0.4
                matched_patterns.append(f"signal:{signal}")

        for header in check_headers:
            header_value = response_headers.get(header, "")
            if header_value and re.search(r"(?i)(169\.254|127\.0\.0\.1|localhost|metadata)", header_value):
                detection_score += 0.2
                matched_patterns.append(f"header:{header}")

        if status_code == 200:
            detection_score += 0.15

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
            description=f"SSRF hardening: {chosen['action_type']} for {attack_type}",
        )

    async def apply_hardening(self, action: ResponseAction, target_url: str) -> Dict[str, Any]:
        logger.info("Applying SSRF hardening", action=action.action_type, target=action.target)
        return {
            "success": True,
            "action": action.action_type,
            "parameters": action.parameters,
            "details": f"Hardening {action.action_type} applied to {action.target}",
            "timestamp": datetime.utcnow().isoformat(),
        }