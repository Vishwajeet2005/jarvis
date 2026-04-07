"""Central state: laptop agent connection + command routing."""
import asyncio, time
from typing import Optional
from fastapi import WebSocket

class AgentState:
    def __init__(self):
        self.ws: Optional[WebSocket] = None
        self.connected = False
        self.last_seen = 0.0
        self.stats: dict = {}
        self.pending: dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()

    async def attach(self, ws: WebSocket):
        async with self._lock:
            self.ws = ws
            self.connected = True
            self.last_seen = time.time()

    async def detach(self):
        async with self._lock:
            self.ws = None
            self.connected = False
            for f in self.pending.values():
                if not f.done(): f.set_result("❌ Laptop disconnected")
            self.pending.clear()

    async def run(self, cmd_id: str, payload: dict, timeout=12.0) -> object:
        if not self.connected or not self.ws:
            return "❌ Laptop not connected. Start agent on your laptop first."
        loop = asyncio.get_event_loop()
        fut: asyncio.Future = loop.create_future()
        self.pending[cmd_id] = fut
        try:
            await self.ws.send_json({"id": cmd_id, **payload})
            return await asyncio.wait_for(asyncio.shield(fut), timeout=timeout)
        except asyncio.TimeoutError:
            return f"❌ Laptop timed out (>{timeout}s)"
        finally:
            self.pending.pop(cmd_id, None)

    def resolve(self, cmd_id: str, value: object):
        f = self.pending.get(cmd_id)
        if f and not f.done():
            f.set_result(value)

    def push_stats(self, s: dict):
        self.stats = s
        self.last_seen = time.time()

agent = AgentState()

# Command log shown in dashboard
log_entries: list[dict] = []

def log_cmd(source: str, cmd: str, result: str):
    log_entries.append({"t": time.strftime("%H:%M:%S"), "src": source, "cmd": cmd, "res": result})
    if len(log_entries) > 60: log_entries.pop(0)
