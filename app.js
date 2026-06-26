/* LyricForge Studio: canvas lyric video creator. Export algorithm intentionally mirrors the original MediaRecorder/canvas capture flow. */
const W = 1920, H = 1080;
const $ = id => document.getElementById(id);
const canvas = $('preview');
const ctx = canvas.getContext('2d', { alpha: false });
const audio = $('audioEl');

const state = { lyrics: [], bg: null, bgType: null, overlays: [], selectedLayer: null, particles: [], prevLineIdx: -1, lineEnterTime: 0, lineLeaveTime: 0, lineLeaving: false, lineAlpha: 1, lineScale: 1, currentLineText: '', customFontName: null, isRecording: false, mediaRecorder: null, recordedChunks: [], lastFrame: performance.now(), fpsFrames: 0, fpsTime: performance.now(), fps: 60, audioCtx: null, analyser: null, freq: null, time: null, sourceNode: null, audioLevel: 0, beat: 0 };
let mediaRecorder = null, recordedChunks = [], isRecording = false;
let particles = state.particles;
let lyrics = state.lyrics;
let bgImage = null;
let prevLineIdx = -1;

function val(id){ const el=$(id); return el?.type === 'checkbox' ? el.checked : el?.value; }
function num(id){ return +val(id); }
function clamp(v,a,b){ return Math.max(a, Math.min(b, v)); }
function easeOut(t){ return 1 - Math.pow(1 - clamp(t,0,1), 3); }
function easeInOut(t){ t=clamp(t,0,1); return t < .5 ? 4*t*t*t : 1 - Math.pow(-2*t+2,3)/2; }
function hexToRgb(hex){ const h=hex.replace('#',''); return [parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)]; }
function rgba(hex,a){ const [r,g,b]=hexToRgb(hex); return `rgba(${r},${g},${b},${a})`; }
function fmt(t){ if(!isFinite(t)) return '00:00'; const m=Math.floor(t/60), s=Math.floor(t%60); return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`; }
function showToast(msg){ const h=$('hint'); h.innerHTML=msg; h.classList.add('show'); clearTimeout(showToast._t); showToast._t=setTimeout(()=>h.classList.remove('show'),2800); }

function parseLRC(text){
  const lines = text.split(/\r?\n/), out = [], re = /\[(\d{1,2}):(\d{1,2})(?:\.(\d{1,3}))?\]/g;
  for(const raw of lines){
    let m, timestamps=[];
    while((m = re.exec(raw)) !== null){
      const min=parseInt(m[1]), sec=parseInt(m[2]); let ms=parseInt(m[3]||0);
      if(m[3] && m[3].length===2) ms*=10; if(m[3] && m[3].length===1) ms*=100;
      timestamps.push(min*60 + sec + ms/1000);
    }
    const content = raw.replace(re,'').trim();
    if(content && timestamps.length) for(const t of timestamps) out.push({time:t,text:content});
  }
  return out.sort((a,b)=>a.time-b.time);
}

function setupTabs(){ document.querySelectorAll('.tab').forEach(btn=>btn.addEventListener('click',()=>{ document.querySelectorAll('.tab,.tab-panel').forEach(x=>x.classList.remove('active')); btn.classList.add('active'); $(`tab-${btn.dataset.tab}`).classList.add('active'); })); }
function bindRange(id,suffix=''){ const el=$(id), out=$(`${id}Val`); if(!el||!out) return; const upd=()=>out.textContent=el.value+suffix; el.addEventListener('input',()=>{ upd(); if(id==='pCount') initParticles(); updateSelectedFromControls(id); }); upd(); }
['bgBlur','bgDim','bgZoom','fontSize','strokeWidth','textGlow','maxWidth','lineSpace','vertPos','popScale','pCount','pSpeed','pSize','pOp','visPower','layerX','layerY','layerSize','layerOpacity','layerRotate'].forEach(id=>bindRange(id, ['maxWidth','vertPos','layerX','layerY','layerSize'].includes(id)?'%':''));

function setupFileBtn(inputId,labelId,cb){ const inp=$(inputId), lab=$(labelId); lab.addEventListener('click',e=>{e.preventDefault(); inp.click();}); inp.addEventListener('change',e=>{ const files=[...e.target.files]; if(files.length){ cb(inputId==='overlayInput'?files:files[0]); lab.classList.add('active'); lab.textContent = inputId==='overlayInput' ? `✓ ${files.length} overlay(s) added` : `✓ ${files[0].name}`; updateStatus(); }}); }
setupFileBtn('lrcInput','lrcLabel', file=>{ const r=new FileReader(); r.onload=e=>{ state.lyrics=parseLRC(e.target.result); lyrics=state.lyrics; $('manualLyrics').value=e.target.result; state.prevLineIdx=-1; prevLineIdx=-1; updateStatus(); }; r.readAsText(file); });
setupFileBtn('audioInput','audioLabel', file=>{ audio.src=URL.createObjectURL(file); audio.load(); });
setupFileBtn('bgInput','bgLabel', setBackgroundFile);
setupFileBtn('fontInput','fontLabel', file=>{ const r=new FileReader(); r.onload=async e=>{ state.customFontName='CustomFont'+Date.now(); const f=new FontFace(state.customFontName,e.target.result); await f.load(); document.fonts.add(f); $('fontFamily').value='__custom'; $('fontLabel').textContent='✓ '+file.name; }; r.readAsArrayBuffer(file); });
setupFileBtn('overlayInput','overlayLabel', addOverlayFiles);

function setBackgroundFile(file){ if(state.bg?.url) URL.revokeObjectURL(state.bg.url); const url=URL.createObjectURL(file); const isVideo=file.type.startsWith('video/'); const isGif=file.type==='image/gif' || file.name.toLowerCase().endsWith('.gif'); if(isVideo||isGif){ const video=document.createElement('video'); video.src=url; video.loop=true; video.muted=true; video.playsInline=true; video.play().catch(()=>{}); state.bg={el:video,url,fileName:file.name}; state.bgType='video'; bgImage=video; } else { const img=new Image(); img.onload=()=>{}; img.src=url; state.bg={el:img,url,fileName:file.name}; state.bgType='image'; bgImage=img; } updateStatus(); }
function addOverlayFiles(files){ files.forEach(file=>{ const url=URL.createObjectURL(file); const video=file.type.startsWith('video/') || file.type==='image/gif' || file.name.toLowerCase().endsWith('.gif'); const el=video?document.createElement('video'):new Image(); if(video){ el.src=url; el.loop=true; el.muted=true; el.playsInline=true; el.play().catch(()=>{}); } else el.src=url; state.overlays.push({id:crypto.randomUUID(),type:video?'video':'image',name:file.name,el,url,x:50,y:50,size:30,opacity:1,rotate:0,blend:'source-over',visible:true}); }); selectLayer(state.overlays.at(-1)?.id); renderOverlayList(); }
$('addTextOverlay').addEventListener('click',()=>{ const layer={id:crypto.randomUUID(),type:'text',name:'Text overlay',text:'NEW TEXT',x:50,y:20,size:18,opacity:1,rotate:0,blend:'source-over',visible:true}; state.overlays.push(layer); selectLayer(layer.id); renderOverlayList(); });

function updateStatus(){ const p=[]; if(state.lyrics.length)p.push(`📝 ${state.lyrics.length} lines`); if(audio.src)p.push('🎵 Audio'); if(state.bg)p.push(`🌌 ${state.bg.fileName}`); if(state.overlays.length)p.push(`🧩 ${state.overlays.length} overlays`); $('mediaStatus').textContent=p.length?p.join(' · '):'No files loaded'; $('emptyState').style.display=(state.bg||audio.src||state.lyrics.length)?'none':'grid'; }
$('applyLyricsBtn').addEventListener('click',()=>{ state.lyrics=parseLRC($('manualLyrics').value); lyrics=state.lyrics; state.prevLineIdx=-1; prevLineIdx=-1; updateStatus(); showToast(`Applied ${state.lyrics.length} lyric lines`); });
$('clearLyrics').addEventListener('click',()=>{ state.lyrics=[]; lyrics=state.lyrics; $('manualLyrics').value=''; updateStatus(); });
$('nudgeBack').addEventListener('click',()=>{ $('lyricOffset').value=num('lyricOffset')-100; showToast('Lyrics nudged -100ms'); });
$('nudgeForward').addEventListener('click',()=>{ $('lyricOffset').value=num('lyricOffset')+100; showToast('Lyrics nudged +100ms'); });
$('fontFamily').addEventListener('change',()=>{ if(val('fontFamily')==='__custom'&&!state.customFontName) $('fontLabel').click(); });

function initParticles(){ state.particles=[]; particles=state.particles; for(let i=0;i<num('pCount');i++) particles.push({x:Math.random()*W,y:Math.random()*H,vx:(Math.random()-.5)*.8,vy:.25+Math.random()*1.4,s:.45+Math.random()*1.9,a:.25+Math.random()*.75,tw:Math.random()*Math.PI*2,h:Math.random()*360}); }
initParticles();
function setupAudioGraph(){ /* Keep export audio capture pristine: do not create a MediaElementSource before export. */ }
function updateAudioLevel(){ const playing = audio.src && !audio.paused; const pulse = playing ? (0.5 + 0.5 * Math.sin(audio.currentTime * 7.2)) : 0.15; const slow = playing ? (0.5 + 0.5 * Math.sin(audio.currentTime * 1.7)) : 0.05; state.audioLevel = playing ? 0.18 + slow * 0.34 : 0.08; state.beat = playing ? Math.pow(pulse, 5) * 0.85 : 0.05; if(!state.freq) state.freq = new Uint8Array(256); for(let i=0;i<state.freq.length;i++) state.freq[i] = Math.floor(255 * (0.18 + state.audioLevel * Math.abs(Math.sin(audio.currentTime * 2 + i * 0.17)))); }

function drawCover(el, fit='cover', zoom=1){ const iw=el.videoWidth||el.naturalWidth||el.width||W, ih=el.videoHeight||el.naturalHeight||el.height||H; if(!iw||!ih) return; let dw=W,dh=H,dx=0,dy=0; const ir=iw/ih, cr=W/H; if(fit==='contain'){ if(ir>cr){dw=W;dh=W/ir;dy=(H-dh)/2}else{dh=H;dw=H*ir;dx=(W-dw)/2} } else if(fit==='cover'){ if(ir>cr){dh=H;dw=H*ir;dx=(W-dw)/2}else{dw=W;dh=W/ir;dy=(H-dh)/2} } dw*=zoom; dh*=zoom; dx=(W-dw)/2; dy=(H-dh)/2; ctx.drawImage(el,dx,dy,dw,dh); }
function drawBackground(now){ ctx.save(); ctx.fillStyle='#03040a'; ctx.fillRect(0,0,W,H); const beatZoom=val('audioReactiveBg') ? state.beat*.045 : 0; const kb=val('kenBurns') ? 1 + Math.sin(now*.00012)*.035 : 1; ctx.filter=`blur(${num('bgBlur')}px)`; if(state.bg) drawCover(state.bg.el,val('bgFit'),num('bgZoom')*kb+beatZoom); else { const g=ctx.createLinearGradient(0,0,W,H); g.addColorStop(0,'#1c1451'); g.addColorStop(.48,'#0f5f86'); g.addColorStop(1,'#221039'); ctx.fillStyle=g; ctx.fillRect(0,0,W,H); } ctx.filter='none'; ctx.fillStyle=`rgba(0,0,0,${num('bgDim')})`; ctx.fillRect(0,0,W,H); drawGrade(); ctx.restore(); }
function drawGrade(){ const p=val('gradePreset'); if(p==='none') return; const g=ctx.createLinearGradient(0,0,W,H); const stops={clouds:['rgba(143,107,255,.23)','rgba(70,215,255,.12)','rgba(255,93,184,.18)'],neon:['rgba(0,255,255,.2)','rgba(255,0,160,.16)','rgba(20,0,80,.25)'],sunset:['rgba(255,170,75,.22)','rgba(255,90,130,.16)','rgba(80,50,180,.18)'],mono:['rgba(0,0,0,.2)','rgba(255,255,255,.06)','rgba(0,0,0,.28)']}[p]; g.addColorStop(0,stops[0]); g.addColorStop(.5,stops[1]); g.addColorStop(1,stops[2]); ctx.globalCompositeOperation=p==='mono'?'saturation':'screen'; ctx.fillStyle=g; ctx.fillRect(0,0,W,H); ctx.globalCompositeOperation='source-over'; }
function drawVignette(){ const v=num('vignette'); const vg=ctx.createRadialGradient(W/2,H/2,Math.min(W,H)*.2,W/2,H/2,Math.max(W,H)*.72); vg.addColorStop(0,'rgba(0,0,0,0)'); vg.addColorStop(1,`rgba(0,0,0,${v})`); ctx.fillStyle=vg; ctx.fillRect(0,0,W,H); }
function updateParticles(dt){ const sp=num('pSpeed'), type=val('pType'); for(const p of particles){ p.tw+=dt*.003; if(type==='rain'){p.y+=p.vy*sp*9;p.x+=p.vx}else{p.x+=p.vx*sp*(1+state.beat);p.y+=p.vy*sp} if(p.y>H+30){p.y=-30;p.x=Math.random()*W} if(p.x<-30)p.x=W+30; if(p.x>W+30)p.x=-30; } }
function drawParticles(){ if(!val('particlesOn')) return; const type=val('pType'), op=num('pOp'), sz=num('pSize'), col=val('pColor'); ctx.save(); ctx.globalCompositeOperation= type==='bokeh'||type==='sparkle' ? 'lighter':'source-over'; for(const p of particles){ const alpha=p.a*op*(type==='sparkle'||type==='stars'?(.35+.65*Math.sin(p.tw)):1); const size=sz*p.s*(1+state.beat*.8); ctx.fillStyle=rgba(col,alpha); ctx.strokeStyle=rgba(col,alpha); if(type==='rain'){ctx.lineWidth=1.6;ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(p.x-2,p.y+size*7);ctx.stroke()} else if(type==='hearts') drawHeart(p.x,p.y,size*2); else if(type==='sparkle'||type==='stars') drawSparkle(p.x,p.y,size*2.2); else { const rg=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,size*2.8); rg.addColorStop(0,rgba(col,alpha)); rg.addColorStop(1,rgba(col,0)); ctx.fillStyle=rg; ctx.beginPath();ctx.arc(p.x,p.y,size*2.8,0,Math.PI*2);ctx.fill(); } } ctx.restore(); }
function drawHeart(x,y,s){ctx.beginPath();ctx.moveTo(x,y+s*.3);ctx.bezierCurveTo(x,y,x-s*.5,y,x-s*.5,y+s*.3);ctx.bezierCurveTo(x-s*.5,y+s*.6,x,y+s*.75,x,y+s);ctx.bezierCurveTo(x,y+s*.75,x+s*.5,y+s*.6,x+s*.5,y+s*.3);ctx.bezierCurveTo(x+s*.5,y,x,y,x,y+s*.3);ctx.fill();}
function drawSparkle(x,y,s){ctx.beginPath();for(let i=0;i<8;i++){const r=i%2?s*.28:s; const a=-Math.PI/2+i*Math.PI/4; ctx[i?'lineTo':'moveTo'](x+Math.cos(a)*r,y+Math.sin(a)*r);}ctx.closePath();ctx.fill();}
function drawVisualizer(now){ if(!val('visualizerOn')) return; const power=num('visPower'), style=val('visStyle'), level=state.audioLevel*power, beat=state.beat*power; ctx.save(); ctx.globalCompositeOperation='lighter'; if(style==='halo'){ const r=210+beat*180; const g=ctx.createRadialGradient(W/2,H*.43,80,W/2,H*.43,r*2.1); g.addColorStop(0,`rgba(70,215,255,${.1+level*.18})`); g.addColorStop(.42,`rgba(143,107,255,${.16+beat*.22})`); g.addColorStop(1,'rgba(255,93,184,0)'); ctx.fillStyle=g; ctx.beginPath(); ctx.arc(W/2,H*.43,r*2.1,0,Math.PI*2); ctx.fill(); } else if(style==='bars'){ const bars=96,bw=W/bars; for(let i=0;i<bars;i++){ const v=(state.freq?.[i*2]||0)/255*power; ctx.fillStyle=`hsla(${190+i*1.8},90%,65%,${.25+v*.6})`; ctx.fillRect(i*bw,H-80,bw*.56,-v*260); } } else { ctx.strokeStyle=`rgba(120,220,255,${.35+level*.6})`; ctx.lineWidth=5; ctx.beginPath(); for(let x=0;x<W;x+=8){ const y=H*.78+Math.sin(x*.018+now*.003)*(35+level*120); x?ctx.lineTo(x,y):ctx.moveTo(x,y); } ctx.stroke(); } ctx.restore(); }

function getCurrentLine(t){ const offsetSec=num('lyricOffset')/1000; let idx=-1; for(let i=0;i<state.lyrics.length;i++){ if(t >= state.lyrics[i].time + offsetSec) idx=i; else break; } return idx; }
function wrapText(text,maxWidth,fontStr){ ctx.font=fontStr; const words=text.split(/\s+/), lines=[]; let cur=''; for(const w of words){ const test=cur?cur+' '+w:w; if(ctx.measureText(test).width>maxWidth&&cur){lines.push(cur);cur=w}else cur=test; } if(cur) lines.push(cur); return lines; }
function drawLyrics(now){ if(!state.lyrics.length){ ctx.save(); ctx.fillStyle='rgba(255,255,255,.55)'; ctx.font='800 54px Poppins, sans-serif'; ctx.textAlign='center'; ctx.fillText('Load an LRC file and audio to begin',W/2,H/2); ctx.restore(); return; } const t=audio.currentTime, idx=getCurrentLine(t); if(idx<0) return; const line=state.lyrics[idx], off=num('lyricOffset')/1000, next=idx<state.lyrics.length-1?state.lyrics[idx+1].time+off:(audio.duration||Infinity), start=line.time+off, dur=next-start, elapsed=t-start; if(idx!==state.prevLineIdx){ state.prevLineIdx=idx; prevLineIdx=idx; state.currentLineText=line.text; state.lineEnterTime=now; state.lineAlpha=0; state.lineScale=1; state.lineLeaving=false; } const fadeIn=num('fadeIn'), fadeOut=num('fadeOut'), rem=dur-elapsed; if(!state.lineLeaving && rem<fadeOut/1000+.05){ state.lineLeaving=true; state.lineLeaveTime=now; } if(!state.lineLeaving){ const since=(now-state.lineEnterTime)/1000, p=clamp(since/(fadeIn/1000),0,1); state.lineAlpha=p; state.lineScale=1+(num('popScale')-1)*(1-easeOut(p)); } else state.lineAlpha=Math.max(0,1-((now-state.lineLeaveTime)/1000)/(fadeOut/1000));
  const fam=val('fontFamily')==='__custom'&&state.customFontName?state.customFontName:val('fontFamily'), fs=num('fontSize'), fw=val('fontWeight'), maxW=W*num('maxWidth')/100, lineSpace=num('lineSpace'), align=val('textAlign'), vert=num('vertPos')/100, fontStr=`${fw} ${fs}px "${fam}", sans-serif`; const lines=wrapText(state.currentLineText,maxW,fontStr), lineH=fs*lineSpace, blockH=lines.length*lineH, startY=H*vert-blockH/2+lineH*.8; const anim=val('lyricAnim'), p=clamp((now-state.lineEnterTime)/fadeIn,0,1), ep=easeOut(p); ctx.save(); ctx.globalAlpha=state.lineAlpha; ctx.font=fontStr; ctx.textAlign=align; ctx.textBaseline='alphabetic'; let tx=W/2, ty=H*vert; if(anim==='float') ty+=(1-ep)*38; if(anim==='slide') tx+=(1-ep)*-80; ctx.translate(tx,ty); const sc= anim==='zoom' ? .82+ep*.18+state.beat*.03 : state.lineScale+state.beat*.015; ctx.scale(sc,sc); ctx.translate(-W/2,-H*vert); if(anim==='slide'){ctx.transform(1,0,-.08*(1-ep),1,0,0)} ctx.shadowColor=rgba(val('fillColor2'),.62); ctx.shadowBlur=num('textGlow')+state.beat*20; ctx.shadowOffsetY=6; const fillGrad=ctx.createLinearGradient(W/2-maxW/2,startY,W/2+maxW/2,startY+blockH); fillGrad.addColorStop(0,val('fillColor')); fillGrad.addColorStop(1,val('fillColor2')); lines.forEach((ln,i)=>{ let shown=ln; if(anim==='type'){ const chars=Math.ceil(ln.length*clamp((elapsed-.02*i)/Math.max(.25,dur*.45),0,1)); shown=ln.slice(0,chars); } const y=startY+i*lineH, x=align==='left'?W/2-maxW/2:align==='right'?W/2+maxW/2:W/2; if(num('strokeWidth')>0){ ctx.strokeStyle=val('strokeColor'); ctx.lineWidth=num('strokeWidth')*2; ctx.lineJoin='round'; ctx.miterLimit=2; ctx.strokeText(shown,x,y); } ctx.fillStyle=val('textGradient')?fillGrad:val('fillColor'); ctx.fillText(shown,x,y); }); ctx.restore(); }
function drawOverlays(){ state.overlays.forEach(layer=>{ if(!layer.visible) return; ctx.save(); ctx.globalAlpha=layer.opacity; ctx.globalCompositeOperation=layer.blend; ctx.translate(W*layer.x/100,H*layer.y/100); ctx.rotate(layer.rotate*Math.PI/180); if(layer.type==='text'){ ctx.font=`800 ${Math.max(18,layer.size*3)}px Poppins, sans-serif`; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.shadowColor='rgba(0,0,0,.65)'; ctx.shadowBlur=18; ctx.fillStyle='#fff'; ctx.fillText(layer.text||layer.name,0,0); } else { const el=layer.el, iw=el.videoWidth||el.naturalWidth||el.width||300, ih=el.videoHeight||el.naturalHeight||el.height||200; if(iw&&ih){ const dw=W*layer.size/100, dh=dw*(ih/iw); ctx.drawImage(el,-dw/2,-dh/2,dw,dh); } } ctx.restore(); }); ctx.globalCompositeOperation='source-over'; }

function frame(now){ const dt=now-state.lastFrame; state.lastFrame=now; updateAudioLevel(); drawBackground(now); drawVisualizer(now); updateParticles(dt); drawParticles(); drawOverlays(); drawLyrics(now); drawVignette(); updateUI(now); requestAnimationFrame(frame); }
requestAnimationFrame(frame);
function updateUI(now){ const t=audio.currentTime,d=audio.duration||0; $('timeDisp').textContent=`${fmt(t)} / ${fmt(d)}`; $('progressBar').style.width=d?(t/d*100)+'%':'0%'; state.fpsFrames++; if(now-state.fpsTime>600){ state.fps=Math.round(state.fpsFrames*1000/(now-state.fpsTime)); state.fpsFrames=0; state.fpsTime=now; $('fpsMeter').textContent=`${state.fps} fps`; } }
async function togglePlay(){ if(!audio.src){showToast('Load audio first');return;} setupAudioGraph(); if(audio.paused){ await audio.play(); $('playBtn').textContent='⏸ Pause'; } else { audio.pause(); $('playBtn').textContent='▶ Play'; } }
$('playBtn').addEventListener('click',togglePlay); $('stopBtn').addEventListener('click',()=>{ audio.pause(); audio.currentTime=0; $('playBtn').textContent='▶ Play'; }); audio.addEventListener('ended',()=>$('playBtn').textContent='▶ Play'); $('progress').addEventListener('click',e=>{ if(!audio.duration)return; const r=e.currentTarget.getBoundingClientRect(); audio.currentTime=((e.clientX-r.left)/r.width)*audio.duration; });
window.addEventListener('keydown',e=>{ if(['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)) return; if(e.code==='Space'){ e.preventDefault(); if(isRecording) stopRecording(); else togglePlay(); } else if(e.code==='ArrowRight') audio.currentTime=Math.min(audio.duration||0,audio.currentTime+5); else if(e.code==='ArrowLeft') audio.currentTime=Math.max(0,audio.currentTime-5); else if(e.code==='Escape'&&isRecording) stopRecording(); else if(e.key.toLowerCase()==='h') document.body.classList.toggle('ui-hidden'); else if(e.key.toLowerCase()==='f') $('canvasWrap').requestFullscreen().catch(()=>{}); });
$('cinemaBtn').addEventListener('click',()=>document.body.classList.toggle('cinema')); $('fullscreenBtn').addEventListener('click',()=>$('canvasWrap').requestFullscreen().catch(()=>{})); $('fitBtn').addEventListener('click',()=>showToast('Preview is fit to window automatically'));

function renderOverlayList(){ const list=$('overlayList'); list.innerHTML=''; state.overlays.forEach(l=>{ const d=document.createElement('div'); d.className='layer-item'+(l.id===state.selectedLayer?' active':''); d.innerHTML=`<span>${l.type==='text'?'🔤':'🖼️'} ${l.name}</span><button data-id="${l.id}">${l.visible?'Hide':'Show'}</button>`; d.addEventListener('click',e=>{ if(e.target.tagName!=='BUTTON') selectLayer(l.id); }); d.querySelector('button').addEventListener('click',()=>{ l.visible=!l.visible; renderOverlayList(); }); list.appendChild(d); }); updateStatus(); }
function selectLayer(id){ state.selectedLayer=id; const l=state.overlays.find(x=>x.id===id); if(!l) return; $('layerName').value=l.name; $('layerX').value=l.x; $('layerY').value=l.y; $('layerSize').value=l.size; $('layerOpacity').value=l.opacity; $('layerRotate').value=l.rotate; $('layerBlend').value=l.blend; $('layerText').value=l.text||''; ['layerX','layerY','layerSize','layerOpacity','layerRotate'].forEach(id=>$(id).dispatchEvent(new Event('input'))); renderOverlayList(); }
function updateSelectedFromControls(id){ if(!id?.startsWith('layer')) return; const l=state.overlays.find(x=>x.id===state.selectedLayer); if(!l) return; l.x=num('layerX'); l.y=num('layerY'); l.size=num('layerSize'); l.opacity=num('layerOpacity'); l.rotate=num('layerRotate'); }
['layerName','layerBlend','layerText'].forEach(id=>$(id).addEventListener('input',()=>{ const l=state.overlays.find(x=>x.id===state.selectedLayer); if(!l)return; l.name=$('layerName').value; l.blend=$('layerBlend').value; l.text=$('layerText').value; renderOverlayList(); }));
$('deleteLayer').addEventListener('click',()=>{ const i=state.overlays.findIndex(x=>x.id===state.selectedLayer); if(i>=0){ const [l]=state.overlays.splice(i,1); if(l.url)URL.revokeObjectURL(l.url); state.selectedLayer=null; renderOverlayList(); }}); $('layerUp').addEventListener('click',()=>moveLayer(1)); $('layerDown').addEventListener('click',()=>moveLayer(-1)); function moveLayer(dir){ const i=state.overlays.findIndex(x=>x.id===state.selectedLayer), j=i+dir; if(i>=0&&j>=0&&j<state.overlays.length){ [state.overlays[i],state.overlays[j]]=[state.overlays[j],state.overlays[i]]; renderOverlayList(); } }
const PRESETS_KEY='lyricforge_position_presets_v2'; let positionPresets={}; function loadPresets(){ try{positionPresets=JSON.parse(localStorage.getItem(PRESETS_KEY)||'{}')}catch{positionPresets={}} renderPresets(); } function savePresets(){ localStorage.setItem(PRESETS_KEY,JSON.stringify(positionPresets)); } function renderPresets(){ const grid=$('presetsGrid'); grid.innerHTML=''; for(let i=1;i<=6;i++){ const val=positionPresets[i]; const slot=document.createElement('div'); slot.className='preset-slot'; slot.innerHTML=`<div class="num">${i}</div><div class="val">${val!==undefined?val+'%':'—'}</div><button class="save">Save</button><button class="load" ${val===undefined?'disabled':''}>Load</button>`; slot.querySelector('.save').onclick=()=>{positionPresets[i]=num('vertPos');savePresets();renderPresets();showToast(`Saved slot ${i}`)}; slot.querySelector('.load').onclick=()=>{if(positionPresets[i]!==undefined){$('vertPos').value=positionPresets[i];$('vertPos').dispatchEvent(new Event('input'));showToast(`Loaded slot ${i}`)}}; grid.appendChild(slot); }} loadPresets();
const dz=$('dropzone'); ['dragenter','dragover'].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.classList.add('drag')})); ['dragleave','drop'].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.classList.remove('drag')})); dz.addEventListener('drop',e=>{ [...e.dataTransfer.files].forEach(file=>{ if(file.type.startsWith('audio/')){audio.src=URL.createObjectURL(file)} else if(file.name.match(/\.(lrc|txt)$/i)){const r=new FileReader();r.onload=ev=>{state.lyrics=parseLRC(ev.target.result);lyrics=state.lyrics;$('manualLyrics').value=ev.target.result;updateStatus()};r.readAsText(file)} else if(file.name.match(/\.(ttf|otf|woff2?)$/i)){} else if(!state.bg) setBackgroundFile(file); else addOverlayFiles([file]); }); updateStatus(); });

$('exportBtn').addEventListener('click', startExport);
async function startExport(){
  if(!audio.src){ showToast('Load audio first'); return; }
  if(!lyrics.length){ showToast('Load an LRC file first'); return; }

  showToast('Going fullscreen & starting record…');

  // Reset playback
  audio.currentTime = 0;
  prevLineIdx = -1;
  state.prevLineIdx = -1;

  // Fullscreen
  try { await document.documentElement.requestFullscreen(); } catch(e){}

  // Capture canvas stream + audio
  const canvasStream = canvas.captureStream(60);
  let combinedStream = canvasStream;
  try {
    const audioCtx = new AudioContext();
    const src = audioCtx.createMediaElementSource(audio);
    const dest = audioCtx.createMediaStreamDestination();
    src.connect(dest);
    src.connect(audioCtx.destination); // also hear it
    combinedStream = new MediaStream([
      ...canvasStream.getVideoTracks(),
      ...dest.stream.getAudioTracks()
    ]);
  } catch(err){
    console.warn('Audio capture failed, recording video only:', err);
  }

  const mime = MediaRecorder.isTypeSupported('video/webm;codecs=vp9,opus')
    ? 'video/webm;codecs=vp9,opus'
    : 'video/webm';
  mediaRecorder = new MediaRecorder(combinedStream, {
    mimeType: mime,
    videoBitsPerSecond: +$('bitrate').value
  });
  recordedChunks = [];
  mediaRecorder.ondataavailable = e=>{ if(e.data.size>0) recordedChunks.push(e.data); };
  mediaRecorder.onstop = ()=>{
    const blob = new Blob(recordedChunks, {type:'video/webm'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `lyrics_${Date.now()}.webm`;
    a.click();
    URL.revokeObjectURL(url);
    $('recBadge').classList.remove('on');
    isRecording = false;
    $('exportBtn').textContent = '🔴 Export 1080p 60fps';
    $('exportBtn').classList.add('good');
    $('exportBtn').classList.remove('warn');
    showToast('Export saved!');
    try{ document.exitFullscreen(); }catch(e){}
  };

  mediaRecorder.start(100);
  isRecording = true;
  $('recBadge').classList.add('on');
  $('exportBtn').textContent = '■ Stop Recording (Space)';
  $('exportBtn').classList.remove('good');
  $('exportBtn').classList.add('warn');

  // Auto-start audio
  try{ await audio.play(); $('playBtn').textContent = '⏸ Pause'; }
  catch(e){ showToast('Click canvas to enable audio, press Space'); }
}
function stopRecording(){ if(mediaRecorder && mediaRecorder.state !== 'inactive'){ mediaRecorder.stop(); audio.pause(); } }

setupTabs(); updateStatus(); setTimeout(()=>showToast('Press <b>Space</b> to play · <b>H</b> hide UI · add overlays in Layers'),800);
