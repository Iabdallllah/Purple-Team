from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
import re

from agents.schemas import EpisodeContext, DetectionResult, ResponseAction, RedTeamAction
from agents.rag.memory import RAGMemory

logger = structlog.get_logger(__name__)


AUTH_HARDENING_RESPONSES = {
    "jwt_algo_confusion": {
        "immediate": [
            {"action_type": "force_reauth", "parameters": {"reason": "jwt_algorithm_confusion", "revoke_all": True}},
            {"action_type": "update_waf_rule", "parameters": {"rule": "block_jwt_none_algo", "pattern": "alg.*none"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "enforce_rs256_only", "endpoint": "all"}},
            {"action_type": "add_header", "parameters": {"header": "X-Content-Type-Options", "value": "nosniff"}},
        ],
    },
    "jwt_none_algo": {
        "immediate": [
            {"action_type": "force_reauth", "parameters": {"reason": "jwt_none_algorithm", "revoke_all": True}},
            {"action_type": "update_waf_rule", "parameters": {"rule": "reject_none_algorithm", "action": "block"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "require_signature_verification"}},
            {"action_type": "add_auth_check", "parameters": {"check": "jwt_signature_required"}},
        ],
    },
    "credential_stuffing": {
        "immediate": [
            {"action_type": "rate_limit", "parameters": {"endpoint": "/api/auth/login", "limit": 5, "window": "15m"}},
            {"action_type": "block_ip", "parameters": {"duration": "1h"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "add_captcha_after_failures", "threshold": 3}},
            {"action_type": "enable_hsts", "parameters": {}},
            {"action_type": "add_header", "parameters": {"header": "X-Frame-Options", "value": "DENY"}},
        ],
    },
    "password_spraying": {
        "immediate": [
            {"action_type": "rate_limit", "parameters": {"endpoint": "/api/auth/login", "limit": 3, "window": "1h", "by": "ip"}},
            {"action_type": "block_ip", "parameters": {"duration": "24h"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "account_lockout", "threshold": 5}},
            {"action_type": "add_auth_check", "parameters": {"check": "mfa_required"}},
        ],
    },
    "weak_reset_token": {
        "immediate": [
            {"action_type": "revoke_session", "parameters": {"target": "reset_tokens"}},
            {"action_type": "update_waf_rule", "parameters": {"rule": "monitor_reset_endpoint"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "crypto_random_tokens", "length": 32}},
            {"action_type": "add_auth_check", "parameters": {"check": "token_expiry_15min"}},
        ],
    },
    "session_fixation": {
        "immediate": [
            {"action_type": "revoke_session", "parameters": {"session_id": "fixed_session_id_12345"}},
            {"action_type": "force_reauth", "parameters": {"reason": "session_fixation_attempt"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "regenerate_session_on_login"}},
            {"action_type": "add_header", "parameters": {"header": "Set-Cookie", "value": "Secure; HttpOnly; SameSite=Strict"}},
        ],
    },
    "bf_la": {
        "immediate": [
            {"action_type": "block_ip", "parameters": {"duration": "24h"}},
            {"action_type": "revoke_session", "parameters": {"all_user_sessions": True}},
        ],
        "hardening": [
            {"action_type": "add_auth_check", "parameters": {"check": "rbac_enforcement", "roles": ["admin"]}},
            {"action_type": "patch_vulnerability", "parameters": {"fix": "function_level_authorization"}},
        ],
    },
    "token_replay": {
        "immediate": [
            {"action_type": "revoke_session", "parameters": {"token": "captured"}},
            {"action_type": "force_reauth", "parameters": {"reason": "token_replay_detected"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "token_binding", "method": "fingerprint"}},
            {"action_type": "add_auth_check", "parameters": {"check": "short_token_expiry", "minutes": 15}},
        ],
    },
}


AUTH_DETECTION_PATTERNS = {
    "jwt_algo_confusion": {
        "indicators": [r"alg.*HS256", r"algorithm.*confusion", r"signature.*valid"],
        "response_signals": [r"admin", r"role.*admin", r"access.*granted"],
        "headers": ["Authorization"],
    },
    "jwt_none_algo": {
        "indicators": [r"alg.*none", r"no.*signature", r"unsigned"],
        "response_signals": [r"admin", r"profile", r"email"],
        "headers": ["Authorization"],
    },
    "credential_stuffing": {
        "indicators": [r"invalid.*credential", r"failed.*login", r"too.*many.*attempt"],
        "response_signals": [r"account.*locked", r"captcha", r"rate.*limit"],
        "headers": [],
    },
    "password_spraying": {
        "indicators": [r"password.*incorrect", r"invalid.*password", r"login.*failed"],
        "response_signals": [r"locked", r"try.*again.*later"],
        "headers": [],
    },
    "weak_reset_token": {
        "indicators": [r"reset.*token", r"predictable", r"sequential"],
        "response_signals": [r"token.*sent", r"check.*email"],
        "headers": [],
    },
    "session_fixation": {
        "indicators": [r"session.*fixed", r"known.*session", r"pre.*set.*cookie"],
        "response_signals": [r"session.*created", r"logged.*in"],
        "headers": ["Cookie", "Set-Cookie"],
    },
    "bf_la": {
        "indicators": [r"admin.*function", r"unauthorized.*access", r"role.*check.*missing"],
        "response_signals": [r"deleted", r"role.*changed", r"success"],
        "headers": ["Authorization"],
    },
    "token_replay": {
        "indicators": [r"reused.*token", r"expired.*token", r"token.*replay"],
        "response_signals": [r"access.*granted", r"valid.*token"],
        "headers": ["Authorization"],
    },
}


class AuthHardeningDetectionAgent:
    def __init__(
        self,
        rag_memory: Optional[RAGMemory] = None,
        scenario: str = "idor",
        target_type: str = "juice_shop",
    ):
        self.rag = rag_memory
        self.scenario = scenario
        self.target_type = target_type
        self.patterns = AUTH_DETECTION_PATTERNS
        self.responses = AUTH_HARDENING_RESPONSES
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
        check_headers = pattern_config.get("headers", [])

        detection_score = 0.0
        matched_patterns = []

        for indicator in indicators:
            if re.search(indicator, response_body, re.IGNORECASE):
                detection_score += 0.3
                matched_patterns.append(f"body:{indicator}")

        for signal in response_signals:
            if re.search(signal, response_body, re.IGNORECASE):
                detection_score += 0.4
                matched_patterns.append(f"signal:{signal}")

        for header in check_headers:
            header_value = response_headers.get(header, "")
            if header_value and ("admin" in header_value.lower() or "bearer" in header_value.lower()):
                detection_score += 0.2
                matched_patterns.append(f"header:{header}")

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
            description=f"Auth hardening: {chosen['action_type']} for {attack_type}",
        )

    async def apply_hardening(self, action: ResponseAction, target_url: str) -> Dict[str, Any]:
        logger.info("Applying hardening", action=action.action_type, target=action.target)

        return {
            "success": True,
            "action": action.action_type,
            "parameters": action.parameters,
            "details": f"Hardening {action.action_type} applied to {action.target}",
            "timestamp": datetime.utcnow().isoformat(),
        }