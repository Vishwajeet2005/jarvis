PHONE_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
<title>JARVIS Iron Hand</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#020c1b;color:#b8d8f0;font-family:'Courier New',monospace;display:flex;
     flex-direction:column;align-items:center;justify-content:center;min-height:100vh;
     padding:24px;text-align:center;-webkit-tap-highlight-color:transparent}
h1{font-size:22px;color:#00b4ff;letter-spacing:4px;margin-bottom:4px}
.sub{font-size:10px;color:#4a7a9b;letter-spacing:3px;margin-bottom:20px}
.arc{width:70px;height:70px;position:relative;margin:0 auto 16px}
.ring{position:absolute;border-radius:50%;border:1.5px solid #00b4ff;inset:0}
.r1{animation:rot 4s linear infinite;border-style:dashed}
.r2{inset:12px;animation:rot 2s linear infinite reverse;border-color:#00e5ff}
.r3{inset:24px;animation:rot 1.5s linear infinite;opacity:.5}
.dot{width:14px;height:14px;border-radius:50%;background:radial-gradient(#fff,#00e5ff,#00b4ff);
     position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);animation:pulse 2s ease-in-out infinite}
@keyframes rot{to{transform:rotate(360deg)}}
@keyframes pulse{0%,100%{box-shadow:0 0 8px #00e5ff}50%{box-shadow:0 0 24px #00e5ff,0 0 48px rgba(0,229,255,.3)}}
.badge{font-size:12px;padding:7px 18px;border:1px solid rgba(0,180,255,.2);
       background:rgba(0,180,255,.05);margin-bottom:12px;letter-spacing:1px}
.on{color:#00e676}.off{color:#ff3333}
.btn{display:block;width:100%;max-width:300px;margin:5px auto;padding:14px;
     background:transparent;border:1px solid #00b4ff;color:#00b4ff;
     font-family:'Courier New',monospace;font-size:12px;letter-spacing:2px;
     cursor:pointer;transition:all .15s;text-transform:uppercase;-webkit-appearance:none}
.btn:active{background:rgba(0,180,255,.15);transform:scale(.98)}
.btn.red{border-color:#ff6b35;color:#ff6b35}
.btn.grn{border-color:#00e676;color:#00e676}
.row{display:flex;gap:8px;max-width:300px;margin:5px auto;width:100%}
.row .btn{margin:0}
.sens{display:flex;align-items:center;gap:10px;max-width:300px;margin:10px auto;width:100%}
.sens label{font-size:10px;color:#4a7a9b;letter-spacing:1px;white-space:nowrap}
input[type=range]{flex:1;accent-color:#00b4ff;height:4px}
.val{font-size:11px;color:#00b4ff;min-width:24px;text-align:right}
#data{font-size:9px;color:#4a7a9b;margin-top:16px;letter-spacing:1px;height:14px}
</style>
</head>
<body>
<div class="arc">
  <div class="ring r1"></div><div class="ring r2"></div><div class="ring r3"></div>
  <div class="dot"></div>
</div>
<h1>IRON HAND</h1>
<div class="sub">GYROSCOPE CURSOR CONTROL</div>
<div class="badge" id="ws-st">⚡ <span class="off">CONNECTING...</span></div>
<div class="badge">🤚 <span id="hs" class="off">INACTIVE</span></div>

<button class="btn grn" onclick="send({type:'toggle'})">⚡ TOGGLE ACTIVE</button>
<button class="btn" onclick="send({type:'calibrate'})">🎯 CALIBRATE (hold naturally)</button>
<div class="row">
  <button class="btn" onclick="g('tap')">🖱 CLICK</button>
  <button class="btn" onclick="g('doubletap')">🖱🖱 DOUBLE</button>
</div>
<button class="btn red" onclick="g('longtap')">🖱 RIGHT CLICK</button>
<button class="btn" onclick="g('shake')">📜 SCROLL DOWN</button>

<div class="sens">
  <label>SENSITIVITY</label>
  <input type="range" min="1" max="20" value="8" id="sens"
    oninput="document.getElementById('sv').textContent=this.value;
             send({type:'setting',key:'sensitivity',value:+this.value})">
  <span class="val" id="sv">8</span>
</div>
<div id="data">Tilt to move cursor — tap buttons to click</div>

<script>
let ws, enabled=false;
const H=location.host, P=location.protocol==='https:'?'wss':'ws';

function connect(){
  ws=new WebSocket(`${P}://${H}/ws/ironhand`);
  ws.onopen=()=>{ document.getElementById('ws-st').innerHTML='⚡ <span class="on">CONNECTED</span>'; reqMot(); };
  ws.onclose=()=>{ document.getElementById('ws-st').innerHTML='⚡ <span class="off">RECONNECTING...</span>'; setTimeout(connect,3000); };
  ws.onmessage=e=>{
    try{
      const d=JSON.parse(e.data);
      if(d.enabled!==undefined){
        enabled=d.enabled;
        const el=document.getElementById('hs');
        el.textContent=enabled?'ACTIVE ⚡':'INACTIVE';
        el.className=enabled?'on':'off';
      }
    }catch(e){}
  };
}
function send(d){if(ws&&ws.readyState===1)ws.send(JSON.stringify(d));}
function g(t){send({type:'gesture',gesture:t});}

function reqMot(){
  if(typeof DeviceMotionEvent!=='undefined'&&typeof DeviceMotionEvent.requestPermission==='function'){
    DeviceMotionEvent.requestPermission().then(p=>{if(p==='granted')attach();}).catch(attach);
  }else{attach();}
}
function attach(){
  window.addEventListener('deviceorientation',e=>{
    send({type:'motion',beta:e.beta,gamma:e.gamma});
    if(enabled)document.getElementById('data').textContent=`β:${e.beta?.toFixed(1)}°  γ:${e.gamma?.toFixed(1)}°`;
  },{passive:true});
}
connect();
</script>
</body>
</html>"""
