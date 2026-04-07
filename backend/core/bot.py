"""Telegram bot — runs inside Railway, talks to laptop via agent."""
import io, logging, os, uuid
from telegram import (BotCommand, InlineKeyboardButton as B,
                      InlineKeyboardMarkup as K, InputFile, Update)
from telegram.ext import (Application, CallbackQueryHandler,
                           CommandHandler, MessageHandler, filters, ContextTypes)
from core.state import agent
from core.nlp import execute
from core.youtube import search as yt_search

log = logging.getLogger("jarvis.bot")
UID = int(os.getenv("TELEGRAM_USER_ID", "0"))

def ok(u: Update) -> bool:
    return u.effective_user.id == UID

def badge(): return "🟢 Laptop Online" if agent.connected else "🔴 Laptop Offline"

def fmt(s: dict) -> str:
    if not s: return f"❌ No data — {badge()}"
    bat = f"{s.get('battery',0):.0f}% {'🔌' if s.get('plugged') else '🔋'}" if s.get("battery") else "N/A"
    h, m = divmod(s.get("uptime",0)//60, 60)
    return (
        f"⚡ *LAPTOP STATUS* — _{badge()}_\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🖥 `{s.get('hostname','?')}` · {s.get('os','?')} · Up: `{h}h {m}m`\n\n"
        f"🔥 CPU   `{s.get('cpu',0):.1f}%` @ `{s.get('cpu_freq',0):.0f} MHz`\n"
        f"🧠 RAM   `{s.get('ram_used_gb',0)}/{s.get('ram_total_gb',0)} GB` ({s.get('ram_pct',0):.1f}%)\n"
        f"💾 Disk  `{s.get('disk_used_gb',0)}/{s.get('disk_total_gb',0)} GB` ({s.get('disk_pct',0):.1f}%)\n"
        f"🔋 Batt  `{bat}` · Net ↑`{s.get('net_up_mb',0)}` ↓`{s.get('net_down_mb',0)} MB`"
    )

MENU = K([[B("📊 Stats",      callback_data="m:stats"),  B("📸 Screenshot", callback_data="m:ss")],
          [B("🎵 YouTube",    callback_data="m:yt"),     B("📋 Processes",  callback_data="m:procs")],
          [B("📁 Files",      callback_data="m:files"),  B("🤚 Iron Hand",  callback_data="m:ih")],
          [B("⚡ Power",      callback_data="m:power"),  B("🔊 Volume",     callback_data="m:vol")]])

async def start(u: Update, _):
    if not ok(u): return
    await u.message.reply_text(
        f"🤖 *J.A.R.V.I.S. ONLINE*\n━━━━━━━━━━━━━━━━━━━━━━━━\n_{badge()}_\n\nType any command or use the menu:",
        reply_markup=MENU, parse_mode="Markdown")

async def help_cmd(u: Update, _):
    if not ok(u): return
    await u.message.reply_text(
        "⚡ *COMMANDS*\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "`open chrome` · `open spotify` · `open vscode`\n"
        "`play lofi beats` · `pause` · `fullscreen` · `next video`\n"
        "`click` · `right click` · `scroll down` · `scroll up`\n"
        "`type Hello World` · `press ctrl+c`\n"
        "`set volume 70` · `mute` · `volume up`\n"
        "`set brightness 80`\n"
        "`lock screen` · `sleep` · `restart` · `shutdown in 5 minutes`\n"
        "`iron hand on` · `iron hand off`\n\n"
        "*/status* /screenshot /apps /youtube /help", parse_mode="Markdown")

async def status_cmd(u: Update, _):
    if not ok(u): return
    m = await u.message.reply_text("🔄 _Fetching..._", parse_mode="Markdown")
    await m.edit_text(fmt(agent.stats), parse_mode="Markdown")

async def ss_cmd(u: Update, _):
    if not ok(u): return
    m = await u.message.reply_text("📸 _Capturing..._", parse_mode="Markdown")
    r = await execute("screenshot", "telegram")
    if isinstance(r, bytes):
        await u.message.reply_photo(InputFile(io.BytesIO(r), "jarvis.png"))
        await m.delete()
    else:
        await m.edit_text(f"`{r}`", parse_mode="Markdown")

async def apps_cmd(u: Update, _):
    if not ok(u): return
    r = await agent.run(str(uuid.uuid4())[:8], {"action": "process_list"})
    if isinstance(r, list):
        lines = ["📋 *TOP PROCESSES*\n━━━━━━━━━━━━━━━━"]
        for p in r[:15]:
            lines.append(f"`{p['pid']:>6}` `{p['name'][:22]:<22}` `{p['cpu']:>5.1f}%`")
        await u.message.reply_text("\n".join(lines), parse_mode="Markdown")
    else:
        await u.message.reply_text(str(r))

async def yt_cmd(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ok(u): return
    if not ctx.args:
        await u.message.reply_text("Usage: `/youtube lofi beats`", parse_mode="Markdown"); return
    q = " ".join(ctx.args)
    m = await u.message.reply_text(f"🔍 _Searching:_ `{q}`...", parse_mode="Markdown")
    results = yt_search(q, 5)
    if not results or "error" in results[0]:
        await m.edit_text("❌ No results."); return
    text = f"🎵 *{q}*\n━━━━━━━━━━━━━━━━\n"
    kb = []
    for i, v in enumerate(results):
        text += f"`{i+1}.` *{v['title'][:44]}*\n   _{v['channel']}_ · {v['duration']}\n"
        kb.append([B(f"▶ {v['title'][:38]}", callback_data=f"yt:{v['id']}:{v['title'][:18]}")])
    kb.append([B("← Back", callback_data="m:main")])
    await m.edit_text(text, reply_markup=K(kb), parse_mode="Markdown")

async def text_msg(u: Update, _):
    if not ok(u): return
    m = await u.message.reply_text("⚡ _Processing..._", parse_mode="Markdown")
    r = await execute(u.message.text.strip(), "telegram")
    if isinstance(r, bytes):
        await u.message.reply_photo(InputFile(io.BytesIO(r), "jarvis.png"))
        await m.delete()
    else:
        await m.edit_text(f"`{r}`", parse_mode="Markdown")

async def doc_msg(u: Update, _):
    if not ok(u): return
    doc = u.message.document
    if not doc: return
    f = await doc.get_file()
    buf = io.BytesIO(); await f.download_to_memory(buf)
    r = await agent.run(str(uuid.uuid4())[:8], {
        "action": "save_file",
        "name": doc.file_name or "upload",
        "data": buf.getvalue().hex()
    })
    await u.message.reply_text(f"`{r}`", parse_mode="Markdown")

async def cb(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    if not ok(u): return
    d = q.data

    async def edit(txt, kb=None):
        await q.edit_message_text(txt, reply_markup=kb, parse_mode="Markdown")

    if d == "m:main":    await edit(f"🤖 *J.A.R.V.I.S.* — _{badge()}_", MENU)
    elif d == "m:stats": await edit(fmt(agent.stats))
    elif d == "m:ss":
        await edit("📸 _Capturing..._")
        r = await execute("screenshot", "telegram")
        if isinstance(r, bytes):
            await ctx.bot.send_photo(q.message.chat_id, InputFile(io.BytesIO(r), "ss.png"))
            await edit("📸 Done.")
        else: await edit(f"`{r}`")

    elif d == "m:procs":
        r = await agent.run(str(uuid.uuid4())[:8], {"action": "process_list"})
        if isinstance(r, list):
            lines = ["📋 *PROCESSES*\n━━━━━━━━━━━━━━━━"]
            for p in r[:14]: lines.append(f"`{p['pid']:>6}` {p['name'][:22]:<22} `{p['cpu']:>5.1f}%`")
            await edit("\n".join(lines))
        else: await edit(str(r))

    elif d == "m:files":
        r = await agent.run(str(uuid.uuid4())[:8], {"action": "list_files", "path": "~"})
        if isinstance(r, list):
            lines = ["📁 *HOME*\n━━━━━━━━━━━━━━━━"]
            for i in r[:14]: lines.append(f"{'📂' if i['is_dir'] else '📄'} {i['name'][:35]}")
            await edit("\n".join(lines))
        else: await edit(str(r))

    elif d == "m:yt":
        await edit("🎵 *YOUTUBE DJ*\n━━━━━━━━━━━━━━━━\nSend `/youtube <search>` to find videos",
            K([[B("⏯",callback_data="ytc:k"), B("⏪",callback_data="ytc:j"), B("⏩",callback_data="ytc:l")],
               [B("🔲",callback_data="ytc:f"), B("🔇",callback_data="ytc:m"), B("⏭",callback_data="ytc:n")],
               [B("← Back",callback_data="m:main")]]))

    elif d.startswith("ytc:"):
        key = d[4:]
        if key == "n": r = await agent.run(str(uuid.uuid4())[:8], {"action":"hotkey","keys":["shift","n"]})
        else:          r = await agent.run(str(uuid.uuid4())[:8], {"action":"key","key":key})
        await edit(f"🎵 `{r}`", K([[B("← YouTube",callback_data="m:yt")]]))

    elif d.startswith("yt:"):
        parts = d[3:].split(":",1)
        r = await agent.run(str(uuid.uuid4())[:8], {
            "action":"youtube_play", "url":f"https://www.youtube.com/watch?v={parts[0]}",
            "title": parts[1].replace("_"," ") if len(parts)>1 else ""
        })
        await edit(f"🎵 `{r}`", K([[B("⏯ Controls",callback_data="m:yt")]]))

    elif d == "m:ih":
        await edit("🤚 *IRON HAND*\n━━━━━━━━━━━━━━━━\nOpen on phone: your Railway URL + `/ironhand`\n_Tilt = cursor · Tap = click_",
            K([[B("⚡ Enable",callback_data="ih:on"), B("⏹ Disable",callback_data="ih:off")],
               [B("🎯 Calibrate",callback_data="ih:cal"), B("← Back",callback_data="m:main")]]))

    elif d.startswith("ih:"):
        a = d[3:]
        if a == "cal": r = await agent.run(str(uuid.uuid4())[:8], {"action":"ironhand_calibrate"})
        else: r = await agent.run(str(uuid.uuid4())[:8], {"action":"ironhand_toggle","enabled": a=="on"})
        await edit(f"🤚 `{r}`")

    elif d == "m:power":
        await edit("⚡ *POWER*\n━━━━━━━━━━━━━━━━",
            K([[B("🔒 Lock",callback_data="pw:lock"), B("😴 Sleep",callback_data="pw:sleep")],
               [B("🔄 Restart",callback_data="pw:restart"), B("⛔ Shutdown",callback_data="pw:shutdown")],
               [B("← Back",callback_data="m:main")]]))

    elif d.startswith("pw:"):
        a = d[3:]
        payload = {"action": a}
        if a == "shutdown": payload["delay_secs"] = 30
        r = await agent.run(str(uuid.uuid4())[:8], payload)
        await edit(f"⚡ `{r}`")

    elif d == "m:vol":
        await edit("🔊 *VOLUME*\n━━━━━━━━━━━━━━━━",
            K([[B("🔉 −10",callback_data="v:down"), B("🔊 +10",callback_data="v:up")],
               [B("🔇 Mute",callback_data="v:mute"), B("← Back",callback_data="m:main")]]))

    elif d.startswith("v:"):
        a = d[2:]
        if a == "mute": r = await agent.run(str(uuid.uuid4())[:8], {"action":"volume","level":0})
        else: r = await agent.run(str(uuid.uuid4())[:8], {"action":"volume_rel","delta": 10 if a=="up" else -10})
        await edit(f"🔊 `{r}`")

async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("start","Main menu"), BotCommand("status","Laptop stats"),
        BotCommand("screenshot","Take screenshot"), BotCommand("apps","Running processes"),
        BotCommand("youtube","Search & play YouTube"), BotCommand("help","All commands"),
    ])

def make_bot(token: str) -> Application:
    app = Application.builder().token(token).post_init(post_init).build()
    for cmd, fn in [("start",start),("help",help_cmd),("status",status_cmd),
                    ("screenshot",ss_cmd),("apps",apps_cmd),("youtube",yt_cmd)]:
        app.add_handler(CommandHandler(cmd, fn))
    app.add_handler(CallbackQueryHandler(cb))
    app.add_handler(MessageHandler(filters.Document.ALL, doc_msg))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_msg))
    return app
