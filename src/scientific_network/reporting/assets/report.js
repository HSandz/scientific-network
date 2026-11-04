(() => {
  'use strict';
  const D = JSON.parse(document.getElementById('report-data').textContent);
  const $ = id => document.getElementById(id);
  const fmt = n => Number(n).toLocaleString('en-US');
  const nodes = new Map(D.nodes.map(n => [n.id, n]));
  const edges = new Map(D.edges.map(e => [e.edge_id, e]));
  const colors = {Paper:'#9aa5b1', Researcher:'#1d5fbf', Organization:'#167a72', Topic:'#8a6a18', Venue:'#15191d'};
  const predicates = ['AUTHORED','AFFILIATED_WITH','PUBLISHED_IN','CITES','HAS_TOPIC','SUBTOPIC_OF','COAUTHORED_WITH','COLLABORATED_WITH','RESEARCHES_TOPIC','CONTRIBUTES_TO_TOPIC'];
  const classes = ['observed','observed','observed','observed','inferred topic','curated taxonomy','derived','derived','derived','derived'];
  const factual = new Set(predicates.slice(0,4));
  const adjacency = new Map(D.nodes.map(n => [n.id, []]));
  D.edges.forEach(e => { adjacency.get(e.source_id).push(e); adjacency.get(e.target_id).push(e); });
  function el(tag, text, cls, parent) {
    const n = document.createElement(tag);
    if (text !== null && text !== undefined) n.textContent = text;
    if (cls) n.className = cls;
    if (parent) parent.append(n);
    return n;
  }
  function svg(tag, attrs, parent) {
    const n = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attrs).forEach(([k,v]) => n.setAttribute(k, v));
    if (parent) parent.append(n);
    return n;
  }
  const human = s => s.replaceAll('_',' ').toLowerCase();
  const value = x => typeof x === 'object' ? JSON.stringify(x) : String(x);
  const day = x => new Date(x).toLocaleDateString('en-GB', {timeZone:'Asia/Bangkok',day:'numeric',month:'short',year:'numeric'});
  function link(url, label, parent) {
    try {
      const u = new URL(url);
      if (!['http:','https:'].includes(u.protocol)) return;
      const a = el('a',label,'source-link',parent);
      a.href = u.href; a.target = '_blank'; a.rel = 'noopener noreferrer';
    } catch { /* Invalid public links are rendered only as text in properties. */ }
  }
  function stats(parent, entries) {
    const box = el('div',null,'detail-stats',parent);
    entries.forEach(([k,v]) => { el('span', k, null, box); el('span',value(v),null,box); });
  }
  function bar(parent, name, count, max, note='', display=null, blue=false) {
    const row = el('div',null,'bar-row',parent);
    const label = el('div',null,'bar-label',row);
    const title = el('span',name,'bar-title',label);
    if (note) el('span',note,'bar-class',title);
    el('span',display || fmt(count),'bar-value',label);
    const track = el('div',null,'track',row);
    track.setAttribute('role','img'); track.setAttribute('aria-label',`${name}: ${count} out of ${max}`);
    const fill = el('div',null,'fill'+(blue?' blue':''),track);
    fill.style.width = `${Math.min(100, Math.max(0, count / Math.max(1,max) * 100))}%`;
  }
  const totalNodes = D.nodes.length, totalEdges = D.edges.length;
  $('lead').textContent = 'Explore a staged, evidence-linked sample across major AI and related conferences. Collection coverage is partial; this snapshot is not a validated release.';
  $('snapshot-date').textContent = `Data recorded ${day(D.snapshot_at)}`;
  $('synthetic').textContent = D.is_synthetic ? 'Synthetic examples — not measured results' : 'Collected data · independent audit pending';
  [['Nodes',totalNodes,'Five entity types'],['Relationships',totalEdges,`${fmt(D.counts.unique_core_factual_edges)} factual R1–R4 edges`],['Covered editions',`${D.scope.covered_editions} / ${D.scope.series-D.scope.no_edition}`,'2023 editions in the planned scope'],['Papers in graph',D.counts.core_papers,`${D.splits.diagnostics} selected diagnostics`]].forEach(([label,count,note]) => {
    const m = el('div',null,'metric',$('summary'));
    el('div',label,'metric-label',m); el('div',typeof count==='number'?fmt(count):count,'metric-value',m); el('div',note,'metric-note',m);
  });
  const rb = el('div',null,'bar-list',$('relation-bars'));
  predicates.forEach((r,i) => bar(rb,r,D.counts.edges_by_relation[r] || 0, Math.max(...Object.values(D.counts.edges_by_relation)), classes[i]));
  const cb = el('div',null,'bar-list',$('collection-bars'));
  const c = D.collection, selected = D.splits.diagnostics;
  [['Selected diagnostics',selected,selected],['Acquired papers',c.acquired,selected],['Parsed PDF headers',D.extraction.by_status.parsed,selected],['Abstracts available',c.abstracts_available,c.acquired],['Strict OpenAlex matches',c.work_matches,c.acquired]].forEach(([name,n,den]) => bar(cb,name,n,den,'',`${fmt(n)} / ${fmt(den)}`));
  $('collection-note').textContent = `Bars use the displayed denominators. Abstract and OpenAlex coverage are separate branches. All ${c.acquired} acquired papers remain in the graph, including those without parsed PDFs. ${c.failed} acquisition conflicts are withheld.`;
  Object.entries(D.counts.nodes_by_label).forEach(([name,n]) => {
    const row = el('div',null,'inventory-row',$('node-inventory'));
    const label = el('span',null,'inventory-name',row);
    const icon = el('i',null,null,label); icon.style.setProperty('--color',colors[name]);
    el('span',name,null,label); el('span',fmt(n),null,row);
  });
  const covered = r => ['collected','legacy_preserved'].includes(r.status);
  function status(r) { return covered(r)?'covered':r.status==='no_2023_edition'?'none':'unresolved'; }
  D.by_venue.filter(covered).forEach(r => {
    const o = el('option',r.name,null,$('venue')); o.value = r.venue_id;
  });
  $('coverage-description').textContent = `${fmt(D.scope.roster_records)} roster records: ${fmt(D.scope.roster_by_status.included)} eligible and ${fmt(D.scope.roster_by_status.excluded)} excluded. The ${selected}-paper diagnostic sample is a separate subset.`;
  [[D.scope.series,'conference series'],[D.scope.covered_editions,'covered editions'],[D.scope.unresolved_editions,'unresolved sources'],[D.scope.no_edition,'without 2023 edition']].forEach(([n,s]) => {const x=el('span',null,null,$('scope-strip'));el('strong',n,null,x);el('span',s,null,x);});
  let conferenceRows = [];
  function renderConferences(all=false) {
    const term = all?'':$('conference-search').value.toLowerCase().trim(), filter = all?'all':$('conference-status').value;
    conferenceRows = D.by_venue.filter(r => (filter==='all'||status(r)===filter) && `${r.name} ${r.venue_id}`.toLowerCase().includes(term));
    $('conference-rows').replaceChildren();
    conferenceRows.forEach(r => {
      const row=el('tr',null,null,$('conference-rows'));
      const label=el('td',r.name,null,row);
      const problem=D.unresolved_sources.find(u => u.venue_id===r.venue_id);
      if(problem) label.title=problem.reason;
      const cell=el('td',null,null,row);
      el('span',status(r)==='covered'?'Covered':status(r)==='none'?'No edition':'Unresolved',`edition-status ${status(r)}`,cell);
      ['included_roster','selected','acquired','abstracts','work_matches','parsed_headers'].forEach(k=>el('td',r[k]===null?'—':fmt(r[k]),'num',row));
    });
    if(!conferenceRows.length) {const row=el('tr',null,null,$('conference-rows')); const td=el('td','No conferences match these filters.',null,row);td.colSpan=8;}
    $('conference-count').textContent=`${conferenceRows.length} / ${D.by_venue.length} series`;
  }
  $('conference-search').addEventListener('input',()=>renderConferences());
  $('conference-status').addEventListener('change',()=>renderConferences());
  renderConferences();
  const gb=el('div',null,'bar-list',$('gate-bars')), sz=D.size_targets;
  [['Resolved core researchers',D.counts.resolved_core_researchers,sz.min_resolved_core_researchers],['All domain nodes',totalNodes,sz.min_domain_nodes],['Factual R1–R4 edges',D.counts.unique_core_factual_edges,sz.min_unique_factual_edges],['Nonempty relationship types',Object.keys(D.counts.edges_by_relation).length,sz.required_relation_types]].forEach(([n,v,t])=>bar(gb,n,v,t,'',`${fmt(v)} / ${fmt(t)}`,true));
  const cov=D.coverage;
  $('topic-note').textContent=`${cov.topic_papers} / ${D.counts.core_papers} papers labeled (${(100*cov.topic_papers/D.counts.core_papers).toFixed(1)}%). ${D.counts.core_papers-cov.topic_papers} papers abstained; ${D.counts.edges_by_relation.HAS_TOPIC || 0} labels total.`;
  const tb=el('div',null,'bar-list',$('topic-bars'));
  D.topics.forEach(t=>bar(tb,t.name,t.papers,Math.max(1,...D.topics.map(x=>x.papers))));
  el('h3','What has been checked',null,$('verification'));
  el('p','This report freshly validates graph structure, reconciles graph counts, and checks the graph and configuration hashes against the metrics snapshot. It does not rerun collection, source downloads, database queries or the independent semantic audit.',null,$('verification'));
  el('p',`Recorded task 006 verification (${day(D.snapshot_at)}): ${D.verification_recorded.source_objects_verified} referenced source hashes checked; Neo4j import/replay and six integrity queries passed. These are historical checks recorded in the input metrics.`,null,$('verification'));
  const limits=[
    `${D.scope.unresolved_editions} of ${D.scope.series-D.scope.no_edition} in-year editions have unresolved sources. Diagnostic sampling is uneven and is not representative of the full international research population.`,
    `Accepted authorships: ${cov.accepted_authored_edges}/${fmt(cov.official_authorships)} (${(100*cov.accepted_authored_edges/cov.official_authorships).toFixed(2)}%). Researchers without corroborated identities remain outside the accepted graph.`,
    `Affiliated author–paper pairs: ${cov.affiliated_author_paper_pairs}/${fmt(cov.official_authorships)} (${(100*cov.affiliated_author_paper_pairs/cov.official_authorships).toFixed(2)}%), from ${cov.accepted_affiliation_observations} aligned triples. Current profiles are not used as historical affiliations.`,
    'Topics use a draft, uncalibrated phrase baseline. Inferred labels and derived relationships do not count toward the factual-edge size gate.',
    `Independent accuracy, precision, recall and F1 are unmeasured. ${D.splits.by_role.test} test and ${D.splits.by_role.development} development papers are reserved but unannotated; held-out acquisition overlap is ${D.splits.held_out_overlap}. Size and coverage requirements remain unmet.`
  ];
  limits.forEach(t=>el('li',t,null,$('limitations')));
  [['Graph version',D.graph_version],['Report generator',D.report_version],['Data recorded',`${day(D.snapshot_at)} · Asia/Bangkok`],['Structural validation',D.structural_validation],['Input graph',D.inputs.graph.name],['Snapshot type',D.is_synthetic?'Synthetic fixture':'Collected diagnostic sample']].forEach(([k,v])=>{el('dt',k,null,$('versions'));el('dd',v,null,$('versions'));});
  Object.entries(D.inputs).forEach(([k,v])=>{el('h4',`${k}: ${v.name}`,null,$('hashes'));el('pre',v.sha256,null,$('hashes'));});
  el('pre',JSON.stringify({...D.methods,classifier:D.classifier_method},null,2),null,$('hashes'));
  $('generated').textContent=`Generated ${day(D.generated_at)} · Asia/Bangkok`;

  // Graph views are filtered by supporting core papers, never by names alone.
  let projection='all', visibleNodes=[], visibleEdges=[], selectedNode=null, selectedEdge=null;
  let positions={}, transform={x:0,y:0,k:1}, listLimit=30;
  const scene=$('scene'), graph=$('graph');
  const relAllowed=e=>projection==='all'||(projection==='factual'&&factual.has(e.relation))||(projection==='coauthors'&&e.relation==='COAUTHORED_WITH')||(projection==='organizations'&&e.relation==='COLLABORATED_WITH');
  function selectNode(id) {selectedNode=id;selectedEdge=null;draw();inspectNode(id);}
  function nodeButton(id,parent,cls='node-action') {
    const n=nodes.get(id); if(!n)return;
    const b=el('button',n.name,cls,parent);b.type='button';b.addEventListener('click',()=>selectNode(id));return b;
  }
  function applyView(resetLayout=true) {
    projection=$('projection').value;
    const venue=$('venue').value, search=$('search').value.toLowerCase().trim();
    let pool=D.nodes.filter(n=>projection==='all'||(projection==='factual'&&n.label!=='Topic')||(projection==='coauthors'&&n.label==='Researcher')||(projection==='organizations'&&n.label==='Organization'));
    let links=D.edges.filter(relAllowed);
    if(venue) {
      const venuePapers=new Set(Object.entries(D.paper_venue).filter(([,v])=>v===venue).map(([p])=>p));
      const scopeEdges=D.edges.filter(e=>e.relation!=='SUBTOPIC_OF' && e.support_papers.length && (e.relation==='CITES'?e.support_papers.every(p=>venuePapers.has(p)):e.support_papers.some(p=>venuePapers.has(p))));
      const active=new Set([...venuePapers,venue]);
      scopeEdges.forEach(e=>{active.add(e.source_id);active.add(e.target_id);});
      // Keep only ancestors of topics supported by this venue's paper evidence.
      const tax=D.edges.filter(e=>e.relation==='SUBTOPIC_OF');
      let changed=true;
      while(changed) {changed=false;tax.forEach(e=>{if(active.has(e.source_id)&&!active.has(e.target_id)){active.add(e.target_id);changed=true;}});}
      const allowed=new Set(scopeEdges.map(e=>e.edge_id));
      links=links.filter(e=>allowed.has(e.edge_id)||(e.relation==='SUBTOPIC_OF'&&active.has(e.source_id)&&active.has(e.target_id)));
      pool=pool.filter(n=>active.has(n.id));
    }
    const poolIds=new Set(pool.map(n=>n.id));links=links.filter(e=>poolIds.has(e.source_id)&&poolIds.has(e.target_id));
    if(search) {
      const matches=new Set(pool.filter(n=>`${n.name} ${n.id}`.toLowerCase().includes(search)).map(n=>n.id));
      const expanded=new Set(matches);
      links.forEach(e=>{if(matches.has(e.source_id)||matches.has(e.target_id)){expanded.add(e.source_id);expanded.add(e.target_id);}});
      pool=pool.filter(n=>expanded.has(n.id));links=links.filter(e=>expanded.has(e.source_id)&&expanded.has(e.target_id));
    }
    visibleNodes=pool;visibleEdges=links;selectedNode=null;selectedEdge=null;listLimit=30;
    if(resetLayout) positions=Object.fromEntries(Object.entries(D.layouts[projection]).map(([k,v])=>[k,[...v]]));
    $('view-count').textContent=`${fmt(pool.length)} visible nodes · ${fmt(links.length)} visible edges`;
    $('empty-graph').hidden=pool.length>0;
    const notes={all:'All evidence classes; derived and taxonomy edges are dashed.',factual:'Observed R1–R4 only; topics and all derived relationships are excluded.',coauthors:'Researcher pairs supported by shared accepted core papers. Isolated researchers remain visible.',organizations:'Organization pairs supported by distinct coauthors on accepted core papers. Isolated organizations remain visible.'};
    $('projection-note').textContent=notes[projection]+(venue?' Conference filter selects relationships by supporting papers; stored weights still describe the full snapshot. Citations require both endpoints in this conference.':'')+(search?' Search shows name/ID matches and their immediate neighbors in this view.':'');
    draw();fit();renderList();inspectIntro();
  }
  function shape(n,parent,r) {
    const common={fill:colors[n.label],stroke:'#fff','stroke-width':1.2,class:'node-shape'};
    if(n.label==='Organization')return svg('rect',{...common,x:-r,y:-r,width:r*2,height:r*2,rx:1},parent);
    if(n.label==='Topic')return svg('path',{...common,d:`M0 ${-r-1}L${r+1} ${r}L${-r-1} ${r}Z`},parent);
    if(n.label==='Venue')return svg('path',{...common,d:`M0 ${-r-2}L${r+2} 0L0 ${r+2}L${-r-2} 0Z`},parent);
    return svg('circle',{...common,r},parent);
  }
  Object.keys(colors).forEach(label=>{
    const item=el('span',null,'legend-item',$('legend'));const icon=svg('svg',{viewBox:'-10 -10 20 20'},item);shape({label},icon,6);el('span',label,null,item);
  });
  function draw() {
    $('edge-layer').replaceChildren();$('node-layer').replaceChildren();$('label-layer').replaceChildren();
    const focus=new Set(selectedNode?[selectedNode]:[]);
    if(selectedNode)visibleEdges.forEach(e=>{if(e.source_id===selectedNode||e.target_id===selectedNode){focus.add(e.source_id);focus.add(e.target_id);}});
    visibleEdges.forEach(e=>{
      const a=positions[e.source_id], b=positions[e.target_id];if(!a||!b)return;
      const active=!selectedNode||e.source_id===selectedNode||e.target_id===selectedNode;
      const line=svg('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:e.edge_id===selectedEdge?'#15191d':'#9ba6b2','stroke-width':e.edge_id===selectedEdge?3:e.evidence_kind==='derived'?1.7:1,opacity:active?.6:.09,'stroke-dasharray':['derived','curated_taxonomy'].includes(e.evidence_kind)?'5 4':'none'},$('edge-layer'));
      if(!['COAUTHORED_WITH','COLLABORATED_WITH'].includes(e.relation))line.setAttribute('marker-end','url(#arrow)');
      const title=svg('title',{},line);title.textContent=`${e.relation}: ${nodes.get(e.source_id).name} → ${nodes.get(e.target_id).name}`;
    });
    const degrees=new Map(visibleNodes.map(n=>[n.id,0]));visibleEdges.forEach(e=>{degrees.set(e.source_id,(degrees.get(e.source_id)||0)+1);degrees.set(e.target_id,(degrees.get(e.target_id)||0)+1);});
    visibleNodes.forEach(n=>{
      const p=positions[n.id];if(!p)return;
      const g=svg('g',{transform:`translate(${p[0]} ${p[1]})`,tabindex:0,role:'button','aria-label':`${n.label}: ${n.name}`,class:n.id===selectedNode?'selected':'',opacity:!selectedNode||focus.has(n.id)?1:.18,'data-node-id':n.id},$('node-layer'));
      const r=n.label==='Paper'?4:n.label==='Venue'?11:n.label==='Researcher'?7:6;
      // Larger transparent hit target supports pointing without changing the data encoding.
      svg('circle',{r:12,fill:'transparent'},g);shape(n,g,r);
      svg('title',{},g).textContent=`${n.name} · ${n.label} · ${degrees.get(n.id)} connections in this view`;
      g.addEventListener('click',()=>{if(!dragMoved)selectNode(n.id);});
      g.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();selectNode(n.id);graph.querySelector(`[data-node-id="${CSS.escape(n.id)}"]`)?.focus();}});
      if(n.id===selectedNode||(!selectedNode&&n.label==='Venue')) {
        const label=svg('text',{x:p[0]+r+6,y:p[1]+4,class:'network-label'},$('label-layer'));
        const name=n.label==='Venue'?n.id.split(':').pop().toUpperCase():n.name;
        label.textContent=name.length>46?name.slice(0,44)+'…':name;
      }
    });
    updateTransform();
  }
  function updateTransform(){scene.setAttribute('transform',`translate(${transform.x} ${transform.y}) scale(${transform.k})`);}
  function fit(){
    if(!visibleNodes.length){transform={x:0,y:0,k:1};updateTransform();return;}
    const points=visibleNodes.map(n=>positions[n.id]).filter(Boolean), xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
    const minX=Math.min(...xs)-35,maxX=Math.max(...xs)+65,minY=Math.min(...ys)-35,maxY=Math.max(...ys)+35;
    const k=Math.min(3,1000/Math.max(100,maxX-minX),570/Math.max(100,maxY-minY));
    transform={k,x:550-k*(minX+maxX)/2,y:325-k*(minY+maxY)/2};updateTransform();
  }
  function zoom(factor){const k=Math.min(8,Math.max(.2,transform.k*factor));const ratio=k/transform.k;transform={k,x:550-(550-transform.x)*ratio,y:325-(325-transform.y)*ratio};updateTransform();}
  $('zoom-in').addEventListener('click',()=>zoom(1.3));$('zoom-out').addEventListener('click',()=>zoom(1/1.3));$('fit').addEventListener('click',fit);
  $('reset').addEventListener('click',()=>{$('projection').value='all';$('venue').value='';$('search').value='';applyView();});
  $('projection').addEventListener('change',()=>applyView());$('venue').addEventListener('change',()=>applyView());$('search').addEventListener('input',()=>applyView(false));
  let drag=null,dragMoved=false;
  function point(event){const p=graph.createSVGPoint();p.x=event.clientX;p.y=event.clientY;return p.matrixTransform(graph.getScreenCTM().inverse());}
  graph.addEventListener('pointerdown',event=>{
    if(event.button!==0)return;const p=point(event),n=event.target.closest('[data-node-id]');
    drag={id:n?.dataset.nodeId,x:p.x,y:p.y,tx:transform.x,ty:transform.y};dragMoved=false;graph.setPointerCapture(event.pointerId);
  });
  graph.addEventListener('pointermove',event=>{
    if(!drag)return;const p=point(event);if(Math.abs(p.x-drag.x)+Math.abs(p.y-drag.y)>4)dragMoved=true;
    if(!dragMoved)return;
    if(drag.id){positions[drag.id]=[(p.x-transform.x)/transform.k,(p.y-transform.y)/transform.k];draw();}
    else{transform.x=drag.tx+p.x-drag.x;transform.y=drag.ty+p.y-drag.y;updateTransform();}
  });
  graph.addEventListener('pointerup',event=>{
    const id=drag?.id;drag=null;
    if(id&&!dragMoved)selectNode(id);
    if(graph.hasPointerCapture(event.pointerId))graph.releasePointerCapture(event.pointerId);
  });
  graph.addEventListener('pointercancel',()=>{drag=null;});
  graph.addEventListener('keydown',event=>{if(event.target!==graph)return;if(['+','=','-','0'].includes(event.key)){event.preventDefault();event.key==='0'?fit():zoom(event.key==='-'?1/1.3:1.3);}});
  function renderList(){
    $('node-results').replaceChildren();$('list-count').textContent=`(${visibleNodes.length})`;
    [...visibleNodes].sort((a,b)=>a.name.localeCompare(b.name)).slice(0,listLimit).forEach(n=>{const b=nodeButton(n.id,$('node-results'));el('small',n.label,null,b);});
    $('more-nodes').hidden=listLimit>=visibleNodes.length;
  }
  $('more-nodes').addEventListener('click',()=>{listLimit+=30;renderList();});
  function inspectIntro(){
    $('detail').replaceChildren();el('p','Select a researcher, organization, paper, topic or venue. The inspector traces each accepted relationship back to its recorded evidence.','detail-intro',$('detail'));
    stats($('detail'),[['Visible entities',visibleNodes.length],['Visible relationships',visibleEdges.length],['Snapshot entities',totalNodes],['Snapshot relationships',totalEdges]]);
    el('p','Use the entity list below the graph to browse by keyboard. A sparse collaboration view reflects conservative identity and affiliation acceptance.','selection-note',$('detail'));
  }
  function inspectNode(id){
    const n=nodes.get(id),box=$('detail');box.replaceChildren();if(!n)return;
    el('div',n.label,'context',box);el('h4',n.name,'detail-name',box);el('p',n.id,'id',box);
    const inView=new Set(visibleNodes.map(x=>x.id));if(!inView.has(id))el('p','This supporting entity is outside the current graph filters. Reset the view to locate it.','selection-note',box);
    const props=el('dl',null,null,box);
    Object.entries(n.properties).forEach(([k,v])=>{el('dt',human(k),null,props);const dd=el('dd',null,null,props);if(k==='official_url')link(v,'Open official source',dd);else dd.textContent=value(v);});
    const incident=adjacency.get(id),inScope=new Set(visibleEdges.map(e=>e.edge_id));
    el('div',`${incident.length} relationships in full snapshot`,'detail-heading',box);
    incident.forEach(e=>{
      const b=el('button',null,'connection',box);b.type='button';
      el('span',`${e.relation} · ${human(e.evidence_kind)}${inScope.has(e.edge_id)?' · in view':''}`,null,b);
      el('strong',nodes.get(e.source_id===id?e.target_id:e.source_id).name,null,b);
      b.addEventListener('click',()=>inspectEdge(e.edge_id));
    });
  }
  function inspectEdge(id){
    const e=edges.get(id);if(!e)return;selectedEdge=id;selectedNode=null;draw();
    const box=$('detail');box.replaceChildren();el('div',human(e.evidence_kind),'context',box);el('h4',e.relation,'detail-name',box);el('p',id,'id',box);
    nodeButton(e.source_id,box);el('p',['COAUTHORED_WITH','COLLABORATED_WITH'].includes(e.relation)?'↔ undirected pair':'→',null,box);nodeButton(e.target_id,box);
    const props=el('dl',null,null,box);
    [['Method',e.method_version],['Graph',e.graph_version],['Status',e.validation_status],...Object.entries(e.properties).map(([k,v])=>[human(k),value(v)])].forEach(([k,v])=>{el('dt',k,null,props);el('dd',v,null,props);});
    if(e.evidence_kind==='derived')el('p','Support counts and fractional weights describe the full snapshot. Conference filtering selects support; it does not recompute stored weights.','selection-note',box);
    if(e.support_papers.length){el('div','Supporting papers','detail-heading',box);e.support_papers.forEach(p=>nodeButton(p,box));}
    el('div',`${e.evidence_ids.length} evidence records`,'detail-heading',box);
    e.evidence_ids.forEach(eid=>{
      const ev=D.evidence[eid],block=el('div',null,'source-block',box);el('p',human(ev.kind),null,block);
      if(ev.source_url)link(ev.source_url,'Open public source ↗',block);
      if(ev.excerpt)el('blockquote',ev.excerpt,null,block);
      if(ev.source_locator)el('p',`Locator: ${ev.source_locator}`,null,block);
      if(ev.retrieved_at)el('p',`Retrieved: ${ev.retrieved_at}`,null,block);
      if(ev.raw_sha256){const d=el('details',null,null,block);el('summary','Source hash',null,d);el('pre',ev.raw_sha256,null,d);}
      if(ev.support_edge_ids.length){const d=el('details',null,null,block);el('summary',`${ev.support_edge_ids.length} supporting input edges`,null,d);ev.support_edge_ids.forEach(s=>{const input=edges.get(s);if(input){const b=el('button',input.relation+' · '+nodes.get(input.source_id).name,'node-action',d);b.type='button';b.addEventListener('click',()=>inspectEdge(s));}});}
    });
  }
  function download(text,name,type){const u=URL.createObjectURL(new Blob([text],{type}));const a=el('a');a.href=u;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1000);}
  $('download').addEventListener('click',()=>download(JSON.stringify(D,null,2),'ai-research-network-report-data.json','application/json'));
  $('export-coverage').addEventListener('click',()=>{
    const keys=['name','status','included_roster','excluded_roster','selected','acquired','abstracts','work_matches','parsed_headers'];
    const cell=v=>'"'+String(v??'').replace(/^[=+@\-\t\r]/,"'$&").replaceAll('"','""')+'"';
    download([keys,...conferenceRows.map(r=>keys.map(k=>r[k]))].map(r=>r.map(cell).join(',')).join('\r\n'),'conference-coverage.csv','text/csv;charset=utf-8');
  });
  window.addEventListener('beforeprint',()=>{document.body.dataset.printing='true';renderConferences(true);});
  window.addEventListener('afterprint',()=>{delete document.body.dataset.printing;renderConferences();});
  $('print').addEventListener('click',()=>window.print());
  applyView();
})();
