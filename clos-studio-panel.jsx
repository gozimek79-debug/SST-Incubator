import React, { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ErrorBar, Cell,
} from "recharts";

/*
  CLOS STUDIO — Panel Badacza
  ---------------------------
  Jedno okno, nawigacja boczna, wszystkie wyniki + raporty bez przelaczania okien.
  Dane ponizej (DATA) to zweryfikowany stan gałęzi v0.7.2-scientific-integrity @ 10470e8.
  Aby podpiac na zywo: zastap pola DATA fetchem z repo:
    reports/academy/L1_1_pattern_echo.json, publications/competency_profile.json,
    publications/L1_1_pattern_echo/metadata.json.
*/

const C = {
  bg:"#0C0F14", panel:"#12161D", raised:"#171C25", line:"#232B36",
  txt:"#E8EDF3", mut:"#78879A", chA:"#4FC8E0", chB:"#A98CFF",
  ok:"#5FC98C", warn:"#F2B049", crit:"#F0655A",
};

const DATA = {
  project: { name:"SST Incubator · CLOS", status:"Research Grade Infrastructure",
    branch:"v0.7.2-scientific-integrity", head:"10470e8", clos:"0.8.4" },
  vitals: { tests:263, ci:"green", coreFrozen:true, lessons:1,
    competencyMeasured:6, competencyValid:4, competencyTotal:13 },
  sprint:[
    {c:"91e4766",p:"P2",t:"L1.1 → noise_world (koniec pseudoreplikacji)"},
    {c:"b2a8383",p:"P1",t:"Bundle L1.1 z pełną prowenancją, legacy otagowane"},
    {c:"8699ffb",p:"P3",t:"CI + walidatory (test negatywny)"},
    {c:"2f7af6b",p:"P4.1",t:"cognitive_ontology.md (13 pojęć)"},
    {c:"954b1f8",p:"P4.2",t:"Capability Analyzer"},
    {c:"ddedf70",p:"P4.3",t:"Competency Profile + karty genomów"},
    {c:"b56d982",p:"P5+P6",t:"README/ROADMAP, spec partial_step()"},
    {c:"10470e8",p:"—",t:"Raport końcowy sprintu"},
  ],
  lesson:{
    id:"L1.1", name:"Pattern Echo",
    hypothesis:"Brain utrzymuje reprezentację wzorca po usunięciu bodźca (pamięć robocza).",
    scenario:"noise_world", control:"stable_world",
    primary:"MSE @ 50 ticków po usunięciu bodźca", pass:"MSE@50 < 0.5", result:"PASS",
    seeds:10,
    genomes:[
      {g:"default_v1", ch:C.chA, mean:0.156712, lo:0.124980, hi:0.188444, nEff:10, valid:true},
      {g:"highly_plastic_v1", ch:C.chB, mean:0.173229, lo:0.142390, hi:0.204068, nEff:10, valid:true},
    ],
  },
  competency:[
    {k:"Perception", s:"insufficient"},
    {k:"Attention", s:"insufficient"},
    {k:"Pattern Recognition", s:"valid", lesson:"L1.1", d:-0.050008,
      A:{v:0.151568,lo:0.133546,hi:0.169591,n:10}, B:{v:0.150072,lo:0.131021,hi:0.169123,n:10}},
    {k:"Pattern Retention", s:"valid", lesson:"L1.1", d:0.276125,
      A:{v:-0.000097,lo:-0.000515,hi:0.000322,n:10}, B:{v:0.000098,lo:-0.000357,hi:0.000554,n:10}},
    {k:"Working Memory", s:"valid", lesson:"L1.1", d:0.327187, primary:true,
      A:{v:0.156712,lo:0.124980,hi:0.188444,n:10}, B:{v:0.173229,lo:0.142390,hi:0.204068,n:10}},
    {k:"Long-term Memory", s:"insufficient"},
    {k:"Prediction", s:"insufficient"},
    {k:"Adaptation", s:"degenerate", lesson:"L1.1",
      A:{v:0.0,n:1}, B:{v:0.0,n:1}, note:"identyczne dla 10 seedów — brak wariancji"},
    {k:"Exploration", s:"insufficient", note:"brak mechanizmu w kodzie (act() = echo v0.1)"},
    {k:"Generalization", s:"insufficient"},
    {k:"Planning", s:"insufficient", note:"brak mechanizmu w kodzie"},
    {k:"Stability", s:"degenerate", lesson:"L1.1",
      A:{v:0.0,n:1}, B:{v:0.0,n:1}, note:"identyczne dla 10 seedów — brak wariancji"},
    {k:"Energy Efficiency", s:"valid", lesson:"L1.1", d:-8.701052,
      A:{v:0.460800,lo:0.456304,hi:0.465296,n:6}, B:{v:0.413800,lo:0.412316,hi:0.415284,n:3}},
  ],
  provenance:{
    experiment_id:"L1_1_pattern_echo",
    git_commit:"91e47669a82774b9b27fbebbd2c4e7f23e6dfdf9",
    config_hash:"0d786263b9e5be55ec5f4aae19a3d5a536e315325bdcdabfbde63007e598a290",
    manifest_hash:"ffdff9844f94da57405549a56e9277e40a672f26448a3fa971c4e1203ee44a94",
    timestamp:"2026-07-08T21:46:32", clos_version:"0.8.4", total_runs:40, reproducible:true,
    legacy:["EXP-1C290805","EXP-3A59D747","EXP-89D9BA69","EXP-8C696B3C"],
  },
  ci:{
    runs:[{c:"8699ffb",r:"success"},{c:"ddedf70",r:"success"},{c:"10470e8",r:"success"}],
    validators:[{n:"validate_publication",r:"OK (5 bundli)"},{n:"validate_artifacts",r:"OK (1 raport)"}],
  },
  reports:[
    {f:"RAPORT_KONCOWY_v0.8.4.md", d:"Raport końcowy sprintu — uczciwa ocena gotowości"},
    {f:"publications/preregistration_L1_1.json", d:"Prerejestracja L1.1 (noise_world)"},
    {f:"publications/competency_profile.md", d:"Profil kompetencji + karty genomów"},
    {f:"clos_academy/cognitive_ontology.md", d:"Ontologia — 13 pojęć poznawczych"},
    {f:"docs/spec_partial_step.md", d:"Specyfikacja partial_step() (pod v0.9)"},
  ],
};

const SECTIONS = [
  {id:"overview", label:"Przegląd"},
  {id:"lessons", label:"Lekcje i wyniki"},
  {id:"competency", label:"Profil kompetencji"},
  {id:"genomes", label:"Porównanie genomów"},
  {id:"provenance", label:"Prowenancja"},
  {id:"tests", label:"Testy i CI"},
  {id:"reports", label:"Raporty"},
];

const sfx = (s) => ({valid:C.ok, degenerate:C.warn, insufficient:C.mut}[s]);
const slabel = (s) => ({valid:"zmierzone", degenerate:"zdegenerowane", insufficient:"brak danych"}[s]);

function Pill({color, children, dot}) {
  return <span className="pill" style={{color, borderColor:color+"55"}}>
    {dot && <i className="pdot" style={{background:color}}/>}{children}</span>;
}
function Card({title, sub, children, span}) {
  return <section className={`card ${span?"span":""}`}>
    <header className="card-h"><span className="card-t">{title}</span>
      {sub && <span className="card-s">{sub}</span>}</header>
    <div className="card-b">{children}</div></section>;
}

/* ---------- sections ---------- */
function Overview() {
  const v = DATA.vitals;
  const tiles = [
    {l:"Status", val:"RGI", sub:"Research Grade", c:C.chA},
    {l:"Testy", val:`${v.tests}`, sub:"passed", c:C.ok},
    {l:"CI", val:"green", sub:"per-commit", c:C.ok, dot:true},
    {l:"Core", val:"frozen", sub:"0 diff vs baseline", c:C.chA},
    {l:"Lekcje", val:`${v.lessons}`, sub:"L1.1 Pattern Echo", c:C.txt},
    {l:"Kompetencje", val:`${v.competencyValid}/${v.competencyTotal}`, sub:`ważne CI95 · ${v.competencyMeasured} zmierzone`, c:C.warn},
  ];
  return <>
    <div className="tiles">{tiles.map(t=>(
      <div key={t.l} className="tile">
        <div className="tile-l">{t.l}</div>
        <div className="tile-v" style={{color:t.c}}>{t.dot&&<i className="pdot" style={{background:t.c}}/>}{t.val}</div>
        <div className="tile-s">{t.sub}</div>
      </div>))}</div>
    <Card title="Sprint v0.8.4" sub="8 commitów · integralność infrastruktury" span>
      <div className="timeline">{DATA.sprint.map(s=>(
        <div key={s.c} className="tl-row">
          <code className="tl-c">{s.c}</code>
          <span className="tl-p">{s.p}</span>
          <span className="tl-t">{s.t}</span>
        </div>))}</div>
    </Card>
    <Card title="Ocena" span>
      <p className="prose">Infrastruktura (CI, prowenancja, metrologia, ontologia, walidatory) jest
      solidna i zweryfikowana niezależnie. Zawartość naukowa jest wąska: <b>jedna lekcja</b>,
      <b> 4 z 13 kompetencji</b> z niezdegenerowanym CI95. To zamierzone i uczciwe — nie należy
      tego mylić z gotowym systemem poznawczym.</p>
    </Card>
  </>;
}

function Lessons() {
  const L = DATA.lesson;
  const chart = L.genomes.map(g=>({name:g.g.replace("_v1",""), mean:g.mean,
    err:[g.mean-g.lo, g.hi-g.mean], color:g.ch}));
  return <>
    <Card title={`${L.id} — ${L.name}`} sub={`${L.scenario} · kontrola: ${L.control}`} span>
      <p className="prose"><b>Hipoteza.</b> {L.hypothesis}</p>
      <div className="kv">
        <div><span>Primary endpoint</span><b>{L.primary}</b></div>
        <div><span>Kryterium</span><b>{L.pass}</b></div>
        <div><span>Seedy / genom</span><b>{L.seeds}</b></div>
        <div><span>Wynik</span><Pill color={C.ok} dot>{L.result}</Pill></div>
      </div>
    </Card>
    <Card title="MSE @ 50 · średnia ± CI95" sub="oba genomy — realna wariancja (noise_world)" span>
      <div style={{height:210}}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chart} margin={{top:12,right:16,left:-8,bottom:6}}>
            <CartesianGrid stroke={C.line} strokeDasharray="2 4"/>
            <XAxis dataKey="name" stroke={C.mut} tick={{fill:C.mut,fontSize:12,fontFamily:"IBM Plex Mono,monospace"}}/>
            <YAxis stroke={C.mut} domain={[0,0.28]} tick={{fill:C.mut,fontSize:11,fontFamily:"IBM Plex Mono,monospace"}}/>
            <Tooltip contentStyle={{background:C.raised,border:`1px solid ${C.line}`,borderRadius:6,
              fontFamily:"IBM Plex Mono,monospace",fontSize:12,color:C.txt}}/>
            <Bar dataKey="mean" radius={[4,4,0,0]}>
              {chart.map((e,i)=><Cell key={i} fill={e.color} fillOpacity={0.85}/>)}
              <ErrorBar dataKey="err" stroke={C.txt} strokeWidth={1.5} width={6}/>
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="note">Kontrola <code>stable_world</code> jest deterministyczna (n_eff=1, CI95 nie dotyczy) —
      punkt odniesienia, nie źródło wariancji.</p>
    </Card>
  </>;
}

function Competency() {
  const measured = DATA.competency.filter(c=>c.s!=="insufficient").length;
  const valid = DATA.competency.filter(c=>c.s==="valid").length;
  const scale = (x) => Math.min(100, Math.abs(x)/0.5*100); // 0..0.5 range for bars
  return <Card title="Instrument kompetencji" span
    sub={`zmierzone ${measured}/13 · ważne CI95 ${valid}/13 — luki są jawne, nie ukryte`}>
    <div className="comp">
      {DATA.competency.map(c=>(
        <div key={c.k} className={`crow ${c.s}`}>
          <div className="crow-head">
            <span className="crow-k">{c.k}{c.primary && <em className="prim">primary</em>}</span>
            <Pill color={sfx(c.s)}>{slabel(c.s)}{c.lesson?` · ${c.lesson}`:""}</Pill>
          </div>
          {c.s==="valid" && (
            <div className="crow-body">
              {[["A",c.A],["B",c.B]].map(([kk,gg])=>{
                const col = kk==="A"?C.chA:C.chB;
                return <div key={kk} className="gbar">
                  <span className="gbar-lbl" style={{color:col}}>{kk==="A"?"default":"plastic"}</span>
                  <div className="gbar-track">
                    <div className="gbar-fill" style={{width:`${scale(gg.v)}%`,background:col}}/>
                  </div>
                  <code className="gbar-val">{gg.v.toFixed(4)}</code>
                  <code className="gbar-ci">CI [{gg.lo.toFixed(3)},{gg.hi.toFixed(3)}]</code>
                </div>;
              })}
              {c.d!=null && <div className="crow-d">Cohen&apos;s d (genom vs genom): <code>{c.d.toFixed(3)}</code></div>}
            </div>
          )}
          {c.s==="degenerate" && (
            <div className="crow-warn">⚠ {c.note} · <code>n_eff=1</code>, <code>ci95_valid=false</code> — policzone, ale bez informacji o wariancji</div>
          )}
          {c.s==="insufficient" && (
            <div className="crow-gap">brak lekcji{c.note?` · ${c.note}`:" mierzącej to pojęcie"}</div>
          )}
        </div>
      ))}
    </div>
  </Card>;
}

function Genomes() {
  const rows = DATA.competency.filter(c=>c.s==="valid");
  return <Card title="default_v1 vs highly_plastic_v1" span
    sub="tylko pojęcia z ważnym CI95 · effect size między genomami">
    <table className="tbl">
      <thead><tr><th>Pojęcie</th><th>default</th><th>highly_plastic</th><th>Δ śr.</th><th>Cohen&apos;s d</th></tr></thead>
      <tbody>{rows.map(c=>(
        <tr key={c.k}>
          <td>{c.k}</td>
          <td><code style={{color:C.chA}}>{c.A.v.toFixed(4)}</code></td>
          <td><code style={{color:C.chB}}>{c.B.v.toFixed(4)}</code></td>
          <td><code>{(c.B.v-c.A.v).toFixed(4)}</code></td>
          <td><code style={{color:Math.abs(c.d)>0.8?C.warn:C.txt}}>{c.d.toFixed(3)}</code></td>
        </tr>))}</tbody>
    </table>
    <p className="note">Porównanie opiera się na <b>jednej</b> lekcji (L1.1). Duże |d| przy Energy
    Efficiency wynika z bardzo małej wariancji wewnątrz genomu (n_eff 6/3), nie z dużej różnicy bezwzględnej — interpretować ostrożnie.</p>
  </Card>;
}

function Provenance() {
  const p = DATA.provenance;
  const trunc = (h)=>h.slice(0,12)+"…"+h.slice(-6);
  return <>
    <Card title="Bundle L1.1 — prowenancja" sub="odtwarzalność eksperymentu" span>
      <dl className="prov">
        <div><dt>experiment_id</dt><dd>{p.experiment_id}</dd></div>
        <div><dt>git_commit</dt><dd>{p.git_commit.slice(0,12)}…</dd></div>
        <div><dt>config_hash</dt><dd>{trunc(p.config_hash)}</dd></div>
        <div><dt>manifest_hash</dt><dd>{trunc(p.manifest_hash)}</dd></div>
        <div><dt>timestamp</dt><dd>{p.timestamp.replace("T"," ")}</dd></div>
        <div><dt>total_runs</dt><dd>{p.total_runs}</dd></div>
        <div><dt>clos_version</dt><dd>{p.clos_version}</dd></div>
        <div><dt>reproducible</dt><dd style={{color:C.ok}}>✓ true</dd></div>
      </dl>
    </Card>
    <Card title="Bundle legacy (pre-0.7.2)" sub="oznaczone, prowenancja nie fabrykowana" span>
      <div className="legacy">{p.legacy.map(l=>(
        <div key={l} className="leg-row"><code>{l}</code>
          <Pill color={C.mut}>legacy-pre-0.7.2</Pill>
          <span className="leg-note">git_commit: pusty (nie zgadywany)</span></div>))}</div>
    </Card>
  </>;
}

function Tests() {
  return <>
    <div className="tiles">
      <div className="tile"><div className="tile-l">pytest</div>
        <div className="tile-v" style={{color:C.ok}}>{DATA.vitals.tests}</div><div className="tile-s">passed</div></div>
      <div className="tile"><div className="tile-l">Core</div>
        <div className="tile-v" style={{color:C.chA}}>frozen</div><div className="tile-s">0 diff vs baseline</div></div>
      <div className="tile"><div className="tile-l">CI</div>
        <div className="tile-v" style={{color:C.ok}}><i className="pdot" style={{background:C.ok}}/>green</div><div className="tile-s">GitHub Actions</div></div>
    </div>
    <Card title="Przebiegi CI (per-commit)" sub="zweryfikowane przez API — conclusion=success" span>
      <div className="legacy">{DATA.ci.runs.map(r=>(
        <div key={r.c} className="leg-row"><code>{r.c}</code>
          <Pill color={C.ok} dot>{r.r}</Pill></div>))}</div>
    </Card>
    <Card title="Walidatory (bramka jakości)" sub="uruchamiane w CI na każdy push" span>
      <div className="legacy">{DATA.ci.validators.map(v=>(
        <div key={v.n} className="leg-row"><code>{v.n}</code>
          <Pill color={C.ok}>{v.r}</Pill></div>))}</div>
      <p className="note">Oba przetestowane negatywnie: wymuszony błąd → exit 1. Wykrywają rozjazd, nie tylko zwracają OK.</p>
    </Card>
  </>;
}

function Reports() {
  return <Card title="Artefakty i raporty" sub="w repo · na gałęzi v0.7.2-scientific-integrity" span>
    <div className="reports">{DATA.reports.map(r=>(
      <div key={r.f} className="rep-row">
        <code className="rep-f">{r.f}</code>
        <span className="rep-d">{r.d}</span>
      </div>))}</div>
    <p className="note">W wersji podpiętej do repo każdy wiersz staje się linkiem otwierającym artefakt.</p>
  </Card>;
}

const VIEWS = {overview:<Overview/>, lessons:<Lessons/>, competency:<Competency/>,
  genomes:<Genomes/>, provenance:<Provenance/>, tests:<Tests/>, reports:<Reports/>};

export default function CLOSStudio() {
  const [sec, setSec] = useState("overview");
  return <div className="studio">
    <style>{css}</style>
    <header className="top">
      <div className="brand"><span className="bdot"/>CLOS STUDIO
        <span className="brand-sub">Panel Badacza</span></div>
      <div className="top-r">
        <Pill color={C.chA}>{DATA.project.status}</Pill>
        <Pill color={C.mut}>{DATA.project.branch}@{DATA.project.head}</Pill>
        <Pill color={C.ok} dot>CI</Pill>
      </div>
    </header>
    <div className="body">
      <nav className="side" aria-label="Sekcje panelu">
        {SECTIONS.map(s=>(
          <button key={s.id} className={`nav ${sec===s.id?"on":""}`}
            onClick={()=>setSec(s.id)} aria-current={sec===s.id}>{s.label}</button>))}
      </nav>
      <main className="main">
        <div className="main-h">{SECTIONS.find(s=>s.id===sec).label}</div>
        <div className="grid">{VIEWS[sec]}</div>
      </main>
    </div>
    <footer className="foot">Dane: v0.7.2-scientific-integrity @ 10470e8 · zweryfikowane niezależnie.
    Podłączenie na żywo: fetch z reports/academy/ i publications/.</footer>
  </div>;
}

const css = `
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
.studio{--bg:${C.bg};--panel:${C.panel};--raised:${C.raised};--line:${C.line};--txt:${C.txt};--mut:${C.mut};--chA:${C.chA};--chB:${C.chB};--ok:${C.ok};--warn:${C.warn};--crit:${C.crit};
  background:var(--bg);color:var(--txt);min-height:100vh;font-family:'Space Grotesk',system-ui,sans-serif}
.studio *{box-sizing:border-box}
code{font-family:'IBM Plex Mono',monospace}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 20px;border-bottom:1px solid var(--line);background:var(--panel);flex-wrap:wrap}
.brand{font-size:18px;font-weight:700;letter-spacing:.06em;display:flex;align-items:center;gap:10px}
.bdot{width:9px;height:9px;border-radius:50%;background:var(--chA);box-shadow:0 0 10px var(--chA);animation:pulse 2.6s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.brand-sub{font-size:12px;font-weight:500;color:var(--mut);letter-spacing:.02em}
.top-r{display:flex;gap:8px;flex-wrap:wrap}
.pill{font-family:'IBM Plex Mono',monospace;font-size:10.5px;padding:3px 9px;border:1px solid;border-radius:20px;display:inline-flex;align-items:center;gap:6px;white-space:nowrap}
.pdot{width:6px;height:6px;border-radius:50%;display:inline-block;box-shadow:0 0 6px currentColor;animation:pulse 2s ease-in-out infinite}
.body{display:flex;min-height:calc(100vh - 106px)}
.side{width:190px;flex-shrink:0;border-right:1px solid var(--line);background:var(--panel);padding:14px 10px;display:flex;flex-direction:column;gap:3px}
.nav{text-align:left;background:none;border:none;color:var(--mut);font-family:inherit;font-size:13.5px;padding:9px 12px;border-radius:7px;cursor:pointer;transition:.15s;border-left:2px solid transparent}
.nav:hover{color:var(--txt);background:var(--raised)}
.nav.on{color:var(--txt);background:var(--raised);border-left-color:var(--chA)}
.nav:focus-visible{outline:2px solid var(--chA);outline-offset:1px}
.main{flex:1;padding:20px;min-width:0}
.main-h{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--mut);margin-bottom:14px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.card.span{grid-column:1/-1}
.card-h{display:flex;justify-content:space-between;align-items:baseline;gap:10px;padding:12px 16px;border-bottom:1px solid var(--line);background:var(--raised);flex-wrap:wrap}
.card-t{font-weight:600;font-size:14px}
.card-s{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--mut)}
.card-b{padding:16px}
.prose{font-size:13.5px;line-height:1.6;color:var(--txt);margin:0}
.prose b{color:var(--txt)}
.note{font-size:11.5px;color:var(--mut);line-height:1.55;margin:12px 0 0}
.note code,.prose code{color:var(--chA);font-size:11px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:14px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.tile-l{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--mut)}
.tile-v{font-family:'IBM Plex Mono',monospace;font-size:26px;font-weight:600;line-height:1.15;margin:6px 0 2px;display:flex;align-items:center;gap:8px}
.tile-s{font-size:11px;color:var(--mut)}
.timeline{display:flex;flex-direction:column}
.tl-row{display:grid;grid-template-columns:80px 54px 1fr;gap:12px;align-items:center;padding:8px 0;border-bottom:1px solid var(--line);font-size:13px}
.tl-row:last-child{border-bottom:none}
.tl-c{color:var(--mut);font-size:12px}
.tl-p{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--chA)}
.tl-t{color:var(--txt)}
.kv{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-top:14px}
.kv div{display:flex;flex-direction:column;gap:3px}
.kv span{font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--mut)}
.kv b{font-size:14px;font-weight:500}
.comp{display:flex;flex-direction:column;gap:8px}
.crow{border:1px solid var(--line);border-radius:8px;padding:11px 13px;border-left:3px solid var(--line);background:var(--raised)}
.crow.valid{border-left-color:var(--ok)}
.crow.degenerate{border-left-color:var(--warn)}
.crow.insufficient{opacity:.62}
.crow-head{display:flex;justify-content:space-between;align-items:center;gap:10px}
.crow-k{font-weight:500;font-size:13.5px;display:flex;align-items:center;gap:8px}
.prim{font-family:'IBM Plex Mono',monospace;font-size:9px;color:var(--chA);border:1px solid var(--chA);border-radius:3px;padding:1px 5px;font-style:normal}
.crow-body{margin-top:10px;display:flex;flex-direction:column;gap:6px}
.gbar{display:grid;grid-template-columns:56px 1fr auto auto;gap:10px;align-items:center}
.gbar-lbl{font-family:'IBM Plex Mono',monospace;font-size:11px}
.gbar-track{height:8px;background:var(--bg);border:1px solid var(--line);border-radius:4px;overflow:hidden}
.gbar-fill{height:100%;border-radius:4px;min-width:2px;opacity:.8}
.gbar-val{font-size:12px;color:var(--txt)}
.gbar-ci{font-size:10px;color:var(--mut)}
.crow-d{font-size:11px;color:var(--mut);margin-top:2px}
.crow-d code{color:var(--txt)}
.crow-warn{margin-top:8px;font-size:11.5px;color:var(--warn);line-height:1.5}
.crow-warn code{color:var(--warn)}
.crow-gap{margin-top:6px;font-size:11.5px;color:var(--mut)}
.tbl{width:100%;border-collapse:collapse;font-size:13px}
.tbl th{text-align:left;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--mut);padding:8px 10px;border-bottom:1px solid var(--line);font-weight:500}
.tbl td{padding:9px 10px;border-bottom:1px solid var(--line)}
.tbl code{font-size:12px}
.prov{display:grid;grid-template-columns:repeat(2,1fr);gap:12px 20px;margin:0}
.prov div{display:flex;flex-direction:column;gap:2px}
.prov dt{font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--mut)}
.prov dd{margin:0;font-family:'IBM Plex Mono',monospace;font-size:12.5px}
.legacy{display:flex;flex-direction:column;gap:8px}
.leg-row{display:flex;align-items:center;gap:12px;flex-wrap:wrap;font-size:13px}
.leg-row code{font-size:12.5px}
.leg-note{font-size:11px;color:var(--mut)}
.reports{display:flex;flex-direction:column}
.rep-row{display:flex;gap:14px;align-items:baseline;padding:10px 0;border-bottom:1px solid var(--line);flex-wrap:wrap}
.rep-row:last-child{border-bottom:none}
.rep-f{font-size:12.5px;color:var(--chA);min-width:230px}
.rep-d{font-size:13px;color:var(--txt)}
.foot{padding:14px 20px;border-top:1px solid var(--line);font-family:'IBM Plex Mono',monospace;font-size:10.5px;color:var(--mut);text-align:center;background:var(--panel)}
@media(max-width:820px){
  .body{flex-direction:column}
  .side{width:100%;flex-direction:row;overflow-x:auto;border-right:none;border-bottom:1px solid var(--line)}
  .nav{white-space:nowrap;border-left:none;border-bottom:2px solid transparent}
  .nav.on{border-left:none;border-bottom-color:var(--chA)}
  .grid{grid-template-columns:1fr}
  .prov{grid-template-columns:1fr}
}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
`;
