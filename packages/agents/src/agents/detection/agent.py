from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
import structlog
import re
import json

from agents.schemas import EpisodeContext, DetectionResult, ResponseAction, RedTeamAction
from agents.rag.memory import RAGMemory

logger = structlog.get_logger(__name__)


IDOR_DETECTION_PATTERNS = {
    "horizontal_idor": {
        "indicators": [
            r"user.*id.*\d+",
            r"profile.*\d+",
            r"account.*\d+",
            r"order.*\d+",
        ],
        "response_signals": [
            r"email.*@",
            r"phone.*\d{10,}",
            r"address.*",
            r"credit.card",
            r"ssn",
        ],
        "status_codes": [200],
    },
    "vertical_idor": {
        "indicators": [
            r"admin",
            r"dashboard",
            r"management",
            r"reports",
            r"all.users",
        ],
        "response_signals": [
            r"user.*list",
            r"total.*users",
            r"admin.*panel",
        ],
        "status_codes": [200],
    },
    "jwt_manipulation": {
        "indicators": [
            r"role.*admin",
            r"privilege.*escalat",
            r"token.*valid",
        ],
        "response_signals": [
            r"admin",
            r"elevated",
            r"super.user",
        ],
        "status_codes": [200],
    },
    "parameter_tampering": {
        "indicators": [
            r"\.\./",
            r"etc/passwd",
            r"windows/system32",
            r"file.*read",
        ],
        "response_signals": [
            r"root:",
            r"\[boot loader\]",
            r"password",
        ],
        "status_codes": [200],
    },
    "bola": {
        "indicators": [
            r"resource.*access",
            r"object.*authorization",
        ],
        "response_signals": [
            r"data",
            r"resource.*id",
        ],
        "status_codes": [200],
    },
}


class DetectionAgent:
    def __init__(
        self,
        rag_memory: Optional[RAGMemory] = None,
        scenario: str = "idor",
        target_type: str = "juice_shop",
    ):
        self.rag = rag_memory
        self.scenario = scenario
        self.target_type = target_type
        self.patterns = IDOR_DETECTION_PATTERNS

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

        pattern_config = self.patterns.get(attack_type, {})
        indicators = pattern_config.get("indicators", [])
        response_signals = pattern_config.get("response_signals", [])
        expected_status_codes = pattern_config.get("status_codes", [200])

        detection_score = 0.0
        matched_patterns = []

        for indicator in indicators:
            if re.search(indicator, response_body, re.IGNORECASE):
                detection_score += 0.3
                matched_patterns.append(f"indicator:{indicator}")

        for signal in response_signals:
            if re.search(signal, response_body, re.IGNORECASE):
                detection_score += 0.4
                matched_patterns.append(f"signal:{signal}")

        if status_code in expected_status_codes:
            detection_score += 0.2

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
        technique_id = attack.get("technique_id", "")

        response_map = {
            "horizontal_idor": {
                "action_type": "add_auth_check",
                "parameters": {"endpoint": attack.get("target_endpoint"), "check": "object_ownership"},
                "description": "Add object-level authorization check to verify resource ownership",
            },
            "vertical_idor": {
                "action_type": "add_auth_check",
                "parameters": {"endpoint": attack.get("target_endpoint"), "check": "role_based_access"},
                "description": "Enforce role-based access control for admin endpoints",
            },
            "jwt_manipulation": {
                "action_type": "force_reauth",
                "parameters": {"reason": "jwt_tampering_detected"},
                "description": "Invalidate tampered tokens and force re-authentication",
            },
            "parameter_tampering": {
                "action_type": "patch_vulnerability",
                "parameters": {"endpoint": attack.get("target_endpoint"), "fix": "input_validation"},
                "description": "Add input validation and path sanitization",
            },
            "bola": {
                "action_type": "add_auth_check",
                "parameters": {"endpoint": attack.get("target_endpoint"), "check": "resource_authorization"},
                "description": "Implement resource-level authorization validation",
            },
        }

        config = response_map.get(attack_type, {
            "action_type": "add_header",
            "parameters": {"header": "X-Content-Type-Options", "value": "nosniff"},
            "description": "Add security header as generic response",
        })

        return ResponseAction(
            action_type=config["action_type"],
            parameters=config["parameters"],
            target=attack.get("target_endpoint"),
            description=config["description"],
        )