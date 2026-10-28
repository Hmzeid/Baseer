"""
Baseer voice-note transcription proxy.

Browser mic -> backend WebSocket (/voice/transcribe) -> Meta realtime
transcription WebSocket. The API key is attached server-side only and is
never sent to the browser, logged, or echoed in any frame.

Our socket protocol (JSON text frames from server):
  {"type": "partial", "text": "..."}   interim transcript
  {"type": "final", "text": "..."}     utterance transcript (appended to notes)
  {"type": "error", "detail": "..."}   failure; the UI keeps typed notes.

Upstream contract: the Meta realtime transcription endpoint URL comes from
env META_TRANSCRIBE_WS_URL (unset by default). Audio chunks from the browser
are relayed byte-for-byte; upstream text frames are relayed verbatim.
Without a configured URL the socket answers one error frame and closes —
typed notes stay the working fallback, never a faked transcript.
"""
from __future__ import annotations

import json
import os

TRANSCRIBE_URL = os.getenv("META_TRANSCRIBE_WS_URL", "")


def _api_key() -> str:
    return os.getenv("MODEL_API_KEY", "") or os.getenv("META_API_KEY", "")


async def proxy(client_ws, accepted: bool = False) -> None:
    if not accepted:
        await client_ws.accept()
    if not TRANSCRIBE_URL:
        await client_ws.send_text(json.dumps({
            "type": "error",
            "detail": "voice transcription is not configured "
                      "(META_TRANSCRIBE_WS_URL unset) — type the note instead",
        }))
        await client_ws.close()
        return
    if not _api_key():
        await client_ws.send_text(json.dumps({
            "type": "error",
            "detail": "voice transcription needs MODEL_API_KEY — type the note instead",
        }))
        await client_ws.close()
        return
    import websockets
    try:
        upstream = await websockets.connect(
            TRANSCRIBE_URL,
            additional_headers={"Authorization": f"Bearer {_api_key()}"},
            max_size=8 * 1024 * 1024,
        )
    except Exception as exc:
        await client_ws.send_text(json.dumps(
            {"type": "error", "detail": f"transcription upstream unreachable: {exc}"}))
        await client_ws.close()
        return
    try:
        async for message in client_ws.iter_bytes():
            await upstream.send(message)
            try:
                reply = await upstream.recv()
            except Exception as exc:
                await client_ws.send_text(json.dumps(
                    {"type": "error", "detail": f"transcription stream ended: {exc}"}))
                break
            if isinstance(reply, bytes):
                continue
            await client_ws.send_text(reply)
    finally:
        try:
            await upstream.close()
        except Exception:
            pass
        try:
            await client_ws.close()
        except Exception:
            pass
