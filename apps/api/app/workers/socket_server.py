import asyncio
import json
import socketio
from typing import Dict, Set
from uuid import UUID

from app.core.config import get_settings
from app.core.security import verify_token

settings = get_settings()

# Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=False,
)

# Track connected clients and their episode subscriptions
connected_clients: Dict[str, Dict] = {}
episode_subscriptions: Dict[str, Set[str]] = {}  # episode_id -> set of client_ids


@sio.event
async def connect(sid: str, environ: dict, auth: dict):
    """Handle client connection with JWT authentication"""
    if not auth or 'token' not in auth:
        await sio.disconnect(sid)
        return False

    token = auth['token']
    payload = verify_token(token)
    if not payload:
        await sio.disconnect(sid)
        return False

    user_id = payload.get('sub')
    connected_clients[sid] = {
        'user_id': user_id,
        'subscriptions': set(),
    }
    print(f"Client connected: {sid} (user: {user_id})")
    return True


@sio.event
async def disconnect(sid: str):
    """Handle client disconnection"""
    if sid in connected_clients:
        # Remove from all episode subscriptions
        for episode_id in connected_clients[sid]['subscriptions']:
            if episode_id in episode_subscriptions:
                episode_subscriptions[episode_id].discard(sid)
        del connected_clients[sid]
    print(f"Client disconnected: {sid}")


@sio.event
async def join_episode(sid: str, episode_id: str):
    """Subscribe client to episode events"""
    if sid not in connected_clients:
        return

    # Validate episode_id format
    try:
        UUID(episode_id)
    except ValueError:
        await sio.emit('error', {'message': 'Invalid episode ID'}, to=sid)
        return

    # Add subscription
    connected_clients[sid]['subscriptions'].add(episode_id)
    if episode_id not in episode_subscriptions:
        episode_subscriptions[episode_id] = set()
    episode_subscriptions[episode_id].add(sid)

    await sio.emit('joined_episode', {'episode_id': episode_id}, to=sid)
    print(f"Client {sid} joined episode {episode_id}")


@sio.event
async def leave_episode(sid: str, episode_id: str):
    """Unsubscribe client from episode events"""
    if sid not in connected_clients:
        return

    connected_clients[sid]['subscriptions'].discard(episode_id)
    if episode_id in episode_subscriptions:
        episode_subscriptions[episode_id].discard(sid)

    await sio.emit('left_episode', {'episode_id': episode_id}, to=sid)


async def broadcast_episode_event(episode_id: str, event_type: str, data: dict):
    """Broadcast an episode event to all subscribed clients"""
    if episode_id not in episode_subscriptions:
        return

    event = {
        'type': event_type,
        'episode_id': episode_id,
        'data': data,
        'timestamp': asyncio.get_event_loop().time(),
    }

    # Send to all subscribed clients
    for sid in episode_subscriptions[episode_id]:
        try:
            await sio.emit('episode_event', event, to=sid)
        except Exception as e:
            print(f"Error sending to {sid}: {e}")


async def broadcast_episode_status(episode_id: str, status: str):
    """Broadcast episode status change"""
    if episode_id not in episode_subscriptions:
        return

    event = {
        'type': 'status',
        'episode_id': episode_id,
        'data': {'status': status},
    }

    for sid in episode_subscriptions[episode_id]:
        try:
            await sio.emit('episode_status', event, to=sid)
        except Exception as e:
            print(f"Error sending status to {sid}: {e}")


async def broadcast_attack(episode_id: str, attack_data: dict):
    """Broadcast an attack event"""
    await broadcast_episode_event(episode_id, 'attack', attack_data)


async def broadcast_detection(episode_id: str, detection_data: dict):
    """Broadcast a detection event"""
    await broadcast_episode_event(episode_id, 'detection', detection_data)


async def broadcast_response(episode_id: str, response_data: dict):
    """Broadcast a response event"""
    await broadcast_episode_event(episode_id, 'response', response_data)


async def broadcast_score(episode_id: str, score_data: dict):
    """Broadcast a score event"""
    await broadcast_episode_event(episode_id, 'score', score_data)


# ASGI app
socket_app = socketio.ASGIApp(sio, socketio_path='/socket.io')