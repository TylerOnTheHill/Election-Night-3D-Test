/* Approved v7.2 layout: reuse existing functional panels, no new data or public capabilities. */
(()=>{'use strict';
const main=document.querySelector('main'),overview=main?.querySelector('.overview'),county=main?.querySelector('.county-panel'),picker=main?.querySelector('.explorer-picker'),cards=main?.querySelector('.cards'),detail=overview?.querySelector('aside'),map=overview?.querySelector('.map-panel');
if(!main||!overview||!county||!detail||!map||!picker||!cards)return;
const el=(tag,cls,text)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(text)node.textContent=text;return node};
const nav=el('div','ehq-view-nav');nav.setAttribute('role','tablist');nav.setAttribute('aria-label','Dashboard views');
const nationalButton=el('button','','National overview'),stateButton=el('button','','State explorer');
for(const [button,id] of [[nationalButton,'ehq-national-screen'],[stateButton,'ehq-state-screen']]){button.type='button';button.setAttribute('role','tab');button.setAttribute('aria-controls',id);nav.append(button)}
const national=el('section','ehq-view');national.id='ehq-national-screen';
const state=el('section','ehq-view');state.id='ehq-state-screen';state.hidden=true;
const heading=el('div','');heading.id='ehq-state-header';heading.append(el('div','eyebrow','STATE EXPLORER · OBSERVED EARLY BALLOTS'));
const stateTabs=el('div','ehq-state-tabs');stateTabs.setAttribute('role','tablist');stateTabs.setAttribute('aria-label','State explorer sections');
const summaryTab=el('button','','Overview'),countyTab=el('button','','County map'),tableTab=el('button','','County table');
const summary=el('section','ehq-tab-content state-metrics'),countyView=el('section','ehq-tab-content'),tableView=el('section','ehq-tab-content');
summary.id='ehq-state-summary';countyView.id='ehq-county-view';tableView.id='ehq-county-table-view';
for(const [button,target] of [[summaryTab,summary],[countyTab,countyView],[tableTab,tableView]]){button.type='button';button.setAttribute('role','tab');button.setAttribute('aria-controls',target.id);stateTabs.append(button)}
const tableSection=el('section','ehq-tab-content');tableSection.id='ehq-state-table';
const controls=main.querySelector('.controls'),stateTable=controls?.nextElementSibling;
if(controls&&stateTable){tableSection.append(controls,stateTable)}
// Move existing live widgets rather than creating duplicate state or county data components.
overview.replaceChildren(map);national.append(cards,overview,tableSection);
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
 if(selected===tableView)showCountyTable();else restoreCountyTable();
 for(const [button,section] of [[summaryTab,summary],[countyTab,countyView],[tableTab,tableView]]){const active=section===selected;button.setAttribute('aria-selected',String(active));section.hidden=!active}
 // The county renderer observes its host size; keep the map in the visible section.
 if(selected===countyView)window.dispatchEvent(new Event('resize'));
}
function switchView(name){const isState=name==='state';national.hidden=isState;state.hidden=!isState;nationalButton.setAttribute('aria-selected',String(!isState));stateButton.setAttribute('aria-selected',String(isState));if(isState)switchTab('overview')}
nationalButton.addEventListener('click',()=>switchView('national'));stateButton.addEventListener('click',()=>switchView('state'));
summaryTab.addEventListener('click',()=>switchTab('overview'));countyTab.addEventListener('click',()=>switchTab('map'));tableTab.addEventListener('click',()=>switchTab('table'));
picker.querySelector('select')?.addEventListener('change',()=>switchView('state'));
window.addEventListener('electionhq:battleground-map-click',()=>switchView('state'));
switchView(new URLSearchParams(location.search).has('state')?'state':'national');
})();
