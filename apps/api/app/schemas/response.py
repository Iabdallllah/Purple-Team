from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ResponseActionType(str):
    BLOCK_IP = "block_ip"
    RATE_LIMIT = "rate_limit"
    ADD_HEADER = "add_header"
    MODIFY_HEADER = "modify_header"
    UPDATE_WAF_RULE = "update_waf_rule"
    REVOKE_SESSION = "revoke_session"
    FORCE_REAUTH = "force_reauth"
    DISABLE_ENDPOINT = "disable_endpoint"
    PATCH_VULNERABILITY = "patch_vulnerability"
    ADD_AUTH_CHECK = "add_auth_check"
    ENABLE_CSP = "enable_csp"
    ENABLE_HSTS = "enable_hsts"
    CUSTOM = "custom"


class ResponseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    episode_id: UUID
    detection_id: Optional[UUID] = None
    action_type: str
    parameters: dict
    target: Optional[str] = None
    success: bool
    result: dict
    error: Optional[str] = None
    applied_at: Optional[datetime] = None
    reverted_at: Optional[datetime] = None
    timestamp: datetime
    created_at: datetime


class ResponseListParams(BaseModel):
    episode_id: UUID
    detection_id: Optional[UUID] = None
    action_type: Optional[str] = None
    success: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=100)


class ResponseStats(BaseModel):
    total_responses: int = 0
    successful_responses: int = 0
    failed_responses: int = 0
    by_action_type: dict = Field(default_factory=dict)
    average_response_time_seconds: float = 0.0