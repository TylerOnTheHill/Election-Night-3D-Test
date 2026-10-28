import { chromium } from 'playwright';
import fs from 'node:fs/promises';

const out='artifacts/geographic-preview';
await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--disable-web-security=false']});
const errors=[];
const result={url:'http://127.0.0.1:8765/',checks:[],errors};
try{
 const page=await browser.newPage({viewport:{width:1440,height:900},deviceScaleFactor:1});
 page.on('pageerror',e=>errors.push('pageerror: '+(e.stack||e.message)));
 page.on('response',r=>{if(!r.ok()&&r.url().startsWith(result.url))errors.push('HTTP '+r.status()+' '+r.url())});
 page.on('requestfailed',r=>errors.push('requestfailed: '+r.url()+' '+r.failure()?.errorText));
 page.on('console',m=>{if(m.type()==='error')errors.push('console: '+m.text())});
 for(let i=0;i<20;i++){try{await page.goto(result.url,{waitUntil:'domcontentloaded',timeout:12000});break}catch(e){if(i===19)throw e;await page.waitForTimeout(500)}}
 await page.waitForTimeout(12000);
 result.diagnostics=await page.evaluate(()=>({ready:!!window.__mapWebGLReady,loading:document.getElementById('loading')?.textContent,mode:document.getElementById('mode')?.value,nationalHidden:document.getElementById('national')?.hidden,scripts:[...document.scripts].map(s=>({src:s.src,type:s.type}))}));
 result.checks.push({name:'stage exists',ok:await page.locator('#stage').count()===1});
 result.checks.push({name:'canvas exists',ok:await page.locator('#stage canvas').count()>=1});
 const layout=await page.evaluate(()=>{const stage=document.querySelector('.stage'),summary=document.querySelector('.summary-strip'),main=document.querySelector('.main-area');const bg=getComputedStyle(document.body).backgroundColor;return {background:bg,mapAboveSummary:stage.getBoundingClientRect().top<summary.getBoundingClientRect().top,mainDisplay:getComputedStyle(main).display,stagingPanel:document.body.innerText.includes('County data · staging review')}});
 result.checks.push({name:'black primary background',ok:layout.background==='rgb(0, 0, 0)',actual:layout.background});
 result.checks.push({name:'map appears before seat summary',ok:layout.mapAboveSummary});
 result.checks.push({name:'development staging panel absent from primary dashboard',ok:!layout.stagingPanel});
 result.checks.push({name:'bounded label pool',ok:(await page.locator('.ehq-place-label').count())<=120});
 await page.screenshot({path:out+'/initial-texas.png',fullPage:true});
 // Enter Texas using the real state-map navigation instead of testing labels on the national map.
 await page.locator('#stage canvas').dblclick({position:{x:520,y:340}}).catch(()=>{});
 await page.waitForTimeout(1400);
 if(!(await page.locator('#national').isVisible())){
   // The national view uses click-to-select, double-click-to-enter; use the search if needed.
   await page.locator('#search').fill('Texas');
   await page.waitForTimeout(300);
   await page.locator('#search').press('Enter');
   await page.waitForTimeout(300);
   await page.locator('#stage canvas').dblclick({position:{x:520,y:340}}).catch(()=>{});
   await page.waitForTimeout(1500);
 }
 result.checks.push({name:'entered a state-level map',ok:await page.locator('#national').isVisible()});
 await page.locator('#zoom-number').fill('90');
 await page.locator('#zoom-number').dispatchEvent('change');
 await page.waitForTimeout(1800);
 const labels=await page.locator('.ehq-place-label:visible').count();
 result.diagnostics.closeZoom={zoom:await page.locator('#zoom-number').inputValue(),labelNodes:await page.locator('.ehq-place-label').count(),visible:labels};
 result.checks.push({name:'Texas close-zoom labels visible',ok:labels>0,visibleLabels:labels});
 await page.screenshot({path:out+'/texas-close-zoom.png',fullPage:true});
 // The United States button is hidden when already in national view; do not click a hidden control.
 const national=page.locator('#national');
 if(await national.isVisible()) await national.click();
 else result.checks.push({name:'national navigation already active',ok:true});
 await page.waitForTimeout(4000);
 await page.screenshot({path:out+'/national-map.png',fullPage:true});
 result.checks.push({name:'national map renders',ok:await page.locator('#stage canvas').count()>=1});
 const nationalLabels=await page.locator('.ehq-place-label:visible').count();
 result.checks.push({name:'national metro labels visible',ok:nationalLabels>0,visibleLabels:nationalLabels});
 result.checks.push({name:'visible labels clear of zoom controls',ok:await page.evaluate(()=>{const controls=document.querySelector('#stage .zoom-controls')||document.querySelector('.zoom-controls');if(!controls)return true;const r=controls.getBoundingClientRect();return [...document.querySelectorAll('.ehq-place-label')].filter(e=>!e.hidden).every(e=>{const b=e.getBoundingClientRect();return b.right<r.left||b.left>r.right||b.bottom<r.top||b.top>r.bottom})})});
 // Exercise the Early Vote view independently; never infer its health from Election Night.
 await page.locator('#tab-early').click();
 await page.waitForTimeout(2500);
 const early=await page.evaluate(()=>({mode:document.body.classList.contains('early'),heading:document.querySelector('.early-heading')?.getBoundingClientRect().height||0,stats:[...document.querySelectorAll('.early-stat')].filter(el=>getComputedStyle(el).display!=='none').length,green:!!document.querySelector('#ev-total'),canvas:!!document.querySelector('#stage canvas')}));
 result.diagnostics.earlyVote=early;
 result.checks.push({name:'Early Vote mode activates',ok:early.mode});
 result.checks.push({name:'Early Vote reporting statistics render',ok:early.heading>0&&early.stats>=2&&early.green});
 result.checks.push({name:'Early Vote map canvas remains available',ok:early.canvas});
 const earlyLayout=await page.evaluate(()=>{const stage=document.querySelector('.stage').getBoundingClientRect(),stats=document.querySelector('.early-stats').getBoundingClientRect(),filters=document.querySelector('.ev-controls').getBoundingClientRect(),card=document.querySelector('.early-stat');return {mapBeforeStats:stage.top<stats.top,filtersBeforeMap:filters.top<stage.top,cardBackground:getComputedStyle(card).backgroundColor}});
 result.diagnostics.earlyLayout=earlyLayout;
 result.checks.push({name:'Early Vote map above reporting metrics',ok:earlyLayout.mapBeforeStats});
 // National view intentionally hides Texas-only participation filters; assert order only when filters are shown.
 const filtersVisible=await page.locator('.ev-controls').isVisible();
 result.checks.push({name:'Early Vote filters do not obstruct national map',ok:!filtersVisible||earlyLayout.filtersBeforeMap,filtersVisible});
 result.checks.push({name:'Early Vote metric cards use black surface',ok:earlyLayout.cardBackground==='rgb(9, 9, 9)',actual:earlyLayout.cardBackground});
 await page.screenshot({path:out+'/early-vote-national.png',fullPage:true});
 // Check the second reporting mode at a narrower desktop viewport as well.
 await page.setViewportSize({width:1024,height:768});
 await page.waitForTimeout(900);
 const narrow=await page.evaluate(()=>{
  const stage=document.querySelector('#stage').getBoundingClientRect();
  const stats=document.querySelector('.early-stats').getBoundingClientRect();
  const doc=document.documentElement;
  return {width:innerWidth,documentWidth:doc.scrollWidth,mapWidth:stage.width,mapHeight:stage.height,mapAboveStats:stage.top<stats.top};
 });
 result.diagnostics.earlyNarrow=narrow;
 result.checks.push({name:'Early Vote map stays usable at 1024px',ok:narrow.mapWidth>=500&&narrow.mapHeight>=300&&narrow.mapAboveStats,actual:narrow});
 await page.screenshot({path:out+'/early-vote-1024px.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 await page.waitForTimeout(950);
 const mobile=await page.evaluate(()=>{
  const map=document.querySelector('#stage').getBoundingClientRect();
  const stats=document.querySelector('.early-stats').getBoundingClientRect();
  const doc=document.documentElement;
  return {viewport:innerWidth,scrollWidth:doc.scrollWidth,mapWidth:map.width,mapHeight:map.height,mapAboveStats:map.top<stats.top};
 });
 result.diagnostics.earlyMobile=mobile;
 result.checks.push({name:'Early Vote mobile map remains accessible',ok:mobile.mapWidth>=300&&mobile.mapHeight>=300&&mobile.mapAboveStats,actual:mobile});
 await page.screenshot({path:out+'/early-vote-mobile.png',fullPage:true});
  await page.setViewportSize({width:1440,height:900});
  result.checks.push({name:'no browser runtime errors',ok:errors.length===0});
 await fs.writeFile(out+'/results.json',JSON.stringify(result,null,2));
 if(result.checks.some(x=>!x.ok)){console.error(JSON.stringify(result,null,2));process.exitCode=1}else console.log(JSON.stringify(result,null,2));
}catch(e){errors.push(String(e));await fs.writeFile(out+'/results.json',JSON.stringify(result,null,2));throw e}
finally{await browser.close()}
