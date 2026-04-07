"""NLP: maps natural language → agent actions."""
import re, uuid
from core.state import agent, log_cmd
from core.youtube import search as yt_search

async def execute(cmd: str, source: str = "api") -> object:
    result = await _route(cmd.lower().strip(), cmd)
    if isinstance(result, str):
        log_cmd(source, cmd, result)
    return result

async def _cmd(action: str, **kw) -> object:
    return await agent.run(str(uuid.uuid4())[:8], {"action": action, **kw})

async def _route(c: str, raw: str) -> object:
    # YouTube
    m = re.search(r"(?:play|youtube|watch)\s+(.+)", c)
    if m:
        q = m.group(1).strip()
        r = yt_search(q, 1)
        if not r or "error" in r[0]: return f"❌ No results for '{q}'"
        v = r[0]
        return await _cmd("youtube_play", url=v["url"], title=v["title"])
    if c == "pause":                             return await _cmd("key", key="k")
    if "fullscreen" in c:                        return await _cmd("key", key="f")
    if "skip forward" in c or "skip ahead" in c: return await _cmd("key", key="l")
    if "skip back" in c or "rewind" in c:        return await _cmd("key", key="j")
    if "next video" in c:                        return await _cmd("hotkey", keys=["shift","n"])

    # Screenshot
    if "screenshot" in c or "capture" in c:      return await _cmd("screenshot")

    # Volume
    m = re.search(r"volume\s+(?:to\s+)?(\d+)", c)
    if m:                  return await _cmd("volume", level=int(m.group(1)))
    if c == "mute":        return await _cmd("volume", level=0)
    if "unmute" in c:      return await _cmd("volume", level=50)
    if "volume up" in c:   return await _cmd("volume_rel", delta=10)
    if "volume down" in c: return await _cmd("volume_rel", delta=-10)

    # Brightness
    m = re.search(r"brightness\s+(?:to\s+)?(\d+)", c)
    if m:                    return await _cmd("brightness", level=int(m.group(1)))
    if "brightness up" in c: return await _cmd("brightness", level=80)
    if "brightness down" in c: return await _cmd("brightness", level=30)

    # Apps
    m = re.search(r"(?:open|launch|start)\s+(.+)", c)
    if m: return await _cmd("launch", name=m.group(1).strip())

    # Mouse
    m = re.search(r"move mouse\s+(?:to\s+)?(\d+)[,\s]+(\d+)", c)
    if m: return await _cmd("mouse_move", x=int(m.group(1)), y=int(m.group(2)))
    if "mouse center" in c:  return await _cmd("mouse_center")
    if "right click" in c:   return await _cmd("click", btn="right")
    if "double click" in c:  return await _cmd("click", btn="double")
    if "click" in c:         return await _cmd("click", btn="left")
    if "scroll down" in c:   return await _cmd("scroll", direction="down", amount=5)
    if "scroll up" in c:     return await _cmd("scroll", direction="up",   amount=5)

    # Keyboard
    m = re.search(r'type\s+"?(.+?)"?\s*$', c)
    if m: return await _cmd("type", text=m.group(1).strip('"'))
    m = re.search(r"press\s+(.+)", c)
    if m: return await _cmd("hotkey", keys=m.group(1).strip().split("+"))

    # Power
    if "lock screen" in c or c == "lock": return await _cmd("lock")
    if c == "sleep":                       return await _cmd("sleep")
    if "restart" in c or "reboot" in c:   return await _cmd("restart")
    m = re.search(r"shutdown(?:\s+in\s+(\d+)\s+min)?", c)
    if m: return await _cmd("shutdown", delay_secs=int(m.group(1) or 0)*60)

    # Iron Hand
    if "iron hand" in c:
        if any(w in c for w in ["on","enable","activate"]):  return await _cmd("ironhand_toggle", enabled=True)
        if any(w in c for w in ["off","disable","stop"]):    return await _cmd("ironhand_toggle", enabled=False)
        return await _cmd("ironhand_toggle")

    # Kill
    m = re.search(r"kill\s+(.+)", c)
    if m: return await _cmd("kill", identifier=m.group(1).strip())

    return f"⚠️ Not understood: '{raw}'"
