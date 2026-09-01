from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
import re

from agents.schemas import EpisodeContext, DetectionResult, ResponseAction
from agents.rag.memory import RAGMemory

logger = structlog.get_logger(__name__)


BUSINESS_LOGIC_HARDENING_RESPONSES = {
    "race_condition_coupon": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "rate_limit_coupon", "limit": 1, "window": "1s"}},
            {"action_type": "revoke_session", "parameters": {"target": "coupon_sessions"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "idempotency_keys", "endpoint": "coupon"}},
            {"action_type": "add_auth_check", "parameters": {"check": "coupon_already_applied"}},
            {"action_type": "patch_vulnerability", "parameters": {"fix": "distributed_lock", "resource": "coupon"}},
        ],
    },
    "race_condition_giftcard": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "rate_limit_giftcard", "limit": 1, "window": "5s"}},
            {"action_type": "block_ip", "parameters": {"duration": "1h"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "atomic_giftcard_redeem"}},
            {"action_type": "add_auth_check", "parameters": {"check": "giftcard_already_used"}},
        ],
    },
    "price_manipulation_negative_qty": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "reject_negative_qty", "pattern": r"quantity.*-\d+"}},
            {"action_type": "block_ip", "parameters": {"duration": "24h"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "validate_quantity_positive"}},
            {"action_type": "add_auth_check", "parameters": {"check": "server_side_price_calculation"}},
        ],
    },
    "price_manipulation_hidden_field": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "detect_price_tampering", "pattern": r"price.*0\.0[01]|total.*0\.0[01]"}},
            {"action_type": "revoke_session", "parameters": {"all_user_sessions": True}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "server_side_price_validation"}},
            {"action_type": "add_auth_check", "parameters": {"check": "price_integrity_verification"}},
        ],
    },
    "bundle_bypass": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "validate_bundle_items"}},
            {"action_type": "revoke_session", "parameters": {"target": "bundle_sessions"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "bundle_server_validation"}},
            {"action_type": "add_auth_check", "parameters": {"check": "bundle_item_authorization"}},
        ],
    },
    "inventory_exhaustion": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "limit_cart_quantity", "max_per_item": 10}},
            {"action_type": "rate_limit", "parameters": {"endpoint": "cart/add", "limit": 5, "window": "1m"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "inventory_reservation_timeout"}},
            {"action_type": "add_auth_check", "parameters": {"check": "max_quantity_per_user"}},
        ],
    },
    "loyalty_points_abuse": {
        "immediate": [
            {"action_type": "revoke_session", "parameters": {"all_user_sessions": True}},
            {"action_type": "force_reauth", "parameters": {"reason": "points_manipulation"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "points_server_side_only"}},
            {"action_type": "add_auth_check", "parameters": {"check": "points_balance_verification"}},
        ],
    },
    "workflow_bypass": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "enforce_workflow_order"}},
            {"action_type": "revoke_session", "parameters": {"target": "checkout_sessions"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "state_machine_checkout"}},
            {"action_type": "add_auth_check", "parameters": {"check": "step_completion_verification"}},
        ],
    },
    "referral_abuse": {
        "immediate": [
            {"action_type": "update_waf_rule", "parameters": {"rule": "rate_limit_referral", "limit": 3, "window": "1h"}},
            {"action_type": "block_ip", "parameters": {"duration": "24h"}},
        ],
        "hardening": [
            {"action_type": "patch_vulnerability", "parameters": {"fix": "referral_email_verification"}},
            {"action_type": "add_auth_check", "parameters": {"check": "referral_uniqueness"}},
        ],
    },
}


BUSINESS_LOGIC_DETECTION_PATTERNS = {
    "race_condition_coupon": {
        "indicators": [
            r"(?i)coupon.*applied",
            r"(?i)discount.*applied",
            r"(?i)promo.*success",
        ],
        "concurrent_success_threshold": 2,
        "status_codes": [200],
    },
    "race_condition_giftcard": {
        "indicators": [
            r"(?i)redeemed|giftcard.*success",
            r"(?i)balance.*added",
        ],
        "concurrent_success_threshold": 2,
        "status_codes": [200],
    },
    "price_manipulation_negative_qty": {
        "indicators": [
            r"(?i)negative.*quantity",
            r"(?i)qty.*-\d+",
            r"(?i)quantity.*-\d+",
            r"(?i)credit|refund",
        ],
        "response_signals": [
            r"(?i)total.*-\$|total.*0\.0",
        ],
        "status_codes": [200],
    },
    "price_manipulation_hidden_field": {
        "indicators": [
            r"(?i)price.*0\.0[01]",
            r"(?i)total.*0\.0[01]",
            r"(?i)amount.*0\.0[01]",
        ],
        "response_signals": [
            r"(?i)order.*placed|checkout.*success",
        ],
        "status_codes": [200],
    },
    "bundle_bypass": {
        "indicators": [
            r"(?i)bundle.*added",
            r"(?i)premium.*free",
            r"(?i)skip.*validation",
        ],
        "response_signals": [
            r"(?i)bundle|package",
        ],
        "status_codes": [200],
    },
    "inventory_exhaustion": {
        "indicators": [
            r"(?i)added.*cart|cart.*updated",
            r"(?i)quantity.*999",
        ],
        "response_signals": [
            r"(?i)reserved|held",
        ],
        "status_codes": [200],
    },
    "loyalty_points_abuse": {
        "indicators": [
            r"(?i)points.*-\d+",
            r"(?i)negative.*points",
            r"(?i)redeemed.*premium",
        ],
        "response_signals": [
            r"(?i)points.*balance|success",
        ],
        "status_codes": [200],
    },
    "workflow_bypass": {
        "indicators": [
            r"(?i)skip.*step|bypass.*payment",
            r"(?i)force.*complete",
            r"(?i)step.*3.*complete",
        ],
        "response_signals": [
            r"(?i)order.*confirmed|checkout.*complete",
            r"(?i)payment.*skipped",
        ],
        "status_codes": [200],
    },
    "referral_abuse": {
        "indicators": [
            r"(?i)referral.*claimed",
            r"(?i)bonus.*awarded",
            r"(?i)referrer.*reward",
        ],
        "response_signals": [
            r"(?i)email.*sent|notification",
        ],
        "status_codes": [200],
    },
}


class BusinessLogicHardeningDetectionAgent:
    def __init__(
        self,
        rag_memory: Optional[RAGMemory] = None,
        scenario: str = "business_logic",
        target_type: str = "custom",
    ):
        self.rag = rag_memory
        self.scenario = scenario
        self.target_type = target_type
        self.patterns = BUSINESS_LOGIC_DETECTION_PATTERNS
        self.responses = BUSINESS_LOGIC_HARDENING_RESPONSES
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
        concurrent = result.get("concurrent_requests", 1)

        pattern_config = self.patterns.get(attack_type, {})
        indicators = pattern_config.get("indicators", [])
        response_signals = pattern_config.get("response_signals", [])
        expected_status = pattern_config.get("status_codes", [200])
        concurrent_threshold = pattern_config.get("concurrent_success_threshold", 1)

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

        if concurrent >= concurrent_threshold and "race_condition" in attack_type:
            detection_score += 0.4
            matched_patterns.append(f"race_condition:{concurrent}_successful")

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
                "concurrent_requests": concurrent,
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
            description=f"Business logic hardening: {chosen['action_type']} for {attack_type}",
        )

    async def apply_hardening(self, action: ResponseAction, target_url: str) -> Dict[str, Any]:
        logger.info("Applying business logic hardening", action=action.action_type, target=action.target)
        return {
            "success": True,
            "action": action.action_type,
            "parameters": action.parameters,
            "details": f"Hardening {action.action_type} applied to {action.target}",
            "timestamp": datetime.utcnow().isoformat(),
        }