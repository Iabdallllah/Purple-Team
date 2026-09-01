from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from uuid import UUID


class EpisodeState(str):
    PENDING = "pending"
    INITIALIZING = "initializing"
    RECON = "recon"
    EXPLOIT = "exploit"
    DETECT = "detect"
    RESPOND = "respond"
    SCORE = "score"
    LEARN = "learn"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentType(str):
    RED_TEAM = "red_team"
    DETECTION = "detection"
    ORCHESTRATOR = "orchestrator"


class ToolCall(BaseModel):
    name: str
    args: Dict[str, Any]
    id: Optional[str] = None


class ToolResult(BaseModel):
    tool_call_id: str
    name: str
    result: Any
    error: Optional[str] = None


class EpisodeContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    episode_id: UUID
    project_id: UUID
    target_app_id: UUID
    scenario: str
    constraints: Dict[str, Any]
    target_url: str
    target_type: str
    current_state: str = EpisodeState.INITIALIZING
    iteration: int = 0
    max_iterations: int = 10
    attacks_executed: List[Dict[str, Any]] = Field(default_factory=list)
    detections_triggered: List[Dict[str, Any]] = Field(default_factory=list)
    responses_applied: List[Dict[str, Any]] = Field(default_factory=list)
    rag_context: List[Dict[str, Any]] = Field(default_factory=list)
    posture_score: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RedTeamAction(BaseModel):
    technique_id: str
    owasp_category: str
    attack_type: str
    target_endpoint: str
    http_method: str = "GET"
    payload: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, str] = Field(default_factory=dict)
    expected_behavior: str = ""


class DetectionResult(BaseModel):
    detected: bool
    detection_type: str
    confidence: float
    matched_patterns: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
    false_positive: bool = False


class ResponseAction(BaseModel):
    action_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    target: Optional[str] = None
    description: str = ""


class PostureMetrics(BaseModel):
    detection_rate: float = 0.0
    mttr_seconds: float = 0.0
    coverage: Dict[str, Any] = Field(default_factory=dict)  # per OWASP: {totalTechniques, coveredTechniques, coverage}
    overall_score: float = 0.0
    trend: Literal["improving", "stable", "declining"] = "stable"