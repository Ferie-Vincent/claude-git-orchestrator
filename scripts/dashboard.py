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
# ---------------------------------------------------------------------------
# HTML — Redesigned with Tailwind + Lucide + Inter/JetBrains Mono
# Dynamic content built via DOM API (createElement/textContent/setAttribute)
# ---------------------------------------------------------------------------
HTML = r"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>git-orchestrator - Dashboard</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://unpkg.com/lucide@latest"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  body { font-family:'Inter',system-ui,-apple-system,sans-serif; }
  .font-mono { font-family:'JetBrains Mono',monospace; }
  ::-webkit-scrollbar{width:5px;height:5px}
  ::-webkit-scrollbar-track{background:transparent}
  ::-webkit-scrollbar-thumb{background:#3f3f46;border-radius:10px}
  ::-webkit-scrollbar-thumb:hover{background:#52525b}
  .commit-row:hover .row-bg { background: rgba(255,255,255,0.03); }
  .commit-row.selected .row-bg { background: rgba(168,85,247,0.08); }
  .lane-dot { transition: transform 0.12s ease; }
  .commit-row:hover .lane-dot { transform: translate(-50%,-50%) scale(1.4); }
  .commit-row.selected .lane-dot { transform: translate(-50%,-50%) scale(1.5); }
</style>
</head>
<body class="bg-[#0A0A0A] text-zinc-300 h-screen w-screen flex flex-col overflow-hidden antialiased selection:bg-purple-500/30 selection:text-purple-200">

<!-- Header -->
<header class="h-14 shrink-0 border-b border-white/[0.08] bg-[#0A0A0A]/80 backdrop-blur-md flex items-center justify-between px-4 z-20">
  <div class="flex items-center gap-3">
    <div class="flex items-center justify-center w-7 h-7 rounded bg-gradient-to-tr from-purple-600 to-blue-500 text-white shadow-lg shadow-purple-500/20">
      <i data-lucide="git-merge" class="w-4 h-4" stroke-width="1.5"></i>
    </div>
    <div class="flex items-center gap-2 text-sm">
      <span class="font-medium text-zinc-100">git-orchestrator</span>
      <span class="text-zinc-600">/</span>
      <div id="repo-badge" class="flex items-center gap-1.5 px-2 py-1 rounded-md bg-white/[0.04] border border-white/[0.08] text-zinc-400">
        <i data-lucide="cpu" class="w-3.5 h-3.5" stroke-width="1.5"></i>
        <span id="repo-name" class="font-mono text-xs"></span>
      </div>
      <div id="branch-badge" class="flex items-center gap-1.5 px-2 py-1 rounded-md bg-purple-500/[0.08] border border-purple-500/20 text-purple-400">
        <i data-lucide="git-branch" class="w-3.5 h-3.5" stroke-width="1.5"></i>
        <span id="branch-name" class="font-mono text-xs"></span>
      </div>
    </div>
  </div>
  <div class="flex items-center gap-4">
    <div id="status-chips" class="flex items-center gap-2"></div>
    <div class="flex items-center gap-2 text-xs text-zinc-500">
      <i data-lucide="clock" class="w-3.5 h-3.5" stroke-width="1.5"></i>
      <span id="last-ts">—</span>
    </div>
    <button id="refresh-btn" onclick="load()" class="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] transition-all text-sm font-medium text-zinc-200">
      <i data-lucide="refresh-cw" class="w-3.5 h-3.5" stroke-width="1.5" id="refresh-icon"></i>
      Refresh
    </button>
  </div>
</header>

<!-- Layout -->
<main class="flex-1 flex overflow-hidden">

  <!-- Left Sidebar -->
  <aside class="w-64 shrink-0 border-r border-white/[0.08] bg-[#0A0A0A] flex flex-col">
    <div class="flex-1 overflow-y-auto p-3 space-y-6">

      <!-- Team -->
      <div>
        <h3 class="text-xs font-medium text-zinc-500 uppercase tracking-widest px-2 mb-2">Team</h3>
        <div id="team-list" class="space-y-0.5"></div>
      </div>

      <!-- Branches -->
      <div>
        <h3 class="text-xs font-medium text-zinc-500 uppercase tracking-widest px-2 mb-2">Branches</h3>
        <div id="branch-list" class="space-y-0.5"></div>
      </div>

    </div>
  </aside>

  <!-- Center Graph -->
  <section class="flex-1 flex flex-col min-w-0 bg-[#0c0c0c] relative overflow-y-auto" id="graph-section">
    <div id="loading-overlay" class="absolute inset-0 flex items-center justify-center bg-[#0c0c0c] z-10 text-zinc-500 text-sm gap-2">
      <i data-lucide="loader-2" class="w-4 h-4 animate-spin" stroke-width="1.5"></i>
      Loading graph…
    </div>
    <div id="commit-rows" class="flex-1 py-4"></div>
  </section>

  <!-- Right Detail Panel -->
  <aside class="w-[340px] shrink-0 border-l border-white/[0.08] bg-[#0A0A0A] flex flex-col shadow-2xl">
    <div id="detail-empty" class="flex-1 flex flex-col items-center justify-center gap-3 text-zinc-600 text-sm px-6 text-center">
      <i data-lucide="git-commit-horizontal" class="w-8 h-8 opacity-30" stroke-width="1.5"></i>
      Click a commit to see details
    </div>
    <div id="detail-body" class="hidden flex-1 flex flex-col overflow-hidden">
      <div id="detail-content" class="p-6 flex-1 overflow-y-auto space-y-6"></div>
      <div class="p-4 border-t border-white/[0.04]">
        <a id="github-link" href="#" target="_blank" class="w-full py-2 px-4 rounded-md bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-sm font-medium text-zinc-200 transition-all flex items-center justify-center gap-2">
          <i data-lucide="external-link" class="w-4 h-4" stroke-width="1.5"></i>
          View on GitHub
        </a>
      </div>
    </div>
  </aside>

</main>

<script>
// ── Constants ─────────────────────────────────────────────────────────────────
const COLORS=['#a855f7','#3b82f6','#10b981','#f59e0b','#ef4444','#ec4899',
              '#06b6d4','#84cc16','#f97316','#8b5cf6','#14b8a6','#eab308'];
const LANE_PX=20, GRAPH_COL_W=96, ROW_H=56;
const NS='http://www.w3.org/2000/svg';

// ── State ─────────────────────────────────────────────────────────────────────
let gData=null, sData=null, selected=null;

// ── Load ──────────────────────────────────────────────────────────────────────
async function load(){
  const icon=document.getElementById('refresh-icon');
  icon.classList.add('animate-spin');
  try{
    const[g,s]=await Promise.all([
      fetch('/api/graph').then(r=>r.json()),
      fetch('/api/status').then(r=>r.json()),
    ]);
    gData=g; sData=s;
    document.getElementById('loading-overlay').style.display='none';
    renderHeader(); renderSidebar(); renderGraph();
  }catch(e){console.error(e);}
  finally{
    icon.classList.remove('animate-spin');
    const now=new Date();
    document.getElementById('last-ts').textContent=
      'Updated '+now.toLocaleTimeString();
    lucide.createIcons();
  }
}

// ── Header ───────────────────────────────────────────────────────────────────
function renderHeader(){
  setText('repo-name', sData.repo_name);
  setText('branch-name', sData.current_branch);
  const chips=document.getElementById('status-chips');
  chips.textContent='';
  const defs=[
    [sData.staged,    'staged',    'text-emerald-400 border-emerald-500/30 bg-emerald-500/10'],
    [sData.unstaged,  'modified',  'text-amber-400   border-amber-500/30   bg-amber-500/10'],
    [sData.untracked, 'untracked', 'text-blue-400    border-blue-500/30    bg-blue-500/10'],
  ];
  for(const[n,label,cls]of defs){
    if(!n) continue;
    const s=document.createElement('span');
    s.className=`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${cls}`;
    s.textContent=`${n} ${label}`;
    chips.append(s);
  }
}

// ── Sidebar ──────────────────────────────────────────────────────────────────
const avatarPalette=[
  'bg-cyan-950 border-cyan-800 text-cyan-400',
  'bg-rose-950 border-rose-800 text-rose-400',
  'bg-purple-950 border-purple-800 text-purple-400',
  'bg-amber-950 border-amber-800 text-amber-400',
  'bg-emerald-950 border-emerald-800 text-emerald-400',
];
function initials(n){ return n.trim().split(/\s+/).map(w=>w[0]||'').join('').slice(0,2).toUpperCase(); }
function avatarCls(n){ let h=0; for(const c of n) h=(h*31+c.charCodeAt(0))&0x7fffffff; return avatarPalette[h%avatarPalette.length]; }

function renderSidebar(){
  // Team
  const tl=document.getElementById('team-list');
  tl.textContent='';
  for(const m of gData.team){
    const btn=el('button','w-full flex items-center justify-between px-2 py-1.5 rounded-md hover:bg-white/[0.04] transition-colors group');
    const inner=el('div','flex items-center gap-2.5');
    const av=el('div',`w-6 h-6 rounded-full border flex items-center justify-center text-xs font-medium ${avatarCls(m.name)}`);
    av.textContent=initials(m.name);
    const info=el('div','flex flex-col items-start');
    const nm=el('span','text-sm text-zinc-300 group-hover:text-zinc-100 transition-colors');
    nm.textContent=m.name;
    const ct=el('span','text-xs text-zinc-500');
    ct.textContent=m.commits+' commit'+(m.commits!==1?'s':'');
    info.append(nm,ct); inner.append(av,info); btn.append(inner); tl.append(btn);
  }

  // Branches
  const bl=document.getElementById('branch-list');
  bl.textContent='';
  const branches=extractBranches();
  const cur=sData.current_branch;
  for(const b of branches){
    const isCur=b.name===cur||b.name==='origin/'+cur;
    const btn=el('button',`w-full flex items-center gap-2.5 px-2 py-1.5 rounded-md transition-colors relative ${isCur?'bg-purple-500/[0.08] text-purple-400':'hover:bg-white/[0.04] text-zinc-400 hover:text-zinc-200'}`);
    if(isCur){
      const accent=el('div','absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-4 bg-purple-500 rounded-r-full');
      btn.append(accent);
    }
    const dot=el('div',`w-2 h-2 rounded-full border-[1.5px] flex-shrink-0`);
    dot.style.borderColor=b.color;
    if(isCur){ dot.style.background=b.color+'33'; dot.style.boxShadow=`0 0 8px ${b.color}66`; }
    const nm=el('span','text-sm truncate font-medium');
    nm.textContent=b.name.replace('origin/','');
    btn.append(dot,nm);
    if(isCur){ const cur=el('span','text-xs text-zinc-500 ml-auto flex-shrink-0'); cur.textContent='current'; btn.append(cur); }
    bl.append(btn);
  }
}

function extractBranches(){
  const seen=new Map();
  for(const c of gData.commits) for(const r of c.refs) if(!seen.has(r)) seen.set(r,c.lane);
  return Array.from(seen.entries()).map(([name,lane])=>({name,lane,color:COLORS[lane%COLORS.length]}));
}

// ── Graph ─────────────────────────────────────────────────────────────────────
function laneX(lane){ return LANE_PX/2 + lane*LANE_PX; }

function computeThruLines(commits){
  /* For each row, which lanes have a vertical line passing through? */
  const active=[]; // active[l] = hash expected at lane l (or null)
  const thru=[]; // thru[i] = Set of lane indices

  for(let i=0;i<commits.length;i++){
    const t=new Set();
    for(let l=0;l<active.length;l++) if(active[l]!==null) t.add(l);
    thru.push(t);

    const short=commits[i].hash;
    let lane=active.indexOf(short);
    if(lane===-1){
      const slot=active.indexOf(null);
      if(slot!==-1){ lane=slot; active[lane]=short; }
      else{ active.push(short); lane=active.length-1; }
    }

    const parents=commits[i].parents;
    if(parents.length){ active[lane]=parents[0];
      for(const p of parents.slice(1))
        if(!active.includes(p)){
          const s=active.indexOf(null);
          if(s!==-1) active[s]=p; else active.push(p);
        }
    } else { active[lane]=null; }
  }
  return thru;
}

function renderGraph(){
  const commits=gData.commits;
  const rows=document.getElementById('commit-rows');
  rows.textContent='';
  if(!commits.length){ const p=el('p','text-zinc-600 text-sm p-8'); p.textContent='No commits found.'; rows.append(p); return; }

  const hashIdx={};
  commits.forEach((c,i)=>hashIdx[c.hash]=i);
  const thruLines=computeThruLines(commits);

  for(let i=0;i<commits.length;i++){
    const c=commits[i];
    const isSel=selected===c.hash;
    const color=COLORS[c.lane%COLORS.length];
    const maxLane=Math.max(...[...thruLines[i]].concat([c.lane]));
    const svgW=Math.max(GRAPH_COL_W, laneX(maxLane)+LANE_PX/2+4);

    // Row container
    const row=el('div',`commit-row group relative flex items-stretch cursor-pointer border-b border-white/[0.04] h-14${isSel?' selected':''}`);
    row.addEventListener('click',()=>selectCommit(c.hash));

    // Background highlight layer
    const bg=el('div','row-bg absolute inset-0 transition-colors');
    row.append(bg);

    // Graph SVG column
    const graphCol=el('div','relative shrink-0 z-[1]');
    graphCol.style.width=svgW+'px';

    const svg=svgEl('svg',{width:svgW,height:ROW_H});
    const dotX=laneX(c.lane);
    const dotY=ROW_H/2;

    // Vertical through-lines
    for(const l of thruLines[i]){
      const lx=laneX(l); const lc=COLORS[l%COLORS.length];
      svg.append(svgEl('line',{x1:lx,y1:0,x2:lx,y2:ROW_H,stroke:lc,'stroke-width':1.5,opacity:.3}));
    }

    // Bezier curves to parents (different lane)
    for(let pi=0;pi<c.parents.length;pi++){
      const ph=c.parents[pi];
      const pi2=hashIdx[ph];
      if(pi2===undefined) continue;
      const pc=commits[pi2];
      if(pc.lane===c.lane) continue; // same lane → already covered by vertical
      const px2=laneX(pc.lane);
      const edgeColor=pi===0?color:COLORS[pc.lane%COLORS.length];
      // Curve from dot to bottom edge toward parent lane
      const midY=ROW_H*0.85;
      svg.append(svgEl('path',{
        d:`M${dotX},${dotY} C${dotX},${midY} ${px2},${midY} ${px2},${ROW_H}`,
        fill:'none',stroke:edgeColor,'stroke-width':1.5,opacity:.4}));
    }

    // Glow filter for selected
    if(isSel){
      const defs=svgEl('defs');
      const filter=svgEl('filter',{id:'glow'});
      const blur=svgEl('feGaussianBlur',{stdDeviation:'3',result:'coloredBlur'});
      const merge=svgEl('feMerge');
      merge.append(svgEl('feMergeNode',{in:'coloredBlur'}),svgEl('feMergeNode',{in:'SourceGraphic'}));
      filter.append(blur,merge); defs.append(filter); svg.append(defs);
    }

    // Dot
    const ring=svgEl('circle',{cx:dotX,cy:dotY,r:8,fill:'#0c0c0c'});
    const dot=svgEl('circle',{cx:dotX,cy:dotY,r:isSel?6:5,
      fill:isSel?color:'#0c0c0c',
      stroke:color,'stroke-width':isSel?2:1.5,
      ...(isSel?{filter:'url(#glow)'}:{})});
    dot.classList.add('lane-dot');
    dot.style.transformOrigin=`${dotX}px ${dotY}px`;
    svg.append(ring,dot);
    graphCol.append(svg);

    // Content column
    const content=el('div','flex-1 flex items-center pr-6 min-w-0 opacity-80 group-hover:opacity-100 transition-opacity z-[1]');
    if(isSel) content.classList.replace('opacity-80','opacity-100');

    // Branch pills
    if(c.refs.length){
      const pills=el('div','flex items-center gap-1.5 mr-3 shrink-0');
      for(const ref of c.refs){
        const pill=el('span','inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border');
        pill.textContent=ref.replace('origin/','');
        pill.style.cssText=`color:${color};border-color:${color}33;background:${color}18`;
        pills.append(pill);
      }
      content.append(pills);
    }

    // Message
    const msg=el('span','text-sm truncate flex-1 transition-colors');
    msg.textContent=truncate(c.subject,52);
    msg.style.color=isSel?'#f4f4f5':'#a1a1aa';
    content.append(msg);

    // Right meta
    const meta=el('div','flex flex-col items-end shrink-0 ml-4');
    if(c.author_name){
      const an=el('span','text-xs transition-colors');
      an.style.color='#71717a'; an.textContent=c.author_name; meta.append(an);
    }
    const dt=el('span','text-xs text-zinc-600');
    dt.textContent=relDate(c.date); meta.append(dt);
    content.append(meta);

    row.append(graphCol,content);
    rows.append(row);
  }
}

// ── Detail Panel (DOM API, no innerHTML on data) ──────────────────────────────
function selectCommit(hash){
  selected=hash;
  const c=gData.commits.find(x=>x.hash===hash);
  if(!c) return;
  renderGraph(); // refresh selection

  document.getElementById('detail-empty').classList.add('hidden');
  const body=document.getElementById('detail-body');
  body.classList.remove('hidden'); body.classList.add('flex');

  const color=COLORS[c.lane%COLORS.length];
  const dc=document.getElementById('detail-content');
  dc.textContent='';

  // Title
  const title=el('h2','text-xl font-medium tracking-tight text-zinc-100 leading-snug');
  title.textContent=c.subject; dc.append(title);

  // Refs
  if(c.refs.length){
    const refs=el('div','flex flex-wrap gap-2');
    for(const r of c.refs){
      const pill=el('span','inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border');
      const icon=document.createElement('i');
      icon.setAttribute('data-lucide','git-branch');
      icon.className='w-3.5 h-3.5 mr-1.5';
      icon.setAttribute('stroke-width','1.5');
      pill.append(icon);
      const t=document.createTextNode(r.replace('origin/',''));
      pill.append(t);
      pill.style.cssText=`color:${color};border-color:${color}33;background:${color}18`;
      refs.append(pill);
    }
    dc.append(refs);
  }

  // Metadata
  const metaSection=el('div','space-y-4');
  const metaTitle=el('h3','text-xs font-medium text-zinc-500 uppercase tracking-widest mb-4');
  metaTitle.textContent='Metadata'; metaSection.append(metaTitle);

  const grid=el('div','grid gap-x-2 gap-y-4 items-start');
  grid.style.gridTemplateColumns='80px 1fr';

  const rows=[
    ['Hash',   c.full_hash, true],
    ['Author', c.author_name, false],
    ['Email',  c.author_email, true],
    ['Date',   c.date?new Date(c.date).toLocaleString():'—', false],
  ];
  for(const[lbl,val,mono]of rows){
    const l=el('div','text-sm text-zinc-500 pt-0.5'); l.textContent=lbl;
    const v=el('div',`text-sm text-zinc-300${mono?' font-mono break-all':''}`); v.textContent=val;
    grid.append(l,v);
  }

  if(c.parents.length){
    const l=el('div','text-sm text-zinc-500 pt-0.5');
    l.textContent='Parent'+(c.parents.length>1?'s':'');
    const v=el('div','flex flex-col gap-1.5');
    for(const p of c.parents){
      const a=el('span','text-sm font-mono text-blue-400 hover:text-blue-300 hover:underline underline-offset-2 transition-colors cursor-pointer w-fit');
      a.textContent=p; a.addEventListener('click',()=>selectCommit(p));
      v.append(a);
    }
    grid.append(l,v);
  }

  metaSection.append(grid); dc.append(metaSection);

  // GitHub link
  const repoMatch=sData.repo_name;
  document.getElementById('github-link').href=
    `https://github.com/Ferie-Vincent/${repoMatch}/commit/${c.full_hash}`;

  lucide.createIcons();
}

// ── Utils ─────────────────────────────────────────────────────────────────────
function el(tag,cls=''){
  const e=document.createElement(tag);
  if(cls) e.className=cls;
  return e;
}
function svgEl(tag,attrs={}){
  const e=document.createElementNS(NS,tag);
  for(const[k,v]of Object.entries(attrs)) e.setAttribute(k,String(v));
  return e;
}
function setText(id,v){ const e=document.getElementById(id); if(e) e.textContent=v; }
function truncate(s,n){ return s.length>n?s.slice(0,n)+'…':s; }
function relDate(iso){
  if(!iso) return '—';
  const d=new Date(iso),ms=new Date()-d,h=ms/36e5;
  if(h<1)  return Math.round(ms/60000)+'m ago';
  if(h<24) return Math.round(h)+'h ago';
  const dd=Math.round(h/24);
  if(dd<30)return dd+'d ago';
  return d.toLocaleDateString();
}

// ── Boot ──────────────────────────────────────────────────────────────────────
lucide.createIcons();
load();
setInterval(load,30000);
</script>
</body>
</html>
"""
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
