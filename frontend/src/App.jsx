import { useState, useEffect, useRef, useCallback } from 'react';

// ── Config ────────────────────────────────────────────────────────────────────
const API    = process.env.REACT_APP_API_URL   || 'http://localhost:8000';
const SECRET = process.env.REACT_APP_SECRET    || 'dev';
const H      = { 'Content-Type': 'application/json', 'x-api-key': SECRET };
const WS     = API.replace('https://','wss://').replace('http://','ws://');

function api(path, opts={}) { return fetch(`${API}${path}`, {headers:H,...opts}).then(r=>r.json()); }
function post(path,body) { return api(path,{method:'POST',body:JSON.stringify(body)}); }

// ── WebSocket hook ────────────────────────────────────────────────────────────
function useWS(path) {
  const [data, setData] = useState(null);
  const [up,   setUp]   = useState(false);
  const ws = useRef(null);
  const connect = useCallback(() => {
    const w = new WebSocket(`${WS}${path}`);
    w.onopen    = () => setUp(true);
    w.onmessage = e => { try { setData(JSON.parse(e.data)); } catch {} };
    w.onclose   = () => { setUp(false); setTimeout(connect, 3000); };
    w.onerror   = () => w.close();
    ws.current  = w;
  },[path]);
  useEffect(()=>{ connect(); return ()=>ws.current?.close(); },[connect]);
  return { data, up };
}

// ── Tokens ────────────────────────────────────────────────────────────────────
const T = {
  bg:'#020c1b', bg2:'#060f1e', blue:'#00b4ff', cyan:'#00e5ff',
  green:'#00e676', orange:'#ff6b35', red:'#ff3344', purple:'#b44dff',
  text:'#b8d8f0', dim:'#3a607a',
  border:'rgba(0,180,255,0.14)', borderH:'rgba(0,180,255,0.38)',
};

// ── Global CSS ────────────────────────────────────────────────────────────────
const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Exo+2:wght@300;400;500;600&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body,#root{width:100%;height:100%;background:${T.bg};overflow:hidden}
body{font-family:'Exo 2',sans-serif;color:${T.text};font-size:12px}
::-webkit-scrollbar{width:3px}
::-webkit-scrollbar-thumb{background:${T.border};border-radius:2px}
button,input{font-family:inherit}
@keyframes rot{to{transform:rotate(360deg)}}
@keyframes pulse{0%,100%{box-shadow:0 0 8px ${T.cyan},0 0 16px rgba(0,229,255,.3)}50%{box-shadow:0 0 18px ${T.cyan},0 0 40px rgba(0,229,255,.5)}}
@keyframes scan{0%{top:-3px;opacity:0}5%{opacity:1}95%{opacity:.7}100%{top:100vh;opacity:0}}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
@keyframes fadeUp{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
@keyframes shimmer{0%{transform:translateX(-100%)}100%{transform:translateX(400%)}}
`;

// ── Primitives ────────────────────────────────────────────────────────────────
function Btn({children,onClick,active,danger,small,full,style={}}) {
  const s={
    background:'transparent',
    border:`1px solid ${danger?T.orange:active?T.cyan:T.blue}`,
    color:danger?T.orange:active?T.cyan:T.blue,
    fontFamily:'Orbitron,sans-serif',fontSize:small?'7px':'8px',
    letterSpacing:'1px',padding:small?'3px 8px':'5px 12px',
    cursor:'pointer',transition:'all .15s',whiteSpace:'nowrap',
    width:full?'100%':'auto',textAlign:full?'center':'left',
    ...style,
  };
  return <button style={s} onClick={onClick}
    onMouseEnter={e=>e.currentTarget.style.background='rgba(0,180,255,.1)'}
    onMouseLeave={e=>e.currentTarget.style.background='transparent'}>{children}</button>;
}

function In({value,onChange,onEnter,placeholder,style={}}) {
  return <input value={value} onChange={e=>onChange(e.target.value)}
    placeholder={placeholder} onKeyDown={e=>e.key==='Enter'&&onEnter?.()}
    style={{background:'rgba(0,180,255,.04)',border:`1px solid ${T.border}`,color:T.text,
            outline:'none',padding:'4px 8px',fontSize:'11px',transition:'border-color .2s',...style}}
    onFocus={e=>e.target.style.borderColor=T.blue}
    onBlur={e=>e.target.style.borderColor=T.border}/>;
}

function Panel({title,icon,children,status='on',style={}}) {
  const dot={on:T.green,off:T.red,warn:T.orange}[status]||T.green;
  return (
    <div style={{background:T.bg2,border:`1px solid ${T.border}`,display:'flex',
                 flexDirection:'column',position:'relative',overflow:'hidden',
                 transition:'border-color .3s',...style}}
      onMouseEnter={e=>e.currentTarget.style.borderColor=T.borderH}
      onMouseLeave={e=>e.currentTarget.style.borderColor=T.border}>
      {/* Corner brackets */}
      {[{t:0,l:0},{t:0,r:0},{b:0,l:0},{b:0,r:0}].map((pos,i)=>{
        const isT=i<2, isL=i%2===0;
        return <div key={i} style={{position:'absolute',width:10,height:10,zIndex:2,...pos}}>
          <div style={{position:'absolute',top:0,[isL?'left':'right']:0,width:10,height:1.5,background:T.blue}}/>
          <div style={{position:'absolute',top:0,[isL?'left':'right']:0,width:1.5,height:10,background:T.blue}}/>
        </div>;
      })}
      <div style={{display:'flex',alignItems:'center',gap:6,padding:'6px 12px',
                   borderBottom:`1px solid ${T.border}`,flexShrink:0,
                   background:'linear-gradient(90deg,rgba(0,180,255,.06),transparent)'}}>
        <span style={{fontSize:12}}>{icon}</span>
        <span style={{fontFamily:'Orbitron,sans-serif',fontSize:9,letterSpacing:'2px',color:T.blue,flex:1}}>{title}</span>
        <div style={{width:6,height:6,borderRadius:'50%',background:dot,boxShadow:`0 0 6px ${dot}`,animation:'blink 2s infinite'}}/>
      </div>
      <div style={{padding:'10px 12px',flex:1,overflow:'hidden'}}>{children}</div>
    </div>
  );
}

function Bar({label,value,color=T.blue}) {
  const pct=Math.min(100,Math.max(0,value));
  const c=pct>90?T.red:pct>75?T.orange:color;
  return (
    <div style={{marginBottom:7}}>
      <div style={{display:'flex',justifyContent:'space-between',marginBottom:3}}>
        <span style={{fontSize:9,color:T.dim,fontFamily:'Orbitron,sans-serif',letterSpacing:'1px'}}>{label}</span>
        <span style={{fontSize:10,color:c,fontWeight:600}}>{Math.round(pct)}%</span>
      </div>
      <div style={{height:4,background:'rgba(0,180,255,.07)',borderRadius:2,overflow:'hidden'}}>
        <div style={{height:'100%',borderRadius:2,width:`${pct}%`,
                     background:`linear-gradient(90deg,${c}88,${c})`,boxShadow:`0 0 6px ${c}66`,
                     transition:'width .5s',position:'relative',overflow:'hidden'}}>
          <div style={{position:'absolute',inset:0,
                       background:'linear-gradient(90deg,transparent,rgba(255,255,255,.18),transparent)',
                       animation:'shimmer 2s infinite'}}/>
        </div>
      </div>
    </div>
  );
}

// ── Arc Reactor ───────────────────────────────────────────────────────────────
function ArcReactor({online}) {
  return (
    <div style={{position:'relative',width:52,height:52,flexShrink:0}}>
      {[{s:52,d:4,dash:true,c:T.blue},{s:38,d:2,c:T.cyan},{s:24,d:1.5,c:'rgba(0,180,255,.5)'}].map((r,i)=>(
        <div key={i} style={{
          position:'absolute',top:'50%',left:'50%',width:r.s,height:r.s,
          marginTop:-r.s/2,marginLeft:-r.s/2,borderRadius:'50%',
          border:`${r.d}px ${r.dash?'dashed':'solid'} ${online?r.c:'#222'}`,
          animation:online?`rot ${[4,2,1.5][i]}s linear infinite ${i===1?'reverse':''}`:undefined,
          boxShadow:online&&i===0?`0 0 8px ${T.blue}44`:undefined,
        }}/>
      ))}
      <div style={{position:'absolute',top:'50%',left:'50%',width:12,height:12,
                   marginTop:-6,marginLeft:-6,borderRadius:'50%',zIndex:2,
                   background:online?`radial-gradient(#fff,${T.cyan},${T.blue})`:'#222',
                   animation:online?'pulse 2s ease-in-out infinite':undefined}}/>
    </div>
  );
}

// ── Clock ─────────────────────────────────────────────────────────────────────
function Clock() {
  const [t,setT]=useState(new Date());
  useEffect(()=>{const id=setInterval(()=>setT(new Date()),1000);return()=>clearInterval(id);},[]);
  return (
    <div style={{textAlign:'right'}}>
      <div style={{fontFamily:'Orbitron,sans-serif',fontSize:17,fontWeight:700,color:T.blue,
                   letterSpacing:2,textShadow:`0 0 12px ${T.blue}88`}}>{t.toLocaleTimeString()}</div>
      <div style={{fontSize:9,color:T.dim,letterSpacing:1,marginTop:2}}>
        {t.toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'})}
      </div>
    </div>
  );
}

function uptime(s){const h=Math.floor(s/3600),m=Math.floor((s%3600)/60);return h?`${h}h ${m}m`:`${m}m`;}

// ── System Monitor ────────────────────────────────────────────────────────────
function SysMonitor({connected,stats}) {
  const s = stats||{};
  return (
    <Panel title="SYSTEM MONITOR" icon="📡" status={connected?'on':'off'}>
      {!connected ? (
        <div style={{textAlign:'center',padding:16,color:T.dim,fontFamily:'Orbitron,sans-serif',fontSize:9,letterSpacing:2,animation:'blink 1.5s infinite'}}>
          {agent.connected?'SCANNING...':'LAPTOP OFFLINE'}
        </div>
      ) : (
        <>
          <div style={{display:'flex',justifyContent:'space-around',marginBottom:12,paddingBottom:12,borderBottom:`1px solid ${T.border}`}}>
            {[{l:'CPU',v:s.cpu||0,c:T.blue},{l:'RAM',v:s.ram_pct||0,c:T.cyan},{l:'DISK',v:s.disk_pct||0,c:T.green},
              ...(s.battery!=null?[{l:s.plugged?'CHRG':'BATT',v:s.battery,c:T.purple}]:[])
            ].map(({l,v,c})=>{
              const r=28,circ=2*Math.PI*r,pct=Math.min(100,Math.max(0,v));
              const col=pct>90?T.red:pct>75?T.orange:c;
              return (
                <div key={l} style={{display:'flex',flexDirection:'column',alignItems:'center',gap:3}}>
                  <svg width="68" height="68" viewBox="0 0 68 68">
                    <circle cx="34" cy="34" r={r} fill="none" stroke={`${col}15`} strokeWidth="5"/>
                    <circle cx="34" cy="34" r={r} fill="none" stroke={col} strokeWidth="5"
                      strokeDasharray={circ} strokeDashoffset={circ-(pct/100)*circ}
                      strokeLinecap="round" transform="rotate(-90 34 34)"
                      style={{transition:'stroke-dashoffset .5s,stroke .5s'}}/>
                    <text x="34" y="31" textAnchor="middle" fill={col} fontSize="13" fontFamily="Orbitron" fontWeight="700">{Math.round(pct)}</text>
                    <text x="34" y="43" textAnchor="middle" fill={T.dim} fontSize="7" fontFamily="Exo 2">%</text>
                  </svg>
                  <span style={{fontFamily:'Orbitron,sans-serif',fontSize:7,color:T.dim,letterSpacing:1}}>{l}</span>
                </div>
              );
            })}
          </div>
          <Bar label={`CPU  ${s.cpu_freq||0} MHz`} value={s.cpu||0}/>
          <Bar label={`RAM  ${s.ram_used_gb||0}/${s.ram_total_gb||0} GB`} value={s.ram_pct||0} color={T.cyan}/>
          <Bar label={`DISK ${s.disk_used_gb||0}/${s.disk_total_gb||0} GB`} value={s.disk_pct||0} color={T.green}/>
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:4,marginTop:10}}>
            {[['HOST',s.hostname],['UPTIME',uptime(s.uptime||0)],['NET↑',`${s.net_up_mb||0}MB`],['NET↓',`${s.net_down_mb||0}MB`]].map(([k,v])=>(
              <div key={k} style={{background:'rgba(0,180,255,.04)',border:`1px solid ${T.border}`,padding:'4px 8px'}}>
                <div style={{fontFamily:'Orbitron,sans-serif',fontSize:7,color:T.dim,letterSpacing:1}}>{k}</div>
                <div style={{fontSize:10,marginTop:2,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{v}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </Panel>
  );
}

// ── Terminal ──────────────────────────────────────────────────────────────────
function Terminal() {
  const [inp,setInp]=useState('');
  const [log,setLog]=useState([
    {t:'sys',m:'J.A.R.V.I.S. TERMINAL v2.0 — STARK INDUSTRIES'},
    {t:'sys',m:'Type any command: open chrome · play lofi · set volume 70'},
  ]);
  const [busy,setBusy]=useState(false);
  const hist=useRef([]); const hi=useRef(-1); const end=useRef(null);
  useEffect(()=>end.current?.scrollIntoView({behavior:'smooth'}),[log]);

  const run=async()=>{
    if(!inp.trim()||busy) return;
    const cmd=inp.trim();
    hist.current.unshift(cmd); hi.current=-1;
    setLog(l=>[...l,{t:'in',m:`> ${cmd}`}]);
    setInp(''); setBusy(true);
    try {
      const r=await post('/api/command',{command:cmd});
      setLog(l=>[...l,{t:'out',m:r.result||'Done.'}]);
    } catch(e) {setLog(l=>[...l,{t:'err',m:`Error: ${e.message}`}]);}
    setBusy(false);
  };

  const onKey=e=>{
    if(e.key==='Enter'){run();return;}
    if(e.key==='ArrowUp'){hi.current=Math.min(hi.current+1,hist.current.length-1);setInp(hist.current[hi.current]||'');}
    if(e.key==='ArrowDown'){hi.current=Math.max(hi.current-1,-1);setInp(hist.current[hi.current]||'');}
  };

  return (
    <Panel title="COMMAND TERMINAL" icon="⌨️">
      <div style={{height:190,overflowY:'auto',fontFamily:'Courier New,monospace',fontSize:11,lineHeight:1.7,marginBottom:8}}>
        {log.map((e,i)=><div key={i} style={{color:{sys:T.dim,in:T.blue,out:T.green,err:T.red}[e.t]||T.text}}>{e.m}</div>)}
        {busy&&<div style={{color:T.dim}}>Processing<span style={{animation:'blink .8s infinite',display:'inline-block'}}>_</span></div>}
        <div ref={end}/>
      </div>
      <div style={{display:'flex',gap:6,alignItems:'center'}}>
        <span style={{fontFamily:'Orbitron,sans-serif',fontSize:8,color:T.orange,letterSpacing:1}}>STARK://</span>
        <In value={inp} onChange={setInp} onEnter={run} placeholder="Enter command..."
          style={{flex:1,fontFamily:'Courier New,monospace',fontSize:11}}/>
        <Btn onClick={run} small>EXEC</Btn>
      </div>
    </Panel>
  );
}

// ── Screenshot ────────────────────────────────────────────────────────────────
function ScreenViewer() {
  const [src,setSrc]=useState(null); const [auto,setAuto]=useState(false); const iv=useRef(null);
  const cap=useCallback(()=>setSrc(`${API}/api/screenshot?t=${Date.now()}`), []);
  useEffect(()=>{
    if(auto){cap();iv.current=setInterval(cap,10000);}
    else clearInterval(iv.current);
    return()=>clearInterval(iv.current);
  },[auto,cap]);
  return (
    <Panel title="SCREEN VIEWER" icon="🖥️">
      <div style={{display:'flex',gap:6,marginBottom:8}}>
        <Btn onClick={cap} small>📸 CAPTURE</Btn>
        <Btn onClick={()=>setAuto(a=>!a)} active={auto} small>{auto?'⏹ STOP':'▶ AUTO 10s'}</Btn>
      </div>
      <div style={{border:`1px solid ${T.border}`,background:'rgba(0,0,0,.4)',minHeight:130,display:'flex',alignItems:'center',justifyContent:'center',overflow:'hidden'}}>
        {src?<img src={src} alt="screen" style={{width:'100%',height:'auto',display:'block'}} onError={()=>setSrc(null)}/>
            :<div style={{textAlign:'center',opacity:.3}}><div style={{fontSize:32}}>🖥️</div><div style={{fontFamily:'Orbitron,sans-serif',fontSize:9,letterSpacing:2,marginTop:6}}>AWAITING CAPTURE</div></div>}
      </div>
    </Panel>
  );
}

// ── Process Manager ───────────────────────────────────────────────────────────
function ProcessManager() {
  const [procs,setProcs]=useState([]); const [filt,setFilt]=useState(''); const [busy,setBusy]=useState(false);
  const load=async()=>{setBusy(true);try{setProcs(await api('/api/processes'));}catch{}setBusy(false);};
  const kill=async(pid,name)=>{if(!window.confirm(`Kill ${name} (${pid})?`))return;await api(`/api/kill`,{method:'POST',headers:H,body:JSON.stringify({identifier:String(pid)})});load();};
  useEffect(()=>{load();},[]);
  const shown=procs.filter(p=>!filt||p.name.toLowerCase().includes(filt.toLowerCase()));
  return (
    <Panel title="PROCESS MANAGER" icon="⚙️">
      <div style={{display:'flex',gap:6,marginBottom:8}}>
        <In value={filt} onChange={setFilt} placeholder="Filter..." style={{flex:1}}/>
        <Btn onClick={load} small>{busy?'...':'↺'}</Btn>
      </div>
      <div style={{maxHeight:220,overflowY:'auto'}}>
        <table style={{width:'100%',borderCollapse:'collapse',fontSize:10}}>
          <thead>
            <tr>{['PID','NAME','CPU%','RAM%','ST',''].map(h=><th key={h} style={{fontFamily:'Orbitron,sans-serif',fontSize:7,color:T.dim,padding:'3px 4px',textAlign:'left',borderBottom:`1px solid ${T.border}`,background:T.bg2,position:'sticky',top:0}}>{h}</th>)}</tr>
          </thead>
          <tbody>
            {shown.slice(0,40).map(p=>(
              <tr key={p.pid}
                onMouseEnter={e=>e.currentTarget.style.background='rgba(0,180,255,.04)'}
                onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
                <td style={{padding:'2px 4px',color:T.dim,fontFamily:'monospace'}}>{p.pid}</td>
                <td style={{padding:'2px 4px',maxWidth:110,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{p.name}</td>
                <td style={{padding:'2px 4px',color:p.cpu>50?T.red:p.cpu>20?T.orange:T.text,fontWeight:p.cpu>20?600:400}}>{p.cpu.toFixed(1)}</td>
                <td style={{padding:'2px 4px'}}>{p.ram.toFixed(1)}</td>
                <td style={{padding:'2px 4px'}}><span style={{fontSize:7,padding:'1px 3px',fontFamily:'Orbitron,sans-serif',color:p.status==='running'?T.green:T.dim,border:`1px solid ${p.status==='running'?'rgba(0,230,118,.2)':T.border}`}}>{p.status?.slice(0,4)}</span></td>
                <td style={{padding:'2px 4px'}}><button onClick={()=>kill(p.pid,p.name)} style={{background:'transparent',border:`1px solid rgba(255,107,53,.3)`,color:T.orange,fontSize:9,padding:'1px 5px',cursor:'pointer'}} onMouseEnter={e=>e.target.style.background='rgba(255,107,53,.1)'} onMouseLeave={e=>e.target.style.background='transparent'}>✕</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

// ── File Explorer ─────────────────────────────────────────────────────────────
function FileExplorer() {
  const [items,setItems]=useState([]); const [path,setPath]=useState('~'); const [inp,setInp]=useState('~');
  const nav=async p=>{try{const r=await api(`/api/files?path=${encodeURIComponent(p)}`);setItems(r);setPath(p);setInp(p);}catch{}};
  const up=()=>{const pts=path.replace('~','').split('/').filter(Boolean);pts.pop();nav(pts.length?'/'+pts.join('/'):'~');};
  useEffect(()=>{nav('~');},[]);
  return (
    <Panel title="FILE EXPLORER" icon="📁">
      <div style={{display:'flex',gap:4,marginBottom:8,alignItems:'center'}}>
        <Btn onClick={up} small>↑</Btn>
        <In value={inp} onChange={setInp} onEnter={()=>nav(inp)} style={{flex:1,fontSize:10}}/>
        <Btn onClick={()=>nav(inp)} small>GO</Btn>
      </div>
      <div style={{maxHeight:190,overflowY:'auto',display:'flex',flexDirection:'column',gap:1}}>
        {items.map((f,i)=>(
          <div key={i} onClick={()=>f.is_dir&&nav(f.path)}
            style={{display:'flex',alignItems:'center',gap:6,padding:'3px 5px',cursor:f.is_dir?'pointer':'default',transition:'background .1s'}}
            onMouseEnter={e=>e.currentTarget.style.background='rgba(0,180,255,.05)'}
            onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
            <span style={{fontSize:11}}>{f.is_dir?'📂':'📄'}</span>
            <span style={{flex:1,fontSize:10,color:f.is_dir?T.blue:T.text,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{f.name}</span>
            <span style={{fontSize:9,color:T.dim}}>{f.size_str}</span>
            {!f.is_dir&&<a href={`${API}/api/download?path=${encodeURIComponent(f.path)}`} download={f.name} onClick={e=>e.stopPropagation()} style={{color:T.blue,fontSize:9,textDecoration:'none'}}>↓</a>}
          </div>
        ))}
      </div>
    </Panel>
  );
}

// ── YouTube DJ ────────────────────────────────────────────────────────────────
function YouTubeDJ() {
  const [q,setQ]=useState(''); const [res,setRes]=useState([]); const [now,setNow]=useState(null);
  const [busy,setBusy]=useState(false); const [fb,setFb]=useState('');
  const flash=m=>{setFb(m);setTimeout(()=>setFb(''),3000);};
  const search=async()=>{if(!q.trim())return;setBusy(true);setRes([]);try{const r=await api(`/api/youtube/search?q=${encodeURIComponent(q)}&limit=5`);setRes(r.results||[]);}catch{}setBusy(false);};
  const play=async(id,title)=>{const url=`https://www.youtube.com/watch?v=${id}`;await post('/api/command',{command:`youtube_play ${url} ${title}`});setNow({title});setRes([]);flash(`▶️ ${title}`);};
  const ctrl=async a=>{const r=await api(`/api/command`,{method:'POST',headers:H,body:JSON.stringify({command:a})});flash(r.result||'✓');};
  return (
    <Panel title="YOUTUBE DJ" icon="🎵" status={now?'on':'warn'}>
      {now?.title&&<div style={{background:'rgba(0,180,255,.05)',border:`1px solid ${T.border}`,padding:'6px 10px',marginBottom:10,animation:'fadeUp .3s'}}>
        <div style={{fontFamily:'Orbitron,sans-serif',fontSize:7,color:T.dim,letterSpacing:1,marginBottom:2}}>NOW PLAYING</div>
        <div style={{fontSize:10,color:T.blue,fontWeight:600,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{now.title}</div>
      </div>}
      <div style={{display:'flex',gap:4,flexWrap:'wrap',marginBottom:10}}>
        {[['⏯','pause'],['⏪','skip back'],['⏩','skip forward'],['🔲','fullscreen'],['🔇','yt mute'],['⏭','next video']].map(([lbl,cmd])=>(
          <Btn key={cmd} onClick={()=>ctrl(cmd)} small style={{flex:1,minWidth:28,textAlign:'center'}}>{lbl}</Btn>
        ))}
      </div>
      <div style={{display:'flex',gap:6,marginBottom:8}}>
        <In value={q} onChange={setQ} onEnter={search} placeholder="Search YouTube..." style={{flex:1}}/>
        <Btn onClick={search} small>{busy?'...':'🔍'}</Btn>
      </div>
      <div style={{maxHeight:170,overflowY:'auto',display:'flex',flexDirection:'column',gap:2}}>
        {res.map(v=>(
          <div key={v.id} onClick={()=>play(v.id,v.title)}
            style={{display:'flex',gap:8,alignItems:'center',padding:'4px 5px',cursor:'pointer',transition:'background .1s'}}
            onMouseEnter={e=>e.currentTarget.style.background='rgba(0,180,255,.06)'}
            onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
            <img src={v.thumb} alt="" style={{width:50,height:36,objectFit:'cover',flexShrink:0,border:`1px solid ${T.border}`}}/>
            <div style={{flex:1,minWidth:0}}>
              <div style={{fontSize:10,fontWeight:500,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{v.title}</div>
              <div style={{fontSize:8,color:T.dim,marginTop:1}}>{v.channel} · {v.duration}</div>
            </div>
            <Btn small>▶</Btn>
          </div>
        ))}
      </div>
      {fb&&<div style={{marginTop:6,padding:'4px 8px',background:'rgba(0,230,118,.06)',borderLeft:`2px solid ${T.green}`,fontSize:10,color:T.green,animation:'fadeUp .2s'}}>{fb}</div>}
    </Panel>
  );
}

// ── Quick Actions ─────────────────────────────────────────────────────────────
function QuickActions() {
  const [vol,setVol]=useState(65); const [fb,setFb]=useState('');
  const flash=m=>{setFb(m);setTimeout(()=>setFb(''),3000);};
  const run=async(cmd,lbl)=>{flash(`${lbl}...`);try{const r=await post('/api/command',{command:cmd});flash(r.result||lbl);}catch(e){flash(`❌ ${e.message}`);}};
  const ACTS=[['🔒','LOCK','lock screen',false],['📸','CAPTURE','screenshot',false],['😴','SLEEP','sleep',false],['🔇','MUTE','mute',false],['🌟','BRIGHT+','set brightness 80',false],['🌑','BRIGHT-','set brightness 30',false],['🔄','RESTART','restart',true],['⛔','SHUTDOWN','shutdown in 5 minutes',true]];
  return (
    <Panel title="QUICK ACTIONS" icon="⚡">
      <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:5,marginBottom:10}}>
        {ACTS.map(([icon,label,cmd,danger])=>(
          <button key={label} onClick={()=>run(cmd,label)}
            style={{background:'rgba(0,180,255,.04)',border:`1px solid ${danger?'rgba(255,107,53,.25)':T.border}`,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:3,padding:'9px 4px',cursor:'pointer',transition:'all .15s'}}
            onMouseEnter={e=>{e.currentTarget.style.background=`rgba(${danger?'255,107,53':'0,180,255'},.1)`;e.currentTarget.style.transform='translateY(-1px)';}}
            onMouseLeave={e=>{e.currentTarget.style.background='rgba(0,180,255,.04)';e.currentTarget.style.transform='none';}}>
            <span style={{fontSize:15}}>{icon}</span>
            <span style={{fontFamily:'Orbitron,sans-serif',fontSize:6.5,letterSpacing:1,color:danger?T.orange:T.dim}}>{label}</span>
          </button>
        ))}
      </div>
      <div style={{display:'flex',alignItems:'center',gap:8,padding:'5px 0',borderTop:`1px solid ${T.border}`}}>
        <span style={{fontFamily:'Orbitron,sans-serif',fontSize:7,color:T.dim,letterSpacing:1}}>VOL</span>
        <input type="range" min="0" max="100" value={vol} onChange={e=>setVol(+e.target.value)}
          onMouseUp={()=>run(`set volume ${vol}`,`VOL ${vol}%`)}
          style={{flex:1,accentColor:T.blue,cursor:'pointer'}}/>
        <span style={{fontSize:10,color:T.blue,minWidth:28}}>{vol}%</span>
      </div>
      {fb&&<div style={{marginTop:6,padding:'4px 8px',background:'rgba(0,230,118,.06)',borderLeft:`2px solid ${T.green}`,fontSize:10,color:T.green,animation:'fadeUp .2s'}}>{fb}</div>}
    </Panel>
  );
}

// ── Command Log ───────────────────────────────────────────────────────────────
function CmdLog({entries}) {
  const end=useRef(null);
  useEffect(()=>end.current?.scrollIntoView({behavior:'smooth'}),[entries]);
  return (
    <Panel title="COMMAND LOG" icon="📜">
      <div style={{maxHeight:95,overflowY:'auto',display:'flex',flexDirection:'column',gap:2}}>
        {!entries.length&&<div style={{color:T.dim,fontSize:10,fontStyle:'italic'}}>Awaiting transmissions...</div>}
        {entries.map((e,i)=>(
          <div key={i} style={{display:'flex',gap:8,fontSize:9,padding:'2px 0',borderBottom:`1px solid rgba(0,180,255,.04)`}}>
            <span style={{color:T.dim,fontFamily:'Orbitron,sans-serif',fontSize:7,letterSpacing:1,whiteSpace:'nowrap'}}>{e.t}</span>
            <span style={{color:{telegram:T.cyan,api:T.blue,dashboard:T.text}[e.src]||T.text,fontWeight:600,whiteSpace:'nowrap'}}>{e.src}</span>
            <span style={{color:T.text,flex:1,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{e.cmd}</span>
          </div>
        ))}
        <div ref={end}/>
      </div>
    </Panel>
  );
}

// ── Root App ──────────────────────────────────────────────────────────────────
const agent = { connected: false }; // ref for use in SysMonitor closure

export default function App() {
  const {data: ws} = useWS('/ws/stats');
  const [logEntries, setLogEntries] = useState([]);

  const connected = ws?.connected || false;
  const stats     = ws?.laptop || {};
  agent.connected = connected;

  // Poll command log
  useEffect(()=>{
    const load=()=>api('/api/log').then(setLogEntries).catch(()=>{});
    load();
    const t=setInterval(load,5000);
    return()=>clearInterval(t);
  },[]);

  return (
    <>
      <style>{CSS}</style>
      {/* Scan line */}
      <div style={{position:'fixed',top:-3,left:0,right:0,height:2,zIndex:1000,pointerEvents:'none',
        background:`linear-gradient(90deg,transparent,${T.blue},${T.cyan},transparent)`,
        boxShadow:`0 0 8px ${T.blue}`,animation:'scan 6s linear infinite'}}/>
      {/* Grid bg */}
      <div style={{position:'fixed',inset:0,zIndex:0,pointerEvents:'none',
        backgroundImage:`linear-gradient(rgba(0,180,255,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(0,180,255,.03) 1px,transparent 1px)`,
        backgroundSize:'36px 36px'}}/>

      <div style={{position:'relative',zIndex:1,height:'100vh',display:'flex',flexDirection:'column'}}>
        {/* Header */}
        <header style={{display:'flex',alignItems:'center',justifyContent:'space-between',
                        padding:'8px 16px',borderBottom:`1px solid ${T.border}`,
                        background:'rgba(2,12,27,.97)',backdropFilter:'blur(10px)',flexShrink:0}}>
          <div style={{display:'flex',alignItems:'center',gap:12}}>
            <ArcReactor online={connected}/>
            <div>
              <div style={{fontFamily:'Orbitron,sans-serif',fontSize:14,fontWeight:700,color:T.blue,letterSpacing:3,textShadow:`0 0 12px ${T.blue}66`}}>J.A.R.V.I.S.</div>
              <div style={{fontSize:8,color:T.dim,letterSpacing:2,marginTop:1}}>MARK IV · STARK INDUSTRIES</div>
            </div>
          </div>
          <div style={{textAlign:'center',flex:1}}>
            <div style={{fontFamily:'Orbitron,sans-serif',fontSize:9,color:T.dim,letterSpacing:3}}>PERSONAL DEFENSE ARRAY</div>
            <div style={{fontSize:10,color:T.dim,marginTop:3}}>
              LAPTOP: <span style={{color:connected?T.green:T.red,fontWeight:600}}>{connected?'● ONLINE':'○ OFFLINE'}</span>
              {stats.cpu!=null&&<span style={{marginLeft:12}}>CPU: <span style={{color:T.blue}}>{stats.cpu}%</span> RAM: <span style={{color:T.cyan}}>{stats.ram_pct}%</span></span>}
            </div>
          </div>
          <Clock/>
        </header>

        {/* 4-column grid */}
        <main style={{flex:1,display:'grid',gridTemplateColumns:'265px 1fr 275px 265px',
                      gap:6,padding:6,overflow:'hidden',minHeight:0}}>
          <div style={{display:'flex',flexDirection:'column',gap:6,overflow:'hidden'}}>
            <SysMonitor connected={connected} stats={stats}/>
            <QuickActions/>
            <CmdLog entries={logEntries}/>
          </div>
          <div style={{display:'flex',flexDirection:'column',gap:6,overflow:'hidden'}}>
            <Terminal/>
            <ScreenViewer/>
            <YouTubeDJ/>
          </div>
          <div style={{display:'flex',flexDirection:'column',gap:6,overflow:'hidden'}}>
            <ProcessManager/>
            <FileExplorer/>
          </div>
          <div style={{display:'flex',flexDirection:'column',gap:6,overflow:'hidden'}}>
            {/* Iron Hand info panel */}
            <Panel title="IRON HAND — GYRO MOUSE" icon="🤚" status={connected?'on':'off'}>
              <div style={{background:'rgba(0,180,255,.04)',border:`1px solid ${T.border}`,padding:'10px',marginBottom:10,textAlign:'center'}}>
                <div style={{fontFamily:'Orbitron,sans-serif',fontSize:9,color:T.blue,letterSpacing:1,marginBottom:6}}>OPEN ON PHONE</div>
                <div style={{fontSize:11,color:T.text,wordBreak:'break-all',fontWeight:500}}>{API}/ironhand</div>
                <div style={{fontSize:9,color:T.dim,marginTop:6}}>Tilt = cursor · Tap = click · Shake = scroll</div>
              </div>
              <div style={{display:'flex',gap:5,marginBottom:8}}>
                <Btn onClick={()=>post('/api/command',{command:'iron hand on'})} style={{flex:1,textAlign:'center'}}>⚡ ENABLE</Btn>
                <Btn onClick={()=>post('/api/command',{command:'iron hand off'})} danger style={{flex:1,textAlign:'center'}}>⏹ DISABLE</Btn>
              </div>
              <div style={{fontSize:9,color:T.dim,textAlign:'center',padding:'4px'}}>Iron Hand page is served from your Railway URL — works from anywhere in the world</div>
            </Panel>
            {/* Status summary */}
            <Panel title="CONNECTION STATUS" icon="🔗">
              <div style={{display:'flex',flexDirection:'column',gap:8}}>
                {[
                  {label:'Railway Backend',color:T.green,status:'ONLINE'},
                  {label:'Telegram Bot',color:T.green,status:'ONLINE'},
                  {label:'Laptop Agent',color:connected?T.green:T.red,status:connected?'ONLINE':'OFFLINE'},
                  {label:'Iron Hand',color:T.dim,status:'STANDBY'},
                ].map(({label,color,status})=>(
                  <div key={label} style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'5px 8px',background:'rgba(0,180,255,.04)',border:`1px solid ${T.border}`}}>
                    <span style={{fontSize:10}}>{label}</span>
                    <span style={{fontFamily:'Orbitron,sans-serif',fontSize:8,color,letterSpacing:1}}>{status}</span>
                  </div>
                ))}
              </div>
              {!connected&&<div style={{marginTop:10,padding:'8px',background:'rgba(255,107,53,.06)',border:`1px solid rgba(255,107,53,.2)`,fontSize:9,color:T.orange,textAlign:'center'}}>
                Run <strong>agent/run.bat</strong> on your laptop to connect
              </div>}
            </Panel>
          </div>
        </main>

        <footer style={{display:'flex',justifyContent:'space-between',alignItems:'center',
                        padding:'4px 16px',borderTop:`1px solid ${T.border}`,
                        background:'rgba(2,12,27,.95)',flexShrink:0,
                        fontFamily:'Orbitron,sans-serif',fontSize:7,letterSpacing:1,color:T.dim}}>
          <span>J.A.R.V.I.S. v2.0 — MARK IV</span>
          <span>{stats.hostname?`${stats.hostname} · ${stats.os}`:'LAPTOP OFFLINE'}</span>
          <span>STARK INDUSTRIES</span>
        </footer>
      </div>
    </>
  );
}
