/* ElectionHQ v7.2 — rebuilt dashboard shell. Preserve existing live map/data nodes. */
(()=>{'use strict';
const main=document.querySelector('main');if(!main)return;
const take=s=>main.querySelector(s);
const cards=take('.cards'),overview=take('.overview'),map=take('.map-panel'),detail=overview?.querySelector('aside'),county=take('.county-panel'),picker=take('.explorer-picker'),controls=take('.controls'),tablePanel=controls?.nextElementSibling,footer=take('.footer');
if(!cards||!map||!detail||!county||!picker||!controls||!tablePanel)return;
const node=(tag,cls,html)=>{const e=document.createElement(tag);e.className=cls||'';if(html)e.innerHTML=html;return e};
const shell=node('div','ehq-shell');
const mast=node('div','ehq-mast','<div class="ehq-overline">2026 MIDTERMS · EARLY VOTING · OBSERVED COUNTS</div><h1>Battleground <span>Watch</span></h1>');
const nav=node('div','ehq-nav');nav.setAttribute('role','tablist');nav.setAttribute('aria-label','Dashboard views');
const nationalBtn=node('button','ehq-nav-btn','<span class="ehq-nav-icon">◈</span> National overview'),stateBtn=node('button','ehq-nav-btn','<span class="ehq-nav-icon">▦</span> State explorer');
for(const [b,label] of [[nationalBtn,'National overview'],[stateBtn,'State explorer']]){b.type='button';b.setAttribute('role','tab');b.setAttribute('aria-label',label);nav.append(b)}
const national=node('section','ehq-screen');national.id='ehq-national-screen';
const state=node('section','ehq-screen');state.id='ehq-state-screen';state.hidden=true;
const summaryHeading=node('div','ehq-section-heading');
const metrics=node('div','ehq-metrics');metrics.append(...Array.from(cards.children));cards.remove();
const mapHeader=node('div','ehq-panel-head ehq-map-head','<span class="ehq-kicker">3D STATE GEOGRAPHY</span>');
map.prepend(mapHeader);
const watch=node('section','ehq-watch');watch.id='ehq-state-table';
watch.innerHTML='<div class="ehq-panel-head"><div><h3>Watchlist (19 states)</h3></div><div class="ehq-watch-counter">ALL 19</div></div>';
const watchBody=node('div','ehq-watch-body');watchBody.append(controls,tablePanel);watch.append(watchBody);
const split=node('div','ehq-main-grid overview');split.append(map,watch);
national.append(summaryHeading,metrics,split);
const stateHead=node('div','ehq-state-heading','<div><div class="ehq-kicker">← BACK TO NATIONAL OVERVIEW</div><h2 id="ehq-visible-state-name">Texas</h2></div>');
const stateTools=node('div','ehq-state-toolbar');stateTools.append(picker);const stateMetrics=node('div','ehq-state-kpis');for(const [label,id] of [['REPORTED EARLY BALLOTS','detail-total'],['REPORTING CUTOFF','detail-date'],['MAIL / ABSENTEE','detail-mail'],['EARLY IN PERSON','detail-inperson']]){const cell=node('div','ehq-state-kpi','<span>'+label+'</span><strong data-mirror="'+id+'">—</strong>');stateMetrics.append(cell)}const syncMetrics=()=>{for(const el of stateMetrics.querySelectorAll('[data-mirror]')){const src=document.getElementById(el.dataset.mirror);if(src)el.textContent=src.textContent}const name=document.getElementById('detail-name');const visible=document.getElementById('ehq-visible-state-name');if(name&&visible)visible.textContent=name.textContent};new MutationObserver(syncMetrics).observe(detail,{subtree:true,childList:true,characterData:true});
const tabs=node('div','ehq-state-tabs');tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','State explorer views');
const mapTab=node('button','','County map'),overviewTab=node('button','','State summary'),tableTab=node('button','','County table');
const countyStage=node('section','ehq-county-stage');countyStage.id='ehq-county-view';
const countyMain=node('div','ehq-county-main');countyMain.append(county);
const countySide=node('div','ehq-county-side');countySide.append(detail);
countyStage.append(countyMain,countySide);
const summaryStage=node('section','ehq-summary-stage');summaryStage.id='ehq-state-summary';summaryStage.hidden=true;
const tableStage=node('section','ehq-table-stage');tableStage.id='ehq-county-table-view';tableStage.hidden=true;
for(const [b,id] of [[mapTab,'ehq-county-view'],[overviewTab,'ehq-state-summary'],[tableTab,'ehq-county-table-view']]){b.type='button';b.setAttribute('role','tab');b.setAttribute('aria-controls',id);tabs.append(b)}
const countyTable=county.querySelector('.scroll'),placeholder=document.createComment('county-table-anchor');countyTable?.before(placeholder);
const countyTableEmpty=node('p','ehq-county-table-empty','County ballot totals have not been published for this state. The county map shows geography only.');
tableStage.append(countyTableEmpty);
function syncCountyTable(){const rows=county.querySelector('#county-preview-rows');const hasData=!!rows?.children.length;const available=!!document.querySelector('#battleground-county-preview:not([hidden])');if(countyTable)countyTable.hidden=!hasData;countyTableEmpty.hidden=hasData;countyTableEmpty.textContent=available?'County ballot totals have not been published for this state. The county map shows geography only.':'County-level reporting is not yet available for this state.';}
function showTab(which){const isMap=which==='map',isSummary=which==='summary',isTable=which==='table';
countyStage.hidden=!isMap;summaryStage.hidden=!isSummary;tableStage.hidden=!isTable;
if(isMap)countySide.append(detail);else if(isSummary)summaryStage.append(detail);else tableStage.append(detail);
if(isTable&&countyTable)tableStage.append(countyTable);else if(countyTable&&countyTable.parentNode!==county)placeholder.after(countyTable);
syncCountyTable();
for(const [b,on] of [[mapTab,isMap],[overviewTab,isSummary],[tableTab,isTable]])b.setAttribute('aria-selected',String(on));
if(isMap)window.dispatchEvent(new Event('resize'))}
function showView(which){const on=which==='state';national.hidden=on;state.hidden=!on;nationalBtn.setAttribute('aria-selected',String(!on));stateBtn.setAttribute('aria-selected',String(on));if(on)showTab('map');window.dispatchEvent(new Event('resize'))}
mapTab.addEventListener('click',()=>showTab('map'));overviewTab.addEventListener('click',()=>showTab('summary'));tableTab.addEventListener('click',()=>showTab('table'));
nationalBtn.addEventListener('click',()=>showView('national'));stateBtn.addEventListener('click',()=>showView('state'));
picker.querySelector('select')?.addEventListener('change',()=>showView('state'));
window.addEventListener('electionhq:battleground-map-click',()=>showView('state'));
watch.querySelector('#rows')?.addEventListener('click',e=>{if(e.target.closest('tr')&&!e.target.closest('a'))showView('state')});
watch.querySelector('#rows')?.addEventListener('keydown',e=>{if(e.key==='Enter'&&e.target.closest('tr'))showView('state')});
window.addEventListener('popstate',()=>showView(new URLSearchParams(location.search).has('state')?'state':'national'));
state.append(stateHead,stateTools,stateMetrics,tabs,countyStage,summaryStage,tableStage);
const foot=node('div','ehq-foot');if(footer)foot.append(footer);
shell.append(mast,nav,national,state,foot);main.replaceChildren(shell);
const countyRows=county.querySelector('#county-preview-rows');
if(countyRows)new MutationObserver(syncCountyTable).observe(countyRows,{childList:true});
const countyPreview=document.getElementById('battleground-county-preview');
if(countyPreview)new MutationObserver(syncCountyTable).observe(countyPreview,{attributes:true,attributeFilter:['hidden']});
syncCountyTable();
showView(new URLSearchParams(location.search).has('state')?'state':'national');
})();