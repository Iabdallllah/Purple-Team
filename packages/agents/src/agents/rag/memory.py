import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
import structlog
import json

from agents.schemas import EpisodeContext, RedTeamAction, DetectionResult, ResponseAction
try:
    from agents.kg.graph import get_knowledge_graph
    _KG_AVAILABLE=True
except Exception:
    _KG_AVAILABLE=False

logger = structlog.get_logger(__name__)


class RAGMemory:
    def __init__(
        self,
        chroma_url: str = "http://localhost:8000",
        collection_name: str = "purple-episodes",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        self.collection_name = collection_name
        self._fallback_store: List[Dict[str, Any]] = []
        self._available = False
        try:
            self.client = chromadb.HttpClient(
                host=chroma_url.replace("http://", "").split(":")[0],
                port=int(chroma_url.split(":")[-1]) if ":" in chroma_url else 8000,
                settings=Settings(anonymized_telemetry=False),
            )
            # quick heartbeat
            self.client.heartbeat()
            self.embedding_model = SentenceTransformer(embedding_model)
            self._ensure_collection()
            self._available = True
        except Exception as e:
            logger.warning("RAGMemory Chroma/SentenceTransformer unavailable, using in-memory stub", error=str(e))
            self.client = None
            self.collection = None
            self.embedding_model = None
            self._available = False

    def _ensure_collection(self):
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        logger.info("RAG collection ready", collection=self.collection_name)

    def _embed(self, text: str) -> List[float]:
        if not self._available or self.embedding_model is None:
            # deterministic hash-based stub embedding (384-dim like MiniLM)
            import hashlib
            h = hashlib.sha256(text.encode()).digest()
            # expand to 384 floats in [0,1)
            vals = []
            for i in range(384):
                vals.append(((h[i % len(h)] + i*31) % 255) / 255.0)
            return vals
        return self.embedding_model.encode(text).tolist()

    def store_episode(
        self,
        episode_id: UUID,
        scenario: str,
        target_type: str,
        attacks: List[RedTeamAction],
        detections: List[DetectionResult],
        responses: List[ResponseAction],
        posture_score: Dict[str, Any],
        success: bool,
    ) -> None:
        timestamp = datetime.utcnow().isoformat()

        attack_texts = [f"{a.technique_id}: {a.attack_type} on {a.target_endpoint}" for a in attacks]
        detection_texts = [f"{d.detection_type}: {'detected' if d.detected else 'missed'} (conf: {d.confidence})" for d in detections]
        response_texts = [f"{r.action_type}: {r.target}" for r in responses]

        full_text = f"""
Scenario: {scenario}
Target: {target_type}
Attacks: {'; '.join(attack_texts)}
Detections: {'; '.join(detection_texts)}
Responses: {'; '.join(response_texts)}
Outcome: {'Success' if success else 'Failure'}
Posture Score: {posture_score.get('overall_score', 0)}
"""

        metadata = {
            "episode_id": str(episode_id),
            "scenario": scenario,
            "target_type": target_type,
            "success": success,
            "overall_score": posture_score.get("overall_score", 0),
            "detection_rate": posture_score.get("detection_rate", 0),
            "timestamp": timestamp,
            "attacks_count": len(attacks),
            "detections_count": len(detections),
            "responses_count": len(responses),
        }

        if not self._available:
            self._fallback_store.append({"episode_id": str(episode_id), "document": full_text, "metadata": metadata, "scenario": scenario, "target_type": target_type})
            logger.info("Episode stored in RAG (in-memory stub)", episode_id=str(episode_id))
            return
        try:
            self.collection.add(
                documents=[full_text],
                embeddings=[self._embed(full_text)],
                metadatas=[metadata],
                ids=[str(episode_id)],
            )
            logger.info("Episode stored in RAG", episode_id=str(episode_id))
        except Exception as e:
            logger.warning("RAG store failed, falling back to memory", error=str(e))
            self._fallback_store.append({"episode_id": str(episode_id), "document": full_text, "metadata": metadata, "scenario": scenario, "target_type": target_type})

    def retrieve_similar(
        self,
        scenario: str,
        target_type: str,
        attack_description: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        kg_ctx=""
        if _KG_AVAILABLE:
            try:
                kg=get_knowledge_graph()
                kg_ctx=kg.expand_query(scenario)
            except Exception:
                kg_ctx=""
        query_text = f"Scenario: {scenario}, Target: {target_type}, Attack: {attack_description} | KG: {kg_ctx}"
        query_embedding = self._embed(query_text)

        if not self._available:
            # filter fallback store by scenario/target
            filtered = [s for s in self._fallback_store if s.get("scenario")==scenario and s.get("target_type")==target_type]
            # simple similarity: most recent first
            filtered = sorted(filtered, key=lambda x: x["metadata"]["timestamp"], reverse=True)[:n_results]
            return [{"episode_id": s["episode_id"], "document": s["document"], "metadata": s["metadata"], "distance": 0} for s in filtered]
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={"$and": [{"scenario": scenario}, {"target_type": target_type}]},
            )
            similar_episodes = []
            for i in range(len(results["ids"][0])):
                similar_episodes.append({
                    "episode_id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else 0,
                })
            logger.info("Retrieved similar episodes", count=len(similar_episodes), scenario=scenario)
            return similar_episodes
        except Exception as e:
            logger.warning("RAG retrieve failed, using fallback", error=str(e))
            return []

    def retrieve_by_technique(
        self,
        technique_id: str,
        n_results: int = 3,
    ) -> List[Dict[str, Any]]:
        kg_ctx=""
        if _KG_AVAILABLE:
            try:
                kg=get_knowledge_graph()
                kg_ctx=kg.expand_query(scenario="", technique_id=technique_id)
            except Exception:
                kg_ctx=""
        query_text = f"MITRE Technique: {technique_id} | {kg_ctx}"
        query_embedding = self._embed(query_text)

        if not self._available:
            filtered = [s for s in self._fallback_store if technique_id in s["document"]]
            return [{"episode_id": s["episode_id"], "document": s["document"], "metadata": s["metadata"]} for s in filtered[:n_results]]
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
            )
            similar = []
            for i in range(len(results["ids"][0])):
                similar.append({
                    "episode_id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                })
            return similar
        except Exception:
            return []

    def get_episode_history(self, scenario: str, target_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not self._available:
            filtered = [s for s in self._fallback_store if s.get("scenario")==scenario and s.get("target_type")==target_type]
            history = [{"episode_id": s["episode_id"], "metadata": s["metadata"]} for s in filtered]
            return sorted(history, key=lambda x: x["metadata"]["timestamp"], reverse=True)[:limit]
        try:
            results = self.collection.query(
                query_embeddings=[self._embed(f"Scenario: {scenario} Target: {target_type}")],
                n_results=limit,
                where={"$and": [{"scenario": scenario}, {"target_type": target_type}]},
            )
            history = []
            for i in range(len(results["ids"][0])):
                history.append({
                    "episode_id": results["ids"][0][i],
                    "metadata": results["metadatas"][0][i],
                })
            return sorted(history, key=lambda x: x["metadata"]["timestamp"], reverse=True)
        except Exception:
            return []

    def get_learning_curve(self, scenario: str, target_type: str) -> List[float]:
        history = self.get_episode_history(scenario, target_type, limit=20)
        scores = [h["metadata"]["overall_score"] for h in history]
        return list(reversed(scores))