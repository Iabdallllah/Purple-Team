import asyncio
import json
import structlog
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, UTC

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import async_session_maker
from app.core.config import get_settings
from app.models.episode import Episode, EpisodeStatus
from app.models.target_app import TargetApp
from app.models.project import Project
from app.models.attack import Attack
from app.models.detection import Detection, DetectionType
from app.models.response import Response
from app.models.posture_score import PostureScore
from app.workers.socket_server import broadcast_episode_event, broadcast_episode_status, broadcast_attack, broadcast_detection, broadcast_response, broadcast_score

from agents.orchestrator.state_machine import Orchestrator
from agents.red_team.agent import RedTeamAgent
from agents.red_team.auth_abuse_agent import AuthAbuseRedTeamAgent
from agents.red_team.injection_agent import InjectionRedTeamAgent
from agents.red_team.business_logic_agent import BusinessLogicRedTeamAgent
from agents.red_team.ssrf_agent import SSRFRedTeamAgent
from agents.detection.agent import DetectionAgent
from agents.detection.auth_hardening_agent import AuthHardeningDetectionAgent
from agents.detection.injection_hardening_agent import InjectionHardeningDetectionAgent
from agents.detection.business_logic_hardening_agent import BusinessLogicHardeningDetectionAgent
from agents.detection.ssrf_hardening_agent import SSRFHardeningDetectionAgent
from agents.rag.memory import RAGMemory
from agents.schemas import EpisodeContext

settings = get_settings()
logger = structlog.get_logger(__name__)

STREAM_KEY = "episode:commands"
CONSUMER_GROUP = "episode-workers"
CONSUMER_NAME = "worker-1"


class EpisodeWorker:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.running = False

    async def start(self):
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await self.redis_client.ping()
        except Exception as e:
            logger.warning("Redis unavailable, worker will run in demo inline mode (no queue)", error=str(e))
            self.redis_client = None
            self.running = True
            logger.info("Episode worker started (demo mode, no redis)")
            # In demo mode, keep alive but don't block on queue
            while self.running:
                await asyncio.sleep(10)
            return
        await self._ensure_consumer_group()
        self.running = True
        logger.info("Episode worker started")
        await self._process_loop()

    async def stop(self):
        self.running = False
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Episode worker stopped")

    async def _ensure_consumer_group(self):
        try:
            await self.redis_client.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
            logger.info("Consumer group created", group=CONSUMER_GROUP)
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
            logger.info("Consumer group already exists", group=CONSUMER_GROUP)

    async def _process_loop(self):
        while self.running:
            try:
                messages = await self.redis_client.xreadgroup(
                    CONSUMER_GROUP,
                    CONSUMER_NAME,
                    {STREAM_KEY: ">"},
                    count=1,
                    block=5000,
                )

                if not messages:
                    continue

                for stream, entries in messages:
                    for entry_id, data in entries:
                        await self._process_episode(entry_id, data)

            except Exception as e:
                logger.error("Error in worker loop", error=str(e))
                await asyncio.sleep(5)

    async def _process_episode(self, entry_id: str, data: Dict[str, Any]):
        episode_id = data.get("episode_id")
        if not episode_id:
            await self.redis_client.xack(STREAM_KEY, CONSUMER_GROUP, entry_id)
            return

        logger.info("Processing episode", episode_id=episode_id)

        async with async_session_maker() as db:
            try:
                episode = await self._get_episode(db, UUID(episode_id))
                if not episode:
                    logger.error("Episode not found", episode_id=episode_id)
                    await self.redis_client.xack(STREAM_KEY, CONSUMER_GROUP, entry_id)
                    return

                target = await self._get_target(db, episode.target_app_id)
                project = await self._get_project(db, episode.project_id)

                if not target or not project:
                    logger.error("Target or project not found")
                    await self.redis_client.xack(STREAM_KEY, CONSUMER_GROUP, entry_id)
                    return

                await self._run_episode(db, episode, target, project)
                await self.redis_client.xack(STREAM_KEY, CONSUMER_GROUP, entry_id)

            except Exception as e:
                logger.error("Failed to process episode", episode_id=episode_id, error=str(e))
                await self._mark_episode_failed(db, UUID(episode_id), str(e))
                await self.redis_client.xack(STREAM_KEY, CONSUMER_GROUP, entry_id)

    async def _get_episode(self, db: AsyncSession, episode_id: UUID) -> Optional[Episode]:
        result = await db.execute(select(Episode).where(Episode.id == episode_id))
        return result.scalar_one_or_none()

    async def _get_target(self, db: AsyncSession, target_id: UUID) -> Optional[TargetApp]:
        result = await db.execute(select(TargetApp).where(TargetApp.id == target_id))
        return result.scalar_one_or_none()

    async def _get_project(self, db: AsyncSession, project_id: UUID) -> Optional[Project]:
        result = await db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def _run_episode(
        self,
        db: AsyncSession,
        episode: Episode,
        target: TargetApp,
        project: Project,
    ):
        episode.status = EpisodeStatus.INITIALIZING
        episode.started_at = datetime.now(UTC)
        await db.commit()

        # --- Sandbox: acquire container and ensure clean snapshot per episode ---
        sandbox_container_id: Optional[str] = None
        sandbox_target_url: Optional[str] = None
        try:
            from sandbox.docker_client import DockerClient
            from sandbox.container_pool import ContainerPool
            from sandbox.snapshot import SnapshotManager
            from sandbox.schemas import SandboxConfig
            docker_client = DockerClient(host=settings.DOCKER_HOST)
            pool = ContainerPool(docker_client=docker_client, max_containers=settings.SANDBOX_MAX_CONTAINERS, network=settings.SANDBOX_NETWORK)
            snap_mgr = SnapshotManager(docker_client=docker_client)
            cfg = SandboxConfig(network=settings.SANDBOX_NETWORK, docker_host=settings.DOCKER_HOST)
            # Try to restore snapshot if exists, else acquire fresh and create snapshot
            snapshot_ref = f"purple-{target.type.value}:clean"
            repo, tag = snapshot_ref.split(":")
            if snap_mgr.get_snapshot_info(repo, tag):
                # snapshot exists -> restore
                restored_id = snap_mgr.restore_snapshot(repo, tag, new_container_name=f"purple-{target.type.value}-{episode.id.hex[:8]}", network=settings.SANDBOX_NETWORK)
                if restored_id:
                    sandbox_container_id = restored_id
                    logger.info("Restored clean snapshot for episode", episode_id=str(episode.id), container_id=restored_id[:12])
            if not sandbox_container_id:
                # No snapshot or restore failed -> acquire from pool
                sandbox_container_id = await pool.acquire(target.type.value, cfg)
                if sandbox_container_id:
                    # Create clean snapshot for next episodes (first time)
                    try:
                        snap_mgr.create_snapshot(sandbox_container_id, repo, tag)
                    except Exception:
                        pass
                    logger.info("Acquired container for episode", episode_id=str(episode.id), container_id=sandbox_container_id[:12])
            if sandbox_container_id:
                status = docker_client.get_container_status(sandbox_container_id)
                if status:
                    # Derive target URL from container ports or use base_url fallback
                    # Prefer mapped host port if available, else internal
                    ports = status.ports or {}
                    # Find first host port
                    host_port = None
                    for container_port, host_bindings in ports.items():
                        if host_bindings:
                            host_port = host_bindings[0].get("HostPort")
                            if host_port:
                                break
                    if host_port:
                        sandbox_target_url = f"http://localhost:{host_port}"
                    else:
                        # internal network address
                        sandbox_target_url = f"http://{sandbox_container_id[:12]}:3000" if target.type.value == "juice_shop" else f"http://{sandbox_container_id[:12]}:80"
        except Exception as e:
            logger.warning("Sandbox unavailable, using target config URL", error=str(e))
            sandbox_container_id = None

        rag_memory = RAGMemory(
            chroma_url=settings.CHROMADB_URL,
            collection_name=settings.CHROMADB_COLLECTION,
        )

        # Factory: select agent pair by scenario (PDF build order: 1R+1B validated, then 2R+2B, then expand)
        scenario = episode.scenario
        if scenario == "injection":
            red_team = InjectionRedTeamAgent(rag_memory=rag_memory, scenario=scenario, target_type=target.type.value)
            detection = InjectionHardeningDetectionAgent(rag_memory=rag_memory, scenario=scenario, target_type=target.type.value)
        elif scenario == "business_logic":
            red_team = BusinessLogicRedTeamAgent(rag_memory=rag_memory, scenario=scenario, target_type=target.type.value)
            detection = BusinessLogicHardeningDetectionAgent(rag_memory=rag_memory, scenario=scenario, target_type=target.type.value)
        elif scenario == "ssrf":
            red_team = SSRFRedTeamAgent(rag_memory=rag_memory, scenario=scenario, target_type=target.type.value)
            detection = SSRFHardeningDetectionAgent(rag_memory=rag_memory, scenario=scenario, target_type=target.type.value)
        elif scenario in ("broken_auth", "idor_auth", "auth_abuse"):
            red_team = AuthAbuseRedTeamAgent(rag_memory=rag_memory, scenario=scenario, target_type=target.type.value)
            detection = AuthHardeningDetectionAgent(rag_memory=rag_memory, scenario=scenario, target_type=target.type.value)
        else:  # default idor
            red_team = RedTeamAgent(rag_memory=rag_memory, scenario=scenario, target_type=target.type.value)
            detection = DetectionAgent(rag_memory=rag_memory, scenario=scenario, target_type=target.type.value)

        # Define event callback to broadcast real-time events
        async def event_callback(episode_id: str, event_type: str, data: dict):
            if event_type == 'attack':
                await broadcast_attack(episode_id, data)
            elif event_type == 'detection':
                await broadcast_detection(episode_id, data)
            elif event_type == 'response':
                await broadcast_response(episode_id, data)
            elif event_type == 'score':
                await broadcast_score(episode_id, data)

        orchestrator = Orchestrator(
            red_team_agent=red_team,
            detection_agent=detection,
            rag_memory=rag_memory,
            max_iterations=episode.constraints.get("max_iterations", 10),
            event_callback=event_callback,
        )

        # Prefer sandbox URL if acquired, else config base_url
        base_target_url = sandbox_target_url or target.config.get("base_url") or f"http://localhost:{target.config.get('exposed_ports', [80])[0]}" if isinstance(target.config.get('exposed_ports'), list) else "http://localhost:3001"
        if isinstance(base_target_url, list):
            base_target_url = base_target_url[0]
        context = EpisodeContext(
            episode_id=episode.id,
            project_id=project.id,
            target_app_id=target.id,
            scenario=episode.scenario,
            constraints=episode.constraints,
            target_url=base_target_url,
            target_type=target.type.value,
        )

        episode.status = EpisodeStatus.RUNNING
        await db.commit()

        try:
            await broadcast_episode_status(str(episode.id), "running")

            final_context = await orchestrator.run_episode(context)

            await self._save_results(db, episode, final_context)

            episode.status = EpisodeStatus.COMPLETED
            episode.completed_at = datetime.now(UTC)
            await broadcast_episode_status(str(episode.id), "completed")

        except Exception as e:
            logger.error("Episode execution failed", episode_id=str(episode.id), error=str(e))
            episode.status = EpisodeStatus.FAILED
            episode.error = str(e)
            episode.completed_at = datetime.now(UTC)
            await broadcast_episode_status(str(episode.id), "failed")

        await db.commit()
        await red_team.close()
        # Release sandbox container back to pool (or cleanup) — snapshot already captured clean state, so release for reuse resets via snapshot next time
        if sandbox_container_id:
            try:
                from sandbox.docker_client import DockerClient
                from sandbox.container_pool import ContainerPool
                from sandbox.schemas import SandboxConfig
                docker_client = DockerClient(host=settings.DOCKER_HOST)
                pool = ContainerPool(docker_client=docker_client, max_containers=settings.SANDBOX_MAX_CONTAINERS, network=settings.SANDBOX_NETWORK)
                # For isolation, we don't just release; we reset via stop+remove if we used snapshot restore path
                # If we used pool acquire, release back
                await pool.release(sandbox_container_id, target.type.value)
            except Exception as e:
                logger.warning("Failed to release sandbox container", container_id=sandbox_container_id[:12], error=str(e))
                try:
                    from sandbox.docker_client import DockerClient
                    dc = DockerClient(host=settings.DOCKER_HOST)
                    dc.stop_container(sandbox_container_id)
                    dc.remove_container(sandbox_container_id, force=True)
                except Exception:
                    pass

    async def _save_results(
        self,
        db: AsyncSession,
        episode: Episode,
        context: EpisodeContext,
    ):
        for attack_data in context.attacks_executed:
            attack = Attack(
                episode_id=episode.id,
                technique_id=attack_data.get("technique_id", ""),
                owasp_category=attack_data.get("owasp_category", ""),
                attack_type=attack_data.get("attack_type", ""),
                success=attack_data.get("result", {}).get("success", False),
                evidence=attack_data.get("result", {}),
                confidence=0.8 if attack_data.get("result", {}).get("success") else 0.2,
                payload=json.dumps(attack_data.get("payload", {})),
                target_endpoint=attack_data.get("target_endpoint"),
                http_method=attack_data.get("http_method"),
                request_headers=attack_data.get("headers"),
                response_status=attack_data.get("result", {}).get("status_code"),
                response_body=attack_data.get("result", {}).get("response_body"),
            )
            db.add(attack)

        for detection_data in context.detections_triggered:
            detection = Detection(
                episode_id=episode.id,
                attack_id=None,
                detected=detection_data.get("detected", False),
                detection_type=detection_data.get("detection_type", "none"),
                confidence=detection_data.get("confidence", 0.0),
                details=detection_data.get("details", {}),
                matched_patterns=detection_data.get("matched_patterns", []),
            )
            db.add(detection)

        for response_data in context.responses_applied:
            response = Response(
                episode_id=episode.id,
                detection_id=None,
                action_type=response_data.get("action_type", ""),
                parameters=response_data.get("parameters", {}),
                target=response_data.get("target"),
                success=response_data.get("result", {}).get("success", False),
                result=response_data.get("result", {}),
            )
            db.add(response)

        if context.posture_score:
            posture = PostureScore(
                episode_id=episode.id,
                project_id=episode.project_id,
                detection_rate=context.posture_score.get("detection_rate", 0.0),
                mttr_seconds=int(context.posture_score.get("mttr_seconds", 0)),
                coverage=context.posture_score.get("coverage", {}),
                overall_score=context.posture_score.get("overall_score", 0.0),
                trend=context.posture_score.get("trend", "stable"),
            )
            db.add(posture)

    async def _mark_episode_failed(self, db: AsyncSession, episode_id: UUID, error: str):
        result = await db.execute(select(Episode).where(Episode.id == episode_id))
        episode = result.scalar_one_or_none()
        if episode:
            episode.status = EpisodeStatus.FAILED
            episode.error = error
            episode.completed_at = datetime.now(UTC)
            await db.commit()


async def main():
    worker = EpisodeWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())