"""
J.A.R.V.I.S. Laptop Agent
Connects to your Railway server and handles all hardware commands.
Run: python agent.py  (or double-click run.bat on Windows)
"""
import asyncio, base64, io, json, logging, os, platform, re, subprocess, sys, time, webbrowser
from pathlib import Path
import psutil, pyautogui, websockets
from dotenv import load_dotenv

load_dotenv()

SERVER = os.getenv("JARVIS_SERVER_URL","").rstrip("/")
SECRET = os.getenv("JARVIS_SECRET","")
OS     = platform.system()

pyautogui.FAILSAFE = False
pyautogui.PAUSE    = 0.03

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("agent.log",encoding="utf-8")]
)
log = logging.getLogger("agent")

# ── Iron Hand state ────────────────────────────────────────────────────────────
class IH:
    enabled=False; sensitivity=8.0; deadzone=1.5; smoothing=0.35
    ref_b=None; ref_g=None; sdx=0.0; sdy=0.0
ih = IH()

# ── Stats ──────────────────────────────────────────────────────────────────────
def stats():
    try:
        c=psutil.cpu_percent(0); m=psutil.virtual_memory()
        d=psutil.disk_usage("/"); n=psutil.net_io_counters()
        b=psutil.sensors_battery(); f=psutil.cpu_freq()
        return {
            "cpu":round(c,1),"cpu_freq":round(f.current) if f else 0,
            "cpu_cores":psutil.cpu_count(logical=True),
            "ram_pct":round(m.percent,1),"ram_used_gb":round(m.used/1e9,2),"ram_total_gb":round(m.total/1e9,2),
            "disk_pct":round(d.percent,1),"disk_used_gb":round(d.used/1e9,1),"disk_total_gb":round(d.total/1e9,1),
            "net_up_mb":round(n.bytes_sent/1e6,1),"net_down_mb":round(n.bytes_recv/1e6,1),
            "battery":round(b.percent,1) if b else None,"plugged":b.power_plugged if b else None,
            "hostname":platform.node(),"os":OS,"uptime":int(time.time()-psutil.boot_time()),
        }
    except Exception as e:
        return {"error":str(e)}

# ── App map ────────────────────────────────────────────────────────────────────
APPS = {
    "chrome":    {"Windows":"start chrome","Darwin":"open -a 'Google Chrome'","Linux":"google-chrome"},
    "firefox":   {"Windows":"start firefox","Darwin":"open -a Firefox","Linux":"firefox"},
    "vscode":    {"Windows":"code","Darwin":"open -a 'Visual Studio Code'","Linux":"code"},
    "spotify":   {"Windows":"start spotify","Darwin":"open -a Spotify","Linux":"spotify"},
    "discord":   {"Windows":"start discord","Darwin":"open -a Discord","Linux":"discord"},
    "notepad":   {"Windows":"notepad","Darwin":"open -a TextEdit","Linux":"gedit"},
    "calculator":{"Windows":"calc","Darwin":"open -a Calculator","Linux":"gnome-calculator"},
    "terminal":  {"Windows":"start cmd","Darwin":"open -a Terminal","Linux":"gnome-terminal"},
    "explorer":  {"Windows":"explorer","Darwin":"open ~","Linux":"nautilus"},
    "vlc":       {"Windows":"start vlc","Darwin":"open -a VLC","Linux":"vlc"},
    "word":      {"Windows":"start winword","Darwin":"open -a 'Microsoft Word'","Linux":"libreoffice --writer"},
    "excel":     {"Windows":"start excel","Darwin":"open -a 'Microsoft Excel'","Linux":"libreoffice --calc"},
    "steam":     {"Windows":"start steam","Darwin":"open -a Steam","Linux":"steam"},
    "paint":     {"Windows":"mspaint","Darwin":"open -a Preview","Linux":"gimp"},
}

# ── Handle ─────────────────────────────────────────────────────────────────────
async def handle(action:str, data:dict) -> object:
    if action == "screenshot":
        buf=io.BytesIO(); pyautogui.screenshot().save(buf,"PNG"); return buf.getvalue()

    if action == "process_list":
        out=[]
        for p in psutil.process_iter(["pid","name","cpu_percent","memory_percent","status"]):
            try:
                i=p.info
                if i["name"]: out.append({"pid":i["pid"],"name":i["name"],"cpu":round(i["cpu_percent"] or 0,1),"ram":round(i["memory_percent"] or 0,2),"status":i["status"]})
            except: pass
        return sorted(out,key=lambda x:x["cpu"],reverse=True)[:80]

    if action == "kill":
        ident=data.get("identifier","")
        try:
            if str(ident).isdigit(): psutil.Process(int(ident)).terminate(); return f"✅ Killed PID {ident}"
            n=0
            for p in psutil.process_iter(["name","pid"]):
                if ident.lower() in (p.info["name"] or "").lower(): p.terminate(); n+=1
            return f"✅ Killed {n} process(es)"
        except Exception as e: return f"❌ {e}"

    if action == "list_files":
        p=Path(data.get("path","~")).expanduser().resolve()
        try:
            items=[]
            for e in sorted(p.iterdir(),key=lambda x:(x.is_file(),x.name.lower()))[:200]:
                try:
                    st=e.stat(); sz=st.st_size
                    hu=next((f"{sz//(1024**i):.1f} {u}" for i,u in enumerate(["B","KB","MB","GB"]) if sz<1024**(i+1)),f"{sz//1024**3:.1f} GB")
                    items.append({"name":e.name,"path":str(e),"is_dir":e.is_dir(),"size":st.st_size if e.is_file() else 0,"size_str":hu if e.is_file() else "—"})
                except: pass
            return items
        except Exception as e: return [{"error":str(e)}]

    if action == "download_file":
        return Path(data.get("path","")).expanduser().open("rb").read()

    if action == "save_file":
        dest=Path.home()/"Downloads"/data.get("name","upload")
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(bytes.fromhex(data.get("data","")))
        return f"✅ Saved to {dest}"

    if action == "launch":
        name=data.get("name","").lower()
        cmd=next((cmds.get(OS) for k,cmds in APPS.items() if k in name),None)
        if not cmd: cmd=f"start {data['name']}" if OS=="Windows" else f"open -a '{data['name']}'" if OS=="Darwin" else data['name']
        try: subprocess.Popen(cmd,shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); return f"✅ Launched {data.get('name')}"
        except Exception as e: return f"❌ {e}"

    if action == "youtube_play":
        url=data.get("url","")
        if url: webbrowser.open(url); return f"▶️ Playing: {data.get('title','')}"
        return "❌ No URL"

    if action == "volume":
        level=max(0,min(100,int(data.get("level",50))))
        try:
            if OS=="Windows":
                from ctypes import cast,POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities,IAudioEndpointVolume
                v=cast(AudioUtilities.GetSpeakers().Activate(IAudioEndpointVolume._iid_,CLSCTX_ALL,None),POINTER(IAudioEndpointVolume))
                v.SetMasterVolumeLevelScalar(level/100,None)
            elif OS=="Darwin": subprocess.run(["osascript","-e",f"set volume output volume {level}"])
            else: subprocess.run(["amixer","-D","pulse","sset","Master",f"{level}%"])
            return f"✅ Volume → {level}%"
        except Exception as e: return f"❌ {e}"

    if action == "volume_rel":
        delta=int(data.get("delta",0))
        try:
            if OS=="Darwin":
                cur=int(subprocess.run(["osascript","-e","output volume of (get volume settings)"],capture_output=True,text=True).stdout.strip())
                nv=max(0,min(100,cur+delta)); subprocess.run(["osascript","-e",f"set volume output volume {nv}"]); return f"✅ Volume → {nv}%"
            elif OS=="Windows":
                from ctypes import cast,POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities,IAudioEndpointVolume
                v=cast(AudioUtilities.GetSpeakers().Activate(IAudioEndpointVolume._iid_,CLSCTX_ALL,None),POINTER(IAudioEndpointVolume))
                cur=int(v.GetMasterVolumeLevelScalar()*100); nv=max(0,min(100,cur+delta))
                v.SetMasterVolumeLevelScalar(nv/100,None); return f"✅ Volume → {nv}%"
        except Exception as e: return f"❌ {e}"

    if action == "brightness":
        level=max(0,min(100,int(data.get("level",50))))
        try: import screen_brightness_control as sbc; sbc.set_brightness(level); return f"✅ Brightness → {level}%"
        except Exception as e: return f"❌ {e}"

    if action == "mouse_move":
        pyautogui.moveTo(int(data["x"]),int(data["y"]),duration=0.2); return f"✅ Mouse → ({data['x']},{data['y']})"

    if action == "mouse_center":
        w,h=pyautogui.size(); pyautogui.moveTo(w//2,h//2,duration=0.2); return "✅ Mouse → center"

    if action == "click":
        btn=data.get("btn","left")
        {"right":pyautogui.rightClick,"double":pyautogui.doubleClick,"middle":pyautogui.middleClick}.get(btn,pyautogui.click)()
        return f"✅ {btn.capitalize()} click"

    if action == "scroll":
        d2=data.get("direction","down"); a=int(data.get("amount",3))
        pyautogui.scroll(-a if d2=="down" else a); return f"✅ Scrolled {d2}"

    if action == "type":
        pyautogui.typewrite(str(data.get("text","")),interval=0.03); return "✅ Typed"

    if action == "key":
        pyautogui.press(data.get("key","")); return f"✅ Key: {data.get('key')}"

    if action == "hotkey":
        keys=data.get("keys",[]); pyautogui.hotkey(*keys) if keys else None; return f"✅ {'+'.join(keys)}"

    POWER = {
        "lock":     {"Windows":"rundll32.exe user32.dll,LockWorkStation","Darwin":"pmset displaysleepnow","Linux":"loginctl lock-session"},
        "sleep":    {"Windows":"rundll32.exe powrprof.dll,SetSuspendState 0,1,0","Darwin":"pmset sleepnow","Linux":"systemctl suspend"},
    }
    if action in POWER:
        subprocess.Popen(POWER[action].get(OS,""),shell=True); return f"✅ {action.capitalize()}"

    if action == "shutdown":
        d2=int(data.get("delay_secs",0))
        if OS=="Windows": subprocess.Popen(f"shutdown /s /t {d2}",shell=True)
        elif OS=="Darwin": subprocess.Popen(f"sudo shutdown -h +{max(1,d2//60)}",shell=True)
        else: subprocess.Popen(f"shutdown -h +{max(1,d2//60)}",shell=True)
        return f"✅ Shutdown in {d2}s"

    if action == "restart":
        if OS=="Windows": subprocess.Popen("shutdown /r /t 5",shell=True)
        elif OS=="Darwin": subprocess.Popen("sudo shutdown -r now",shell=True)
        else: subprocess.Popen("reboot",shell=True)
        return "✅ Restarting"

    # Iron Hand
    if action == "ironhand_toggle":
        e=data.get("enabled"); ih.enabled=not ih.enabled if e is None else bool(e)
        ih.ref_b=ih.ref_g=None; ih.sdx=ih.sdy=0.0
        return f"🤚 Iron Hand {'ACTIVE ⚡' if ih.enabled else 'INACTIVE'}"

    if action == "ironhand_calibrate":
        ih.ref_b=ih.ref_g=None; ih.sdx=ih.sdy=0.0; return "🎯 Calibrated"

    if action == "ironhand_sensitivity":
        ih.sensitivity=max(1.0,min(30.0,float(data.get("value",8)))); return f"✅ Sensitivity → {ih.sensitivity}"

    if action == "ironhand_data":
        gyro=data.get("data",{}); kind=gyro.get("type","motion")
        if kind=="gesture":
            g=gyro.get("gesture","")
            if g=="tap": pyautogui.click()
            elif g=="doubletap": pyautogui.doubleClick()
            elif g=="longtap": pyautogui.rightClick()
            elif g=="shake": pyautogui.scroll(-3)
            return None
        if not ih.enabled or kind!="motion": return None
        beta=gyro.get("beta",0.0); gamma=gyro.get("gamma",0.0)
        if ih.ref_b is None: ih.ref_b=beta; ih.ref_g=gamma; return None
        dx=gamma-ih.ref_g; dy=beta-ih.ref_b
        if abs(dx)<ih.deadzone: dx=0
        if abs(dy)<ih.deadzone: dy=0
        if not dx and not dy: ih.ref_b=beta; ih.ref_g=gamma; return None
        sm=ih.smoothing; ih.sdx=sm*dx+(1-sm)*ih.sdx; ih.sdy=sm*dy+(1-sm)*ih.sdy
        px=int(ih.sdx*ih.sensitivity); py=int(ih.sdy*ih.sensitivity)
        if px or py:
            try:
                cx,cy=pyautogui.position(); sw,sh=pyautogui.size()
                pyautogui.moveTo(max(0,min(sw-1,cx+px)),max(0,min(sh-1,cy+py)),duration=0)
            except: pass
        ih.ref_b=beta; ih.ref_g=gamma; return None

    return f"⚠️ Unknown action: {action}"

# ── Connection loop ────────────────────────────────────────────────────────────
async def run():
    if not SERVER or not SECRET:
        print("\n❌  Set JARVIS_SERVER_URL and JARVIS_SECRET in agent/.env\n")
        sys.exit(1)

    ws_url = SERVER.replace("https://","wss://").replace("http://","ws://") + f"/ws/agent?secret={SECRET}"
    log.info(f"⚡ Connecting to {SERVER}")

    while True:
        try:
            async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as ws:
                log.info("✅ Connected")
                print(f"\n{'='*52}\n  J.A.R.V.I.S. AGENT — ONLINE\n  Server: {SERVER}\n  Ctrl+C to stop\n{'='*52}\n")

                async def push():
                    while True:
                        try: await ws.send(json.dumps({"type":"stats","stats":stats()}))
                        except: break
                        await asyncio.sleep(2)

                task = asyncio.create_task(push())
                try:
                    async for raw in ws:
                        d = json.loads(raw)
                        cid = d.get("id",""); action = d.get("action","")
                        log.info(f"← {action}  {cid}")
                        try:    result = await handle(action, d)
                        except Exception as e: result = f"❌ {e}"; log.error(f"{action}: {e}")
                        if result is None: continue
                        if isinstance(result, bytes):
                            t = "screenshot" if action=="screenshot" else "file"
                            await ws.send(json.dumps({"type":t,"id":cid,"data":base64.b64encode(result).decode()}))
                        elif isinstance(result, list):
                            await ws.send(json.dumps({"type":"list","id":cid,"items":result}))
                        else:
                            await ws.send(json.dumps({"type":"result","id":cid,"result":str(result)}))
                finally:
                    task.cancel()

        except (websockets.ConnectionClosed, OSError) as e:
            log.warning(f"Disconnected ({e}) — retrying in 5s")
            await asyncio.sleep(5)
        except Exception as e:
            log.error(f"Error ({e}) — retrying in 10s")
            await asyncio.sleep(10)

if __name__ == "__main__":
    try: asyncio.run(run())
    except KeyboardInterrupt: print("\n⛔ Agent stopped.")
