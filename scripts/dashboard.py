#!/usr/bin/env python3
"""
git-orchestrator dashboard — live Git graph viewer
Usage:  python3 scripts/dashboard.py [--port 7777]
Auto-start: launched by SessionStart hook (see .claude/settings.json.example)
"""
import argparse, http.server, json, os, subprocess, sys, urllib.parse
from datetime import datetime, timezone

DEFAULT_PORT = int(os.environ.get("GIT_DASHBOARD_PORT", 7777))


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------
def _git(args, cwd):
    r = subprocess.run(["git"] + args, capture_output=True, text=True, cwd=cwd)
    return r.stdout.strip()

def repo_root():
    return _git(["rev-parse", "--show-toplevel"], os.getcwd())

def _assign_lanes(commits):
    active, lanes = [], []
    for c in commits:
        short = c["hash"]
        lane = next((i for i, h in enumerate(active) if h == short), None)
        if lane is None:
            try:
                lane = active.index(None); active[lane] = short
            except ValueError:
                active.append(short); lane = len(active) - 1
        parents = c["parents"]
        if parents:
            active[lane] = parents[0]
            for extra in parents[1:]:
                if extra not in active:
                    try:
                        idx = active.index(None); active[idx] = extra
                    except ValueError:
                        active.append(extra)
        else:
            active[lane] = None
        lanes.append(lane)
    return lanes

def api_graph(root):
    sep = "\x1f"
    raw = _git(["log","--all","--topo-order",
                 f"--format=%H{sep}%P{sep}%an{sep}%ae{sep}%aI{sep}%s{sep}%D",
                 "--max-count=300"], root)
    commits = []
    for line in raw.splitlines():
        if not line: continue
        parts = line.split(sep, 6)
        if len(parts) < 7: continue
        h, parents_str, an, ae, date, subject, refs_str = parts
        short  = h[:8]
        parents = [p[:8] for p in parents_str.split() if p]
        refs = []
        for r in refs_str.split(","):
            r = r.strip().replace("HEAD -> ","")
            if r and r != "HEAD" and r not in refs:
                refs.append(r)
        commits.append({"hash":short,"full_hash":h,"parents":parents,
                         "author_name":an,"author_email":ae,"date":date,
                         "subject":subject,"refs":refs})
    lane_indices = _assign_lanes(commits)
    max_lane = max(lane_indices) if lane_indices else 0
    for i, c in enumerate(commits):
        c["lane"] = lane_indices[i]
    team_raw = _git(["log","--all","--format=%an\t%ae"], root)
    team: dict = {}
    for line in team_raw.splitlines():
        if "\t" not in line: continue
        name, email = line.split("\t",1)
        key = email.strip() or name.strip()
        if key not in team:
            team[key] = {"name":name.strip(),"email":email.strip(),"commits":0}
        team[key]["commits"] += 1
    return {"commits":commits,
            "team":sorted(team.values(), key=lambda x: -x["commits"]),
            "max_lane":max_lane}

def api_status(root):
    branch = _git(["rev-parse","--abbrev-ref","HEAD"], root)
    repo_name = os.path.basename(root)
    porcelain = _git(["status","--porcelain"], root)
    lines = [l for l in porcelain.splitlines() if l]
    staged   = sum(1 for l in lines if l and l[0] not in (" ","?"))
    unstaged = sum(1 for l in lines if l and l[1] not in (" ","?") and l[0] != "?")
    untracked= sum(1 for l in lines if l.startswith("??"))
    return {"current_branch":branch,"repo_name":repo_name,"is_dirty":bool(porcelain),
            "staged":staged,"unstaged":unstaged,"untracked":untracked,
            "timestamp":datetime.now(timezone.utc).isoformat()}


# ---------------------------------------------------------------------------
# HTML (embedded — no static files needed)
# All dynamic content built via DOM API (createElement/textContent/setAttribute)
# No innerHTML used for user-supplied data
# ---------------------------------------------------------------------------
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>git-orchestrator · Dashboard</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0d1117;--surface:#161b22;--surface2:#1c2128;
  --border:#30363d;--text:#e6edf3;--muted:#8b949e;--accent:#a371f7;
}
html,body{height:100%;overflow:hidden}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
  background:var(--bg);color:var(--text);display:flex;flex-direction:column;font-size:13px}
/* Header */
header{display:flex;align-items:center;gap:12px;padding:0 20px;height:52px;
  border-bottom:1px solid var(--border);background:var(--surface);flex-shrink:0;z-index:10}
.logo{display:flex;align-items:center;gap:8px;font-weight:700;font-size:15px}
.logo svg{width:22px;height:22px}
.repo-name{font-size:12px;color:var(--muted);padding:2px 8px;
  background:var(--bg);border:1px solid var(--border);border-radius:6px;
  font-family:ui-monospace,monospace}
.branch-pill{display:flex;align-items:center;gap:5px;padding:2px 10px;
  border-radius:100px;font-size:12px;font-family:ui-monospace,monospace;
  background:rgba(163,113,247,.14);border:1px solid rgba(163,113,247,.35);color:#a371f7}
.branch-pill svg{width:12px;height:12px}
.spacer{flex:1}
.chips{display:flex;gap:6px;align-items:center}
.chip{padding:2px 8px;border-radius:100px;font-size:11px;font-weight:600;border:1px solid}
.chip-s{color:#3fb950;border-color:rgba(63,185,80,.4);background:rgba(63,185,80,.08)}
.chip-u{color:#ffa657;border-color:rgba(255,166,87,.4);background:rgba(255,166,87,.08)}
.chip-n{color:#79c0ff;border-color:rgba(121,192,255,.4);background:rgba(121,192,255,.08)}
.btn{display:flex;align-items:center;gap:5px;padding:4px 10px;
  border:1px solid var(--border);border-radius:6px;background:var(--surface2);
  color:var(--muted);cursor:pointer;font-size:12px;transition:all .15s}
.btn:hover{border-color:var(--accent);color:var(--text)}
.btn.spin svg{animation:spin .6s linear infinite}
.ts{font-size:11px;color:var(--muted)}
@keyframes spin{to{transform:rotate(360deg)}}
/* Layout */
.layout{display:flex;flex:1;overflow:hidden}
/* Sidebar */
aside{width:240px;flex-shrink:0;border-right:1px solid var(--border);
  background:var(--surface);display:flex;flex-direction:column;overflow:hidden}
.aside-sec{padding:14px 16px 10px}
.aside-sec.flex{flex:1;overflow:hidden;display:flex;flex-direction:column}
.aside-title{font-size:11px;font-weight:600;letter-spacing:.06em;
  text-transform:uppercase;color:var(--muted);margin-bottom:10px}
.team-list,.branch-list{display:flex;flex-direction:column;gap:5px;overflow-y:auto}
.team-row{display:flex;align-items:center;gap:9px;padding:7px 10px;
  border-radius:8px;transition:background .12s}
.team-row:hover{background:var(--surface2)}
.avatar{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-weight:700;font-size:12px;color:#fff;flex-shrink:0}
.member-name{font-size:12px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.member-cmt{font-size:11px;color:var(--muted)}
.br-row{display:flex;align-items:center;gap:8px;padding:5px 10px;border-radius:6px;transition:background .12s}
.br-row:hover{background:var(--surface2)}
.br-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.br-name{font-size:12px;font-family:ui-monospace,monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.br-cur{font-size:10px;color:var(--muted);margin-left:auto;flex-shrink:0}
.divider{height:1px;background:var(--border);margin:0 16px;flex-shrink:0}
/* Graph */
.graph-wrap{flex:1;overflow:auto;position:relative;background:var(--bg)}
#graph-svg{display:block}
/* Detail */
.detail{width:340px;flex-shrink:0;border-left:1px solid var(--border);
  background:var(--surface);display:flex;flex-direction:column;overflow:hidden}
.detail-empty{flex:1;display:flex;flex-direction:column;align-items:center;
  justify-content:center;gap:10px;color:var(--muted);font-size:13px;text-align:center;padding:24px}
.detail-empty svg{opacity:.3;width:36px;height:36px}
.detail-body{flex:1;overflow-y:auto;padding:18px;display:flex;flex-direction:column;gap:14px}
.d-subject{font-size:15px;font-weight:600;line-height:1.4}
.d-refs{display:flex;flex-wrap:wrap;gap:5px}
.ref-pill{padding:2px 8px;border-radius:100px;font-size:11px;
  font-family:ui-monospace,monospace;font-weight:600;border:1px solid}
.sec-lbl{font-size:11px;font-weight:600;letter-spacing:.05em;
  text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.meta-grid{display:flex;flex-direction:column;gap:7px}
.meta-row{display:flex;align-items:flex-start;gap:10px;font-size:12px}
.meta-lbl{color:var(--muted);width:60px;flex-shrink:0;padding-top:1px}
.meta-val{color:var(--text);font-family:ui-monospace,monospace;word-break:break-all}
.parent-link{color:#58a6ff;cursor:pointer;text-decoration:underline dotted;font-size:12px;
  font-family:ui-monospace,monospace;display:block}
.parent-link:hover{color:#a371f7}
/* Loading */
.loading{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
  background:var(--bg);z-index:5;color:var(--muted);gap:10px}
.loading svg{animation:spin .8s linear infinite;width:18px;height:18px}
/* Scrollbar */
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:#30363d;border-radius:3px}
</style>
</head>
<body>
<header>
  <div class="logo">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/>
      <path d="M18 9v1a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V9"/><line x1="12" y1="12" x2="12" y2="15"/>
    </svg>
    git-orchestrator
  </div>
  <span class="repo-name" id="repo-name"></span>
  <div class="branch-pill">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
      <line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/>
      <path d="M18 9a9 9 0 0 1-9 9"/>
    </svg>
    <span id="branch-name"></span>
  </div>
  <div class="chips" id="chips"></div>
  <div class="spacer"></div>
  <span class="ts" id="ts"></span>
  <button class="btn" id="ref-btn" onclick="load()">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
      <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.51"/>
    </svg>
    Refresh
  </button>
</header>
<div class="layout">
  <aside>
    <div class="aside-sec">
      <div class="aside-title">Team</div>
      <div class="team-list" id="team-list"></div>
    </div>
    <div class="divider"></div>
    <div class="aside-sec flex">
      <div class="aside-title">Branches</div>
      <div class="branch-list" id="branch-list"></div>
    </div>
  </aside>
  <div class="graph-wrap" id="graph-wrap">
    <div class="loading" id="loading">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
      </svg>
      Loading graph…
    </div>
    <svg id="graph-svg"></svg>
  </div>
  <div class="detail">
    <div class="detail-empty" id="detail-empty">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      Click a commit to see details
    </div>
    <div class="detail-body" id="detail-body" style="display:none"></div>
  </div>
</div>
<script>
// ── Constants ─────────────────────────────────────────────────────────────────
const COLORS=['#a371f7','#58a6ff','#3fb950','#ffa657','#ff7b72','#f778ba',
              '#79c0ff','#d2a8ff','#39d353','#ffd700','#56d364','#e3b341'];
const ROW_H=56, LANE_W=26, DOT_R=7, PAD_L=18, PAD_R=24, GRAPH_LABEL_GAP=14;
const NS='http://www.w3.org/2000/svg';

// ── State ──────────────────────────────────────────────────────────────────────
let gData=null, sData=null, selected=null;

// ── Fetch ─────────────────────────────────────────────────────────────────────
async function load(){
  const btn=document.getElementById('ref-btn');
  btn.classList.add('spin');
  try{
    const[g,s]=await Promise.all([
      fetch('/api/graph').then(r=>r.json()),
      fetch('/api/status').then(r=>r.json()),
    ]);
    gData=g; sData=s;
    renderHeader();
    renderSidebar();
    renderGraph();
  }catch(e){console.error(e);}
  finally{
    btn.classList.remove('spin');
    const el=document.getElementById('ts');
    el.textContent='Updated '+new Date().toLocaleTimeString();
    document.getElementById('loading').style.display='none';
  }
}

// ── Header ───────────────────────────────────────────────────────────────────
function renderHeader(){
  setText('repo-name', sData.repo_name);
  setText('branch-name', sData.current_branch);
  const chips=document.getElementById('chips');
  chips.textContent='';
  if(sData.staged)    chips.append(chip(sData.staged+' staged','chip-s'));
  if(sData.unstaged)  chips.append(chip(sData.unstaged+' modified','chip-u'));
  if(sData.untracked) chips.append(chip(sData.untracked+' untracked','chip-n'));
}
function chip(text, cls){
  const el=document.createElement('span');
  el.className='chip '+cls;
  el.textContent=text;
  return el;
}

// ── Sidebar ──────────────────────────────────────────────────────────────────
const avatarPalette=['#7c3aed','#0ea5e9','#059669','#d97706','#dc2626','#db2777','#0891b2'];
function avatarColor(name){
  let h=0; for(const c of name) h=(h*31+c.charCodeAt(0))&0x7fffffff;
  return avatarPalette[h%avatarPalette.length];
}
function initials(name){
  return name.trim().split(/\s+/).map(w=>w[0]||'').join('').slice(0,2).toUpperCase();
}
function renderSidebar(){
  const teamEl=document.getElementById('team-list');
  teamEl.textContent='';
  for(const m of gData.team){
    const row=document.createElement('div'); row.className='team-row';
    const av=document.createElement('div'); av.className='avatar';
    av.style.background=avatarColor(m.name); av.textContent=initials(m.name);
    const info=document.createElement('div'); info.style.flex='1'; info.style.minWidth='0';
    const nm=document.createElement('div'); nm.className='member-name'; nm.textContent=m.name;
    const ct=document.createElement('div'); ct.className='member-cmt';
    ct.textContent=m.commits+' commit'+(m.commits!==1?'s':'');
    info.append(nm,ct); row.append(av,info); teamEl.append(row);
  }
  const brEl=document.getElementById('branch-list');
  brEl.textContent='';
  const branches=extractBranches();
  for(const b of branches){
    const row=document.createElement('div'); row.className='br-row';
    const dot=document.createElement('div'); dot.className='br-dot'; dot.style.background=b.color;
    const nm=document.createElement('div'); nm.className='br-name';
    nm.textContent=b.name.replace('origin/','');
    row.append(dot,nm);
    if(b.isCurrent){
      const cur=document.createElement('div'); cur.className='br-cur'; cur.textContent='current';
      row.append(cur);
    }
    brEl.append(row);
  }
}
function extractBranches(){
  const seen=new Map();
  for(const c of gData.commits)
    for(const r of c.refs)
      if(!seen.has(r)) seen.set(r,c.lane);
  const cur=sData.current_branch;
  return Array.from(seen.entries()).map(([name,lane])=>({
    name,lane,color:COLORS[lane%COLORS.length],
    isCurrent:name===cur||name==='origin/'+cur,
  }));
}

// ── Graph (SVG via DOM API) ───────────────────────────────────────────────────
function svgEl(tag,attrs={},text=null){
  const el=document.createElementNS(NS,tag);
  for(const[k,v]of Object.entries(attrs)) el.setAttribute(k,String(v));
  if(text!==null) el.textContent=text;
  return el;
}

function renderGraph(){
  const commits=gData.commits;
  const svg=document.getElementById('graph-svg');
  svg.textContent='';
  if(!commits.length){
    svg.append(svgEl('text',{x:20,y:40,fill:'#8b949e'},'No commits found.'));
    return;
  }
  const maxLane=gData.max_lane;
  const graphW=PAD_L+(maxLane+1)*LANE_W;
  const totalW=graphW+GRAPH_LABEL_GAP+580;
  const totalH=commits.length*ROW_H+16;
  svg.setAttribute('width',totalW); svg.setAttribute('height',totalH);

  const hashIdx={};
  commits.forEach((c,i)=>hashIdx[c.hash]=i);
  const cx=c=>PAD_L+c.lane*LANE_W;
  const cy=i=>8+i*ROW_H+ROW_H/2;
  const rightX=totalW-PAD_R;

  // Layer groups for correct z-order
  const gEdges =svgEl('g'); // edges first (behind rows)
  const gRows  =svgEl('g'); // clickable rows
  const gDots  =svgEl('g'); // dots on top

  // Edges
  for(let i=0;i<commits.length;i++){
    const c=commits[i];
    const color=COLORS[c.lane%COLORS.length];
    const x0=cx(c), y0=cy(i);
    for(let pi=0;pi<c.parents.length;pi++){
      const ph=c.parents[pi];
      const pi2=hashIdx[ph];
      if(pi2===undefined) continue;
      const cp=commits[pi2];
      const x1=cx(cp), y1=cy(pi2);
      const edgeColor=pi===0?color:COLORS[cp.lane%COLORS.length];
      if(x0===x1){
        gEdges.append(svgEl('line',{x1:x0,y1:y0,x2:x1,y2:y1,
          stroke:edgeColor,'stroke-width':2,opacity:.65}));
      }else{
        const midY=(y0+y1)/2;
        gEdges.append(svgEl('path',{
          d:`M${x0},${y0} C${x0},${midY} ${x1},${midY} ${x1},${y1}`,
          fill:'none',stroke:edgeColor,'stroke-width':2,opacity:.55}));
      }
    }
  }

  // Rows + labels
  for(let i=0;i<commits.length;i++){
    const c=commits[i];
    const color=COLORS[c.lane%COLORS.length];
    const x0=cx(c), y0=cy(i);
    const rowY=8+i*ROW_H;
    const isSel=selected===c.hash;

    const gRow=svgEl('g');
    gRow.style.cursor='pointer';
    gRow.addEventListener('click',()=>selectCommit(c.hash));

    // Row bg
    const bg=svgEl('rect',{x:0,y:rowY,width:totalW,height:ROW_H,
      fill:isSel?'rgba(163,113,247,.10)':'rgba(255,255,255,0)',rx:0});
    bg.style.transition='fill .1s';
    bg.addEventListener('mouseenter',()=>{ if(!isSel) bg.setAttribute('fill','rgba(255,255,255,.04)'); });
    bg.addEventListener('mouseleave',()=>{ if(!isSel) bg.setAttribute('fill','rgba(255,255,255,0)'); });
    gRow.append(bg);

    // Ref pills
    let lx=graphW+GRAPH_LABEL_GAP;
    for(const ref of c.refs){
      const label=ref.replace('origin/','');
      const w=label.length*6.8+14;
      gRow.append(svgEl('rect',{x:lx,y:y0-10,width:w,height:20,rx:5,
        fill:color,opacity:.18}));
      gRow.append(svgEl('rect',{x:lx,y:y0-10,width:w,height:20,rx:5,
        fill:'none',stroke:color,'stroke-width':1,opacity:.45}));
      const rt=svgEl('text',{x:lx+7,y:y0+5,fill:color,'font-size':11,
        'font-weight':600,'font-family':'ui-monospace,monospace'});
      rt.textContent=label;
      gRow.append(rt); lx+=w+6;
    }

    // Subject
    const subjectX=lx+(c.refs.length?6:0);
    const st=svgEl('text',{x:subjectX,y:y0+5,fill:isSel?'#e6edf3':'#cdd9e5',
      'font-size':13,'font-family':'-apple-system,BlinkMacSystemFont,system-ui,sans-serif'});
    st.textContent=truncate(c.subject,46);
    gRow.append(st);

    // Hash (right side, dim)
    const ht=svgEl('text',{x:rightX-110,y:y0+8,'text-anchor':'end',
      fill:'#6e7681','font-size':11,'font-family':'ui-monospace,monospace'});
    ht.textContent=c.hash;
    gRow.append(ht);

    // Author
    const at=svgEl('text',{x:rightX,y:y0-7,'text-anchor':'end',
      fill:'#8b949e','font-size':11,
      'font-family':'-apple-system,BlinkMacSystemFont,system-ui,sans-serif'});
    at.textContent=c.author_name;
    gRow.append(at);

    // Date
    const dt=svgEl('text',{x:rightX,y:y0+8,'text-anchor':'end',
      fill:'#6e7681','font-size':11,'font-family':'ui-monospace,monospace'});
    dt.textContent=relDate(c.date);
    gRow.append(dt);

    gRows.append(gRow);

    // Dot
    const dot=svgEl('circle',{cx:x0,cy:y0,r:DOT_R,
      fill:isSel?color:'#0d1117',stroke:color,'stroke-width':2.5});
    dot.style.cursor='pointer';
    dot.addEventListener('click',()=>selectCommit(c.hash));
    gDots.append(dot);
  }

  svg.append(gEdges,gRows,gDots);
}

// ── Detail panel (DOM API, no innerHTML for data) ────────────────────────────
function selectCommit(hash){
  selected=hash;
  const c=gData.commits.find(x=>x.hash===hash);
  if(!c) return;
  renderGraph(); // refresh selection highlight

  document.getElementById('detail-empty').style.display='none';
  const body=document.getElementById('detail-body');
  body.style.display='flex';
  body.textContent='';

  const color=COLORS[c.lane%COLORS.length];

  // Subject
  const subj=document.createElement('div'); subj.className='d-subject';
  subj.textContent=c.subject; body.append(subj);

  // Refs
  if(c.refs.length){
    const refRow=document.createElement('div'); refRow.className='d-refs';
    for(const r of c.refs){
      const pill=document.createElement('span'); pill.className='ref-pill';
      pill.textContent=r.replace('origin/','');
      pill.style.cssText=`color:${color};border-color:${color}40;background:${color}18`;
      refRow.append(pill);
    }
    body.append(refRow);
  }

  // Metadata
  const metaWrap=document.createElement('div');
  const metaLbl=document.createElement('div'); metaLbl.className='sec-lbl';
  metaLbl.textContent='Metadata'; metaWrap.append(metaLbl);
  const grid=document.createElement('div'); grid.className='meta-grid';
  const rows=[
    ['Hash',    c.full_hash],
    ['Author',  c.author_name, 'inherit'],
    ['Email',   c.author_email],
    ['Date',    c.date ? new Date(c.date).toLocaleString() : '—', 'inherit'],
  ];
  for(const[lbl,val,ff]of rows){
    const mr=document.createElement('div'); mr.className='meta-row';
    const ml=document.createElement('div'); ml.className='meta-lbl'; ml.textContent=lbl;
    const mv=document.createElement('div'); mv.className='meta-val';
    if(ff) mv.style.fontFamily=ff;
    mv.textContent=val; mr.append(ml,mv); grid.append(mr);
  }
  if(c.parents.length){
    const mr=document.createElement('div'); mr.className='meta-row';
    const ml=document.createElement('div'); ml.className='meta-lbl';
    ml.textContent='Parent'+(c.parents.length>1?'s':'');
    const mv=document.createElement('div'); mv.className='meta-val';
    for(const p of c.parents){
      const a=document.createElement('span'); a.className='parent-link';
      a.textContent=p; a.addEventListener('click',()=>selectCommit(p));
      mv.append(a);
    }
    mr.append(ml,mv); grid.append(mr);
  }
  metaWrap.append(grid); body.append(metaWrap);
}

// ── Utils ─────────────────────────────────────────────────────────────────────
function setText(id,val){ document.getElementById(id).textContent=val; }
function truncate(s,n){ return s.length>n?s.slice(0,n)+'…':s; }
function relDate(iso){
  if(!iso) return '—';
  const d=new Date(iso), now=new Date(), ms=now-d;
  const h=ms/36e5;
  if(h<1)  return Math.round(ms/60000)+'m ago';
  if(h<24) return Math.round(h)+'h ago';
  const d2=Math.round(h/24);
  if(d2<30)return d2+'d ago';
  return d.toLocaleDateString();
}

// ── Boot ──────────────────────────────────────────────────────────────────────
load();
setInterval(load,30000);
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        root = repo_root()
        try:
            if path == "/api/graph":
                self._json(api_graph(root))
            elif path == "/api/status":
                self._json(api_status(root))
            elif path in ("/", "/index.html"):
                self._send(200, "text/html; charset=utf-8", HTML.encode())
            else:
                self.send_error(404)
        except Exception as e:
            self.send_error(500, str(e))

    def _json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self._send(200, "application/json; charset=utf-8", body)

    def _send(self, code, ct, body):
        self.send_response(code)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="git-orchestrator dashboard")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    root = repo_root()
    if not root:
        print("[dashboard] Not inside a git repository.", file=sys.stderr)
        sys.exit(1)

    server = http.server.HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"[git-orchestrator] Dashboard → http://localhost:{args.port}")
    print(f"[git-orchestrator] Watching : {root}")
    print(f"[git-orchestrator] Stop     : Ctrl-C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[git-orchestrator] Stopped.")
