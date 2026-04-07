"""J.A.R.V.I.S. Backend — Railway deployment."""
import asyncio, base64, json, logging, os, uuid
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from typing import Optional

from core.state import agent, log_entries
from core.nlp import execute
from core.youtube import search as yt_search
from core.ironhand_ui import PHONE_UI

SECRET       = os.getenv("JARVIS_SECRET", "dev")
BOT_TOKEN    = os.getenv("TELEGRAM_BOT_TOKEN", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
log = logging.getLogger("jarvis")

app = FastAPI(title="J.A.R.V.I.S.", version="2.0",
              docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ── Auth ──────────────────────────────────────────────────────────────────────
def auth(k: Optional[str]):
    if k != SECRET: raise HTTPException(401, "Invalid secret")

# ── Models ────────────────────────────────────────────────────────────────────
class CmdReq(BaseModel): command: str
class AppReq(BaseModel): name: str
class KillReq(BaseModel): identifier: str
class VolReq(BaseModel): level: int
class YTReq(BaseModel): query: str; max_results: int = 6

# ── Bot startup ───────────────────────────────────────────────────────────────
_bot = None

@app.on_event("startup")
async def startup():
    global _bot
    if BOT_TOKEN:
        from core.bot import make_bot
        _bot = make_bot(BOT_TOKEN)
        await _bot.initialize()
        await _bot.start()
        asyncio.create_task(_bot.updater.start_polling(drop_pending_updates=True))
        log.info("✅ Telegram bot started")
    else:
        log.warning("⚠️  No TELEGRAM_BOT_TOKEN — bot disabled")
    log.info("✅ JARVIS backend online")

@app.on_event("shutdown")
async def on_shutdown():
    if _bot:
        await _bot.updater.stop()
        await _bot.stop()
        await _bot.shutdown()

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"ok": True, "agent": agent.connected, "bot": _bot is not None}

# ── API ───────────────────────────────────────────────────────────────────────
@app.post("/api/command")
async def command(req: CmdReq, k: Optional[str] = Header(None, alias="x-api-key")):
    auth(k)
    r = await execute(req.command, "api")
    return {"result": str(r) if not isinstance(r, (dict,list)) else r}

@app.get("/api/stats")
async def stats(k: Optional[str] = Header(None, alias="x-api-key")):
    auth(k)
    return {"connected": agent.connected, "laptop": agent.stats}

@app.get("/api/screenshot")
async def screenshot(k: Optional[str] = Header(None, alias="x-api-key")):
    auth(k)
    r = await agent.run(str(uuid.uuid4())[:8], {"action": "screenshot"})
    if isinstance(r, bytes): return Response(r, media_type="image/png")
    raise HTTPException(503, str(r))

@app.get("/api/processes")
async def processes(k: Optional[str] = Header(None, alias="x-api-key")):
    auth(k)
    r = await agent.run(str(uuid.uuid4())[:8], {"action": "process_list"})
    return r if isinstance(r, list) else []

@app.post("/api/kill")
async def kill(req: KillReq, k: Optional[str] = Header(None, alias="x-api-key")):
    auth(k)
    return {"result": await agent.run(str(uuid.uuid4())[:8], {"action":"kill","identifier":req.identifier})}

@app.get("/api/files")
async def files(path: str = Query("~"), k: Optional[str] = Header(None, alias="x-api-key")):
    auth(k)
    r = await agent.run(str(uuid.uuid4())[:8], {"action":"list_files","path":path})
    return r if isinstance(r, list) else []

@app.get("/api/download")
async def download(path: str = Query(...), k: Optional[str] = Header(None, alias="x-api-key")):
    auth(k)
    r = await agent.run(str(uuid.uuid4())[:8], {"action":"download_file","path":path})
    if isinstance(r, bytes):
        return Response(r, media_type="application/octet-stream",
                        headers={"Content-Disposition": f'attachment; filename="{Path(path).name}"'})
    raise HTTPException(503, str(r))

@app.get("/api/youtube/search")
async def yt_search_ep(q: str = Query(...), limit: int = 6, k: Optional[str] = Header(None, alias="x-api-key")):
    auth(k)
    return {"results": yt_search(q, limit)}

@app.post("/api/youtube/play")
async def yt_play(req: YTReq, k: Optional[str] = Header(None, alias="x-api-key")):
    auth(k)
    results = yt_search(req.query, 1)
    if not results or "error" in results[0]:
        return {"result": f"❌ No results for '{req.query}'"}
    v = results[0]
    r = await agent.run(str(uuid.uuid4())[:8], {"action":"youtube_play","url":v["url"],"title":v["title"]})
    return {"result": r, "video": v}

@app.get("/api/log")
async def get_log(k: Optional[str] = Header(None, alias="x-api-key")):
    auth(k); return log_entries

# ── Iron Hand phone page ──────────────────────────────────────────────────────
@app.get("/ironhand", response_class=HTMLResponse)
async def ironhand(): return PHONE_UI

# ── WebSocket: Laptop Agent ───────────────────────────────────────────────────
_dash_clients: list[WebSocket] = []

@app.websocket("/ws/agent")
async def ws_agent(ws: WebSocket):
    if ws.query_params.get("secret") != SECRET:
        await ws.close(code=4001); return
    await ws.accept()
    await agent.attach(ws)
    log.info("🖥  Agent connected")
    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            kind = data.get("type", "")
            if kind == "stats":
                agent.push_stats(data.get("stats", {}))
                payload = {"connected": True, "laptop": agent.stats}
                for d in _dash_clients:
                    try: await d.send_json(payload)
                    except: pass
            elif kind == "result":
                agent.resolve(data["id"], data["result"])
            elif kind == "screenshot":
                agent.resolve(data["id"], base64.b64decode(data["data"]))
            elif kind == "file":
                agent.resolve(data["id"], base64.b64decode(data["data"]))
            elif kind == "list":
                agent.resolve(data["id"], data["items"])
    except WebSocketDisconnect:
        pass
    except Exception as e:
        log.error(f"Agent error: {e}")
    finally:
        await agent.detach()
        log.info("🖥  Agent disconnected")
        for d in _dash_clients:
            try: await d.send_json({"connected": False, "laptop": {}})
            except: pass

# ── WebSocket: Dashboard ──────────────────────────────────────────────────────
@app.websocket("/ws/stats")
async def ws_stats(ws: WebSocket):
    await ws.accept()
    _dash_clients.append(ws)
    await ws.send_json({"connected": agent.connected, "laptop": agent.stats})
    try:
        while True:
            await asyncio.sleep(25)
            await ws.send_json({"ping": True})
    except WebSocketDisconnect:
        pass
    finally:
        if ws in _dash_clients: _dash_clients.remove(ws)

# ── WebSocket: Iron Hand ──────────────────────────────────────────────────────
@app.websocket("/ws/ironhand")
async def ws_ironhand(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            kind = data.get("type","")
            if kind == "calibrate":
                r = await agent.run(str(uuid.uuid4())[:8], {"action":"ironhand_calibrate"})
                await ws.send_json({"message": str(r), "enabled": False})
            elif kind == "toggle":
                r = await agent.run(str(uuid.uuid4())[:8], {
                    "action":"ironhand_toggle","enabled":data.get("enabled")})
                is_on = "ACTIVE" in str(r)
                await ws.send_json({"enabled": is_on})
            elif kind == "setting":
                await agent.run(str(uuid.uuid4())[:8], {
                    "action":"ironhand_sensitivity","value":float(data.get("value",8))})
            elif kind in ("motion","gesture"):
                await agent.run(str(uuid.uuid4())[:8], {"action":"ironhand_data","data":data})
    except WebSocketDisconnect:
        pass
