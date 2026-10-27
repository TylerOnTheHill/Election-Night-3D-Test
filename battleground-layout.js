/* Approved v7.2 layout: reuse existing functional panels, no new data or public capabilities. */
(()=>{'use strict';
const main=document.querySelector('main'),overview=main?.querySelector('.overview'),county=main?.querySelector('.county-panel'),picker=main?.querySelector('.explorer-picker'),cards=main?.querySelector('.cards'),detail=overview?.querySelector('aside'),map=overview?.querySelector('.map-panel');
if(!main||!overview||!county||!detail||!map||!picker||!cards)return;
const el=(tag,cls,text)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(text)node.textContent=text;return node};
const nav=el('div','ehq-view-nav');nav.setAttribute('role','tablist');nav.setAttribute('aria-label','Dashboard views');
const nationalButton=el('button','','National overview'),stateButton=el('button','','State explorer');
for(const [button,id] of [[nationalButton,'ehq-national-screen'],[stateButton,'ehq-state-screen']]){button.type='button';button.setAttribute('role','tab');button.setAttribute('aria-controls',id);nav.append(button)}
const national=el('section','ehq-view');national.id='ehq-national-screen';
const hero=el('div','studio-hero');hero.innerHTML='<div><div class="studio-kicker">2026 MIDTERM ELECTIONS <span class="studio-live">● EARLY VOTING</span></div><h1>Election <em>Intelligence.</em></h1><p>Reported early ballots · 19-state watchlist · source-verified observations</p></div><div class="studio-hero-meta"><span>LIVE OBSERVATION DESK</span><strong>2026 / US</strong><small>Counts are ballots, not candidate votes</small></div>';
const mapHeader=el('div','studio-map-header');mapHeader.innerHTML='<div><span class="studio-kicker">NATIONAL OVERVIEW</span><h3>Where America is voting</h3></div><span class="studio-map-chip">3D GEOGRAPHY</span>';
const railHeader=el('div','studio-rail-header');railHeader.innerHTML='<span class="studio-kicker">THE WATCHLIST</span><h3>State reporting desk</h3><p>Select a state to open its county explorer</p>';
const state=el('section','ehq-view');state.id='ehq-state-screen';state.hidden=true;
const heading=el('div','studio-state-hero');heading.id='ehq-state-header';heading.innerHTML='<div><div class="studio-kicker">STATE INTELLIGENCE / COUNTY REPORTING</div><h2>County Explorer</h2><p>Verified county-level early ballot reporting · select a county for details</p></div><div class="studio-state-mark">ELECTIONHQ <span> / 2026</span></div>';
const stateTabs=el('div','ehq-state-tabs');stateTabs.setAttribute('role','tablist');stateTabs.setAttribute('aria-label','State explorer sections');
const summaryTab=el('button','','Overview'),countyTab=el('button','','County map'),tableTab=el('button','','County table');
const summary=el('section','ehq-tab-content state-metrics'),countyView=el('section','ehq-tab-content'),tableView=el('section','ehq-tab-content');
summary.id='ehq-state-summary';countyView.id='ehq-county-view';tableView.id='ehq-county-table-view';
for(const [button,target] of [[summaryTab,summary],[countyTab,countyView],[tableTab,tableView]]){button.type='button';button.setAttribute('role','tab');button.setAttribute('aria-controls',target.id);stateTabs.append(button)}
const tableSection=el('section','ehq-tab-content');tableSection.id='ehq-state-table';
const controls=main.querySelector('.controls'),stateTable=controls?.nextElementSibling;
if(controls&&stateTable){tableSection.append(controls,stateTable)}
// Move existing live widgets rather than creating duplicate state or county data components.
map.prepend(mapHeader);tableSection.prepend(railHeader);overview.replaceChildren(map,tableSection);national.append(hero,cards,overview);
summary.append(detail);
countyView.append(county);
state.append(heading,picker,stateTabs,summary,countyView,tableView);
const countyTable=county.querySelector('.scroll');
const countyPlaceholder=document.createComment('county-table-original-position');
countyTable?.before(countyPlaceholder);
function showCountyTable(){if(countyTable&&countyTable.parentElement!==tableView)tableView.append(countyTable)}
function restoreCountyTable(){if(countyTable&&countyTable.parentElement!==county)countyPlaceholder.after(countyTable)}
const header=main.querySelector('h2');header?.after(nav,national,state);
function switchTab(name){const selected=name==='overview'?summary:name==='map'?countyView:tableView;
 if(selected===summary)summary.append(detail);else if(selected===countyView)countyView.append(detail);else tableView.append(detail);
 if(selected===tableView)showCountyTable();else restoreCountyTable();
 for(const [button,section] of [[summaryTab,summary],[countyTab,countyView],[tableTab,tableView]]){const active=section===selected;button.setAttribute('aria-selected',String(active));section.hidden=!active}
 // The county renderer observes its host size; keep the map in the visible section.
 if(selected===countyView)window.dispatchEvent(new Event('resize'));
}
function switchView(name){const isState=name==='state';national.hidden=isState;state.hidden=!isState;nationalButton.setAttribute('aria-selected',String(!isState));stateButton.setAttribute('aria-selected',String(isState));if(isState)switchTab('map');else window.dispatchEvent(new Event('resize'))}
nationalButton.addEventListener('click',()=>switchView('national'));stateButton.addEventListener('click',()=>switchView('state'));
summaryTab.addEventListener('click',()=>switchTab('overview'));countyTab.addEventListener('click',()=>switchTab('map'));tableTab.addEventListener('click',()=>switchTab('table'));
picker.querySelector('select')?.addEventListener('change',()=>switchView('state'));
window.addEventListener('electionhq:battleground-map-click',()=>switchView('state'));
// Selecting a watchlist row is a navigation action, not just a hidden detail update.
const watchRows=main.querySelector('#rows');
watchRows?.addEventListener('click',event=>{if(event.target.closest('tr')&&!event.target.closest('a'))switchView('state')});
watchRows?.addEventListener('keydown',event=>{if(event.key==='Enter'&&event.target.closest('tr'))switchView('state')});
window.addEventListener('popstate',()=>{if(new URLSearchParams(location.search).has('state'))switchView('state')});
switchView(new URLSearchParams(location.search).has('state')?'state':'national');
})();
