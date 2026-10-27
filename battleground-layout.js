/* ElectionHQ v7.2 — rebuilt dashboard shell. Preserve existing live map/data nodes. */
(()=>{'use strict';
const main=document.querySelector('main');if(!main)return;
const take=s=>main.querySelector(s);
const cards=take('.cards'),overview=take('.overview'),map=take('.map-panel'),detail=overview?.querySelector('aside'),county=take('.county-panel'),picker=take('.explorer-picker'),controls=take('.controls'),tablePanel=controls?.nextElementSibling,footer=take('.footer');
if(!cards||!map||!detail||!county||!picker||!controls||!tablePanel)return;
const node=(tag,cls,html)=>{const e=document.createElement(tag);e.className=cls||'';if(html)e.innerHTML=html;return e};
const shell=node('div','ehq-shell');
const mast=node('div','ehq-mast','<div><div class="ehq-overline"><span class="ehq-dot"></span> ELECTIONHQ / 2026 MIDTERMS <span class="ehq-overline-sep">/</span> EARLY VOTE INTELLIGENCE</div><h1>Election <span>Intelligence.</span></h1><p>Observed early voting. Verified reporting. A clearer view of the electorate.</p></div><div class="ehq-mast-right"><div>THE OBSERVATION DESK</div><strong>2026</strong><small>Ballots cast, not candidate votes</small></div>');
const nav=node('div','ehq-nav');nav.setAttribute('role','tablist');nav.setAttribute('aria-label','Dashboard views');
const nationalBtn=node('button','ehq-nav-btn','<span class="ehq-nav-icon">◈</span> National overview'),stateBtn=node('button','ehq-nav-btn','<span class="ehq-nav-icon">▦</span> State explorer');
for(const [b,label] of [[nationalBtn,'National overview'],[stateBtn,'State explorer']]){b.type='button';b.setAttribute('role','tab');b.setAttribute('aria-label',label);nav.append(b)}
const national=node('section','ehq-screen');national.id='ehq-national-screen';
const state=node('section','ehq-screen');state.id='ehq-state-screen';state.hidden=true;
const summaryHeading=node('div','ehq-section-heading','<div><div class="ehq-kicker">01 / THE NATIONAL PICTURE</div><h2>Early vote dashboard</h2></div><div class="ehq-heading-note">19-STATE WATCHLIST <span class="ehq-dot"></span> SOURCE-REPORTED DATA</div>');
const metrics=node('div','ehq-metrics');metrics.append(...Array.from(cards.children));cards.remove();
const mapHeader=node('div','ehq-panel-head','<div><div class="ehq-kicker">NATIONAL GEOGRAPHY</div><h3>Early voting across America</h3><p>Explore states and reported ballot totals</p></div><div class="ehq-geometry-badge">3D MAP</div>');
map.prepend(mapHeader);
const watch=node('section','ehq-watch');watch.id='ehq-state-table';
watch.innerHTML='<div class="ehq-panel-head"><div><div class="ehq-kicker">LIVE REPORTING DESK</div><h3>The state watchlist</h3><p>Select any state to explore county reporting</p></div><div class="ehq-watch-counter">19 STATES</div></div>';
const watchBody=node('div','ehq-watch-body');watchBody.append(controls,tablePanel);watch.append(watchBody);
const split=node('div','ehq-main-grid overview');split.append(map,watch);
national.append(summaryHeading,metrics,split);
const stateHead=node('div','ehq-state-heading','<div><div class="ehq-kicker">02 / STATE EXPLORER</div><h2>Inside the early vote.</h2><p>County-level observations, reporting coverage, and ballot methods</p></div><div class="ehq-heading-note">VERIFIED REPORTING / 2026</div>');
const stateTools=node('div','ehq-state-toolbar');stateTools.append(picker);
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
function showTab(which){const isMap=which==='map',isSummary=which==='summary',isTable=which==='table';
countyStage.hidden=!isMap;summaryStage.hidden=!isSummary;tableStage.hidden=!isTable;
if(isMap)countySide.append(detail);else if(isSummary)summaryStage.append(detail);else tableStage.append(detail);
if(isTable&&countyTable)tableStage.append(countyTable);else if(countyTable&&countyTable.parentNode!==county)placeholder.after(countyTable);
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
state.append(stateHead,stateTools,tabs,countyStage,summaryStage,tableStage);
const foot=node('div','ehq-foot');if(footer)foot.append(footer);
shell.append(mast,nav,national,state,foot);main.replaceChildren(shell);
showView(new URLSearchParams(location.search).has('state')?'state':'national');
})();