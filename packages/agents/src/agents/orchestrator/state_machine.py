import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Dict, Any, Literal, Callable, Awaitable, Optional
from datetime import datetime
from uuid import UUID
import structlog

from agents.schemas import EpisodeContext, EpisodeState, RedTeamAction, DetectionResult, ResponseAction, PostureMetrics
from agents.red_team.agent import RedTeamAgent
from agents.detection.agent import DetectionAgent
from agents.rag.memory import RAGMemory

logger = structlog.get_logger(__name__)

# Type for event callback
EventCallback = Optional[Callable[[str, str, dict], Awaitable[None]]]


class Orchestrator:
    def __init__(
        self,
        red_team_agent: RedTeamAgent,
        detection_agent: DetectionAgent,
        rag_memory: RAGMemory,
        max_iterations: int = 10,
        event_callback: EventCallback = None,
    ):
        self.red_team = red_team_agent
        self.detection = detection_agent
        self.rag = rag_memory
        self.max_iterations = max_iterations
        self.event_callback = event_callback
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(EpisodeContext)

        workflow.add_node("initialize", self._initialize)
        workflow.add_node("recon", self._recon)
        workflow.add_node("exploit", self._exploit)
        workflow.add_node("detect", self._detect)
        workflow.add_node("respond", self._respond)
        workflow.add_node("score", self._score)
        workflow.add_node("learn", self._learn)

        workflow.set_entry_point("initialize")

        workflow.add_conditional_edges(
            "initialize",
            self._route_after_init,
            {
                "recon": "recon",
                "failed": END,
            },
        )

        workflow.add_conditional_edges(
            "recon",
            self._route_after_recon,
            {
                "exploit": "exploit",
                "completed": "score",
            },
        )

        workflow.add_conditional_edges(
            "exploit",
            self._route_after_exploit,
            {
                "detect": "detect",
                "recon": "recon",
                "completed": "score",
            },
        )

        workflow.add_conditional_edges(
            "detect",
            self._route_after_detect,
            {
                "respond": "respond",
                "exploit": "exploit",
            },
        )

        workflow.add_conditional_edges(
            "respond",
            self._route_after_respond,
            {
                "exploit": "exploit",
                "score": "score",
            },
        )

        workflow.add_edge("score", "learn")
        workflow.add_edge("learn", END)

        return workflow.compile(checkpointer=MemorySaver())

    async def _initialize(self, state: EpisodeContext) -> EpisodeContext:
        logger.info("Initializing episode", episode_id=str(state.episode_id))
        state.current_state = EpisodeState.INITIALIZING
        state.iteration = 0
        state.updated_at = datetime.utcnow()
        return state

    def _route_after_init(self, state: EpisodeContext) -> Literal["recon", "failed"]:
        if state.error:
            return "failed"
        state.current_state = EpisodeState.RECON
        return "recon"

    async def _recon(self, state: EpisodeContext) -> EpisodeContext:
        logger.info("Running reconnaissance", episode_id=str(state.episode_id))
        state.current_state = EpisodeState.RECON

        rag_context = self.rag.retrieve_similar(
            scenario=state.scenario,
            target_type=state.target_type,
            attack_description="initial reconnaissance",
            n_results=3,
        )
        state.rag_context = rag_context

        state.updated_at = datetime.utcnow()
        return state

    def _route_after_recon(self, state: EpisodeContext) -> Literal["exploit", "completed"]:
        if state.iteration >= self.max_iterations:
            return "completed"
        state.current_state = EpisodeState.EXPLOIT
        return "exploit"

    async def _exploit(self, state: EpisodeContext) -> EpisodeContext:
        logger.info("Running exploit phase", episode_id=str(state.episode_id), iteration=state.iteration)
        state.current_state = EpisodeState.EXPLOIT

        action = await self.red_team.select_action(state)

        if action:
            result = await self.red_team.execute_action(action, state.target_url)
            action.result = result
            state.attacks_executed.append(action.model_dump())
            logger.info("Attack executed", technique=action.technique_id, success=result.get("success", False))
            
            if self.event_callback:
                await self.event_callback(str(state.episode_id), 'attack', {
                    'technique_id': action.technique_id,
                    'attack_type': action.attack_type,
                    'target_endpoint': action.target_endpoint,
                    'success': result.get('success', False),
                    'confidence': result.get('confidence', 0.0),
                })

        state.iteration += 1
        state.updated_at = datetime.utcnow()
        return state

    def _route_after_exploit(self, state: EpisodeContext) -> Literal["detect", "recon", "completed"]:
        if state.iteration >= self.max_iterations:
            return "completed"

        last_attack = state.attacks_executed[-1] if state.attacks_executed else None
        if last_attack and last_attack.get("result", {}).get("success"):
            return "detect"

        if state.iteration % 3 == 0:
            return "recon"

        return "exploit"

    async def _detect(self, state: EpisodeContext) -> EpisodeContext:
        logger.info("Running detection", episode_id=str(state.episode_id))
        state.current_state = EpisodeState.DETECT

        last_attack = state.attacks_executed[-1] if state.attacks_executed else None
        if last_attack:
            detection = await self.detection.analyze(last_attack, state)
            state.detections_triggered.append(detection.model_dump())

            if detection.detected:
                logger.info("Attack detected", technique=last_attack.get("technique_id"), confidence=detection.confidence)
                if self.event_callback:
                    await self.event_callback(str(state.episode_id), 'detection', {
                        'technique_id': last_attack.get('technique_id'),
                        'detected': detection.detected,
                        'detection_type': detection.detection_type,
                        'confidence': detection.confidence,
                        'matched_patterns': detection.matched_patterns,
                    })

        state.updated_at = datetime.utcnow()
        return state

    def _route_after_detect(self, state: EpisodeContext) -> Literal["respond", "exploit"]:
        last_detection = state.detections_triggered[-1] if state.detections_triggered else None
        if last_detection and last_detection.get("detected"):
            return "respond"
        return "exploit"

    async def _respond(self, state: EpisodeContext) -> EpisodeContext:
        logger.info("Running response", episode_id=str(state.episode_id))
        state.current_state = EpisodeState.RESPOND

        last_detection = state.detections_triggered[-1] if state.detections_triggered else None
        last_attack = state.attacks_executed[-1] if state.attacks_executed else None

        if last_detection and last_attack:
            response = await self.detection.generate_response(last_detection, last_attack, state)
            result = await self._apply_response(response, state.target_url)
            response.result = result
            state.responses_applied.append(response.model_dump())
            logger.info("Response applied", action=response.action_type, success=result.get("success", False))
            
            if self.event_callback:
                await self.event_callback(str(state.episode_id), 'response', {
                    'action_type': response.action_type,
                    'target': response.target,
                    'success': result.get('success', False),
                    'description': response.description,
                })

        state.updated_at = datetime.utcnow()
        return state

    def _route_after_respond(self, state: EpisodeContext) -> Literal["exploit", "score"]:
        if state.iteration >= self.max_iterations:
            return "score"
        return "exploit"

    async def _score(self, state: EpisodeContext) -> EpisodeContext:
        logger.info("Calculating posture score", episode_id=str(state.episode_id))
        state.current_state = EpisodeState.SCORE

        metrics = self._calculate_metrics(state)
        state.posture_score = metrics.model_dump()

        if self.event_callback:
            await self.event_callback(str(state.episode_id), 'score', {
                'detection_rate': metrics.detection_rate,
                'mttr_seconds': metrics.mttr_seconds,
                'coverage': metrics.coverage,
                'overall_score': metrics.overall_score,
            })

        state.updated_at = datetime.utcnow()
        return state

    async def _learn(self, state: EpisodeContext) -> EpisodeContext:
        logger.info("Learning from episode", episode_id=str(state.episode_id))
        state.current_state = EpisodeState.LEARN

        success = len([a for a in state.attacks_executed if a.get("result", {}).get("success")]) > 0
        self.rag.store_episode(
            episode_id=state.episode_id,
            scenario=state.scenario,
            target_type=state.target_type,
            attacks=[RedTeamAction(**a) for a in state.attacks_executed],
            detections=[DetectionResult(**d) for d in state.detections_triggered],
            responses=[ResponseAction(**r) for r in state.responses_applied],
            posture_score=state.posture_score or {},
            success=success,
        )

        state.current_state = EpisodeState.COMPLETED
        state.updated_at = datetime.utcnow()
        return state

    def _calculate_metrics(self, state: EpisodeContext) -> PostureMetrics:
        total_attacks = len(state.attacks_executed)
        true_positives = len([d for d in state.detections_triggered if d.get("detected")])
        detection_rate = true_positives / total_attacks if total_attacks > 0 else 0.0

        # MTTR: avg time between detection and response (use stored timestamps or fallback)
        mttr_vals = []
        for det, resp in zip(state.detections_triggered, state.responses_applied):
            try:
                det_t = det.get("details", {}).get("timestamp") or det.get("timestamp")
                resp_t = resp.get("result", {}).get("timestamp") or resp.get("timestamp")
                if det_t and resp_t:
                    dt = (datetime.fromisoformat(str(resp_t).replace("Z","+00:00")) - datetime.fromisoformat(str(det_t).replace("Z","+00:00"))).total_seconds()
                    if 0 <= dt < 3600:
                        mttr_vals.append(dt)
            except Exception:
                pass
        mttr = sum(mttr_vals)/len(mttr_vals) if mttr_vals else (15.0 if state.responses_applied else 0.0)

        # Coverage per OWASP category (A01-A10) based on distinct MITRE techniques exercised vs full OWASP/MITRE matrix
        # Totals derived from packages/shared/src/constants/owasp.ts (OWASP_TOP_10_2021.mitreTechniques length) and mitre.ts
        # This replaces previous heuristic (1/1) with real matrix per proposal KPIs.
        OWASP_TOTAL_TECHNIQUES = {
            "A01": 3,  # T1548, T1083, T1005 (OWASP) / 4 with mitre.ts inclusive
            "A02": 3,  # T1557, T1040, T1552
            "A03": 3,  # T1190, T1059, T1059.007 (core) / 8 with full mitre
            "A04": 2,  # T1599, T1585
            "A05": 3,  # T1599, T1585, T1592
            "A06": 2,  # T1190, T1585
            "A07": 3,  # T1110, T1556, T1539
            "A08": 3,  # T1195, T1553, T1584
            "A09": 3,  # T1562, T1070, T1556
            "A10": 3,  # T1590, T1592, T1580
        }
        # More accurate full matrix from mitre.ts (technique -> owaspCategories):
        # Used for distinct counting when technique appears in multiple categories via its declared owaspCategories
        # Fallback to attack's owasp_category if technique not in map
        MITRE_TO_OWASP = {
            "T1190": ["A03","A06"], "T1199": ["A01","A04"], "T1059": ["A03"], "T1059.007": ["A03"],
            "T1505": ["A03","A08"], "T1548": ["A01","A07"], "T1070": ["A09"], "T1562": ["A05","A09"],
            "T1552": ["A02","A07"], "T1556": ["A07"], "T1083": ["A01","A05"], "T1590": ["A05","A10"],
            "T1592": ["A05","A10"], "T1570": ["A03","A08"], "T1005": ["A01","A02"], "T1071": ["A03","A10"],
            "T1485": ["A03","A04"], "T1491": ["A03","A04"], "T1548.003": ["A01"], "T1548.002": ["A01"],
            "T1556.002": ["A07"], "T1556.001": ["A07"], "T1599": ["A04","A05"], "T1585": ["A04","A05","A06"],
            "T1110": ["A07"], "T1539": ["A07"], "T1195": ["A08"], "T1553": ["A08"], "T1584": ["A08"],
            "T1557": ["A02"], "T1040": ["A02"], "T1580": ["A10"],
        }
        from collections import defaultdict
        covered_by_cat: dict[str, set] = defaultdict(set)
        for a in state.attacks_executed:
            tid = a.get("technique_id")
            owasp_cat = a.get("owasp_category")
            if tid and tid in MITRE_TO_OWASP:
                for cat in MITRE_TO_OWASP[tid]:
                    covered_by_cat[cat].add(tid)
            elif owasp_cat:
                # fallback: count distinct technique per declared owasp
                covered_by_cat[owasp_cat].add(tid or owasp_cat)
        coverage = {}
        for cat in ["A01","A02","A03","A04","A05","A06","A07","A08","A09","A10"]:
            total = OWASP_TOTAL_TECHNIQUES.get(cat, 3)
            covered = len(covered_by_cat.get(cat, set()))
            # cap at total (distinct techniques shouldn't exceed total; if exceeds, count as 100%)
            covered_capped = min(covered, total)
            coverage[cat] = {
                "totalTechniques": total,
                "coveredTechniques": covered_capped,
                "coverage": round(covered_capped/total, 3) if total else 0.0,
                "uniqueTechniques": sorted(list(covered_by_cat.get(cat, set()))) if covered else []
            }

        # Overall score weighted: 60% detection, 20% MTTR (inverse), 20% coverage
        avg_coverage = sum(v["coverage"] for v in coverage.values())/len(coverage) if coverage else 0.0
        mttr_score = max(0, 1 - (mttr/300.0)) if mttr else 0  # 5min max
        overall = round((detection_rate*0.6 + avg_coverage*0.2 + mttr_score*0.2)*100, 1)

        return PostureMetrics(
            detection_rate=round(detection_rate,3),
            mttr_seconds=round(mttr,1),
            coverage=coverage,
            overall_score=overall,
        )

    async def _apply_response(self, response: ResponseAction, target_url: str) -> Dict[str, Any]:
        return {"success": True, "details": f"Applied {response.action_type}"}

    async def _invoke_with_circuit(self, episode_context: EpisodeContext, config: dict) -> Dict[str, Any]:
        # Circuit breaker + exponential backoff for transient LLM/network failures
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), retry=retry_if_exception_type((asyncio.TimeoutError, ConnectionError)), reraise=True)
        async def _run():
            return await self.graph.ainvoke(episode_context, config)
        return await _run()

    async def run_episode(self, episode_context: EpisodeContext) -> EpisodeContext:
        config = {"configurable": {"thread_id": str(episode_context.episode_id)}}
        # Timeout enforced from constraints (PDF: Episode Duration ≤30min)
        max_minutes = int(episode_context.constraints.get("max_duration_minutes", 30)) if isinstance(episode_context.constraints, dict) else 30
        timeout_s = max(60, max_minutes * 60)
        try:
            result = await asyncio.wait_for(self._invoke_with_circuit(episode_context, config), timeout=timeout_s)
        except asyncio.TimeoutError:
            logger.warning("Episode timed out", episode_id=str(episode_context.episode_id), timeout=timeout_s)
            episode_context.error = f"Episode timed out after {timeout_s}s"
            episode_context.current_state = EpisodeState.FAILED
            return episode_context
        return EpisodeContext(**result)