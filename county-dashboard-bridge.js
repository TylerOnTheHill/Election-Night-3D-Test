/* Staging-only bridge: county preview remains opt-in and never replaces official Texas totals. */
(()=>{'use strict';
const ready=()=>document.querySelector('.early-heading');
function start(){
 if(!ready())return;
 const host=document.createElement('section');host.id='county-staging-bridge';host.setAttribute('aria-label','County preview review');
 host.style.cssText='display:block;max-width:1500px;margin:14px auto;padding:14px;border:1px solid #5b6474;border-radius:10px;background:#1b2430;color:#e7edf7';
 const heading=document.createElement('strong');heading.textContent='County data · staging review (TX / NC)';
 const note=document.createElement('p');note.textContent='Not published or approved for election reporting. Load a locally downloaded, verified workflow artifact to inspect county figures. The main dashboard remains unchanged.';
 note.style.cssText='font-size:12px;color:#c2cad7;margin:8px 0';
 const link=document.createElement('a');link.href='./county-review.html';link.textContent='Open county review';link.style.color='#9ed3ff';
 const status=document.createElement('span');status.textContent=' · Requires local staging JSON file';status.style.fontSize='12px';
 const precinct=document.createElement('a');precinct.href='./precinct-review.html';precinct.textContent=' · Preview precinct geometry (staging)';precinct.style.color='#9ed3ff';
 host.append(heading,note,link,precinct,status);
 const target=document.querySelector('.early-stats');
 if(target&&target.parentElement)target.parentElement.insertBefore(host,target);
 else document.querySelector('main')?.prepend(host);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();