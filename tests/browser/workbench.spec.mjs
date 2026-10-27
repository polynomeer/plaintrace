import {test as base, expect} from '@playwright/test';
import {demoReport} from '../../plaintrace/web/demo.mjs';
import fs from 'node:fs/promises';
import os from 'node:os';
const test = base.extend({
  page: async ({page}, use) => {
    const errors = [], external = [], badAssets = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('request', r => {if (/^https?:/.test(r.url()) && new URL(r.url()).origin !== 'http://127.0.0.1:8771') external.push(r.url());});
    page.on('response', r => {if(r.status() >= 400) badAssets.push(r.url());});
    await use(page);
    expect(errors).toEqual([]); expect(external).toEqual([]); expect(badAssets).toEqual([]);
  }
});
const upload = async (page, report, name='합성 보고서.json') => {
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', {name:'보고서 열기', exact:true}).click();
  await (await chooser).setFiles({name, mimeType:'application/json', buffer:Buffer.from(JSON.stringify(report))});
  await expect(page.locator('#workspace-name')).toHaveText(name);
};

test('B-01 empty screen, skip navigation and keyboard modal', async ({page}) => {
  await page.goto('/'); await expect(page.locator('#empty-workspace')).toBeVisible();
  await page.keyboard.press('Tab'); await expect(page.getByRole('link', {name:'본문으로 이동'})).toBeFocused();
  await page.keyboard.press('Enter'); await expect(page.locator('#main')).toBeFocused();
  await page.getByRole('button', {name:'사용 방법'}).click();
  await expect(page.locator('#help-dialog')).toBeVisible(); await page.keyboard.press('Escape');
  await expect(page.locator('#help-dialog')).not.toBeVisible();
  await expect(page.getByRole('button', {name:'사용 방법'})).toBeFocused();
});

test('B-02 demo filters, source details, diagnostics, timeline and support', async ({page}) => {
  await page.goto('/?demo=1'); await expect(page.locator('.source-item')).toHaveCount(3);
  await page.locator('[data-filter=windows]').click(); await expect(page.locator('.source-item')).toHaveCount(2);
  await page.locator('#source-search').fill('SYSTEM'); await expect(page.locator('.source-item')).toHaveCount(1);
  await expect(page.locator('#record-total')).toHaveText('1개');
  await page.locator('#diagnostics summary').click(); await expect(page.locator('#diagnostics')).toContainText('합성 미리보기');
  await page.locator('[data-view=timeline]').click(); await expect(page.locator('#timeline-list > li')).toHaveCount(5);
  await page.locator('#timeline-selected').check(); await expect(page.locator('#timeline-count')).toHaveText('0개');
  await page.locator('[data-view=support]').click(); await expect(page.locator('.support-group')).toHaveCount(21);
  await expect(page.locator('.host-item')).toHaveCount(3);
});

test('B-03 native report picker, literal hostile text, raw values and source references', async ({page}) => {
  const report=demoReport(); report.visits[0].title='<img src=x onerror=alert(1)> 한글 O\'Brien\nline';
  report.visits[0].timestamp_raw='134375702481234567';
  await page.goto('/'); await upload(page,report);
  await expect(page.locator('#demo-notice')).toBeHidden();
  await page.locator('#record-list .row-open').first().click();
  await expect(page.locator('#raw-content')).toContainText('134375702481234567');
  await expect(page.locator('#raw-content')).toContainText('<img src=x onerror=alert(1)>');
  await expect(page.locator('#record-context')).toHaveText('visits / S-1');
  await expect(page.locator('img')).toHaveCount(0); await page.keyboard.press('Escape');
  await expect(page.locator('#record-list .row-open').first()).toBeFocused();
});

test('B-04 rejected schema and UTF-8 preserve the current workspace', async ({page}) => {
  await page.goto('/?demo=1');
  for(const buffer of [Buffer.from('{"tool":"plaintrace","format_version":16}'),Buffer.from([0xff,0xfe,0x41])]) {
    await page.locator('#report-file').setInputFiles({name:'invalid.json',mimeType:'application/json',buffer});
    await expect(page.locator('#error')).toBeVisible(); await expect(page.locator('#workspace-name')).toHaveText('DEMO-001');
    await expect(page.locator('.source-item')).toHaveCount(3);
  }
});

test('B-05 original download preserves selected file bytes', async ({page}) => {
  await page.goto('/'); const buffer=Buffer.from(JSON.stringify(demoReport(),null,3)+'\n\n');
  await page.locator('#report-file').setInputFiles({name:'original.json',mimeType:'application/json',buffer});
  await expect(page.locator('#workspace-name')).toHaveText('original.json');
  const pending=page.waitForEvent('download'); await page.locator('#save-report').click();
  const download=await pending; expect(await fs.readFile(await download.path())).toEqual(buffer);
});

test('B-06 source and record pagination retain associations', async ({page}) => {
  const r=demoReport(); r.sources=Array.from({length:32},(_,i)=>({...r.sources[0],source_id:i+1,path:`/synthetic/History-${i+1}`}));
  r.events=[];r.downloads=[];r.system_info=[];r.diagnostics=[];
  r.visits=Array.from({length:45},(_,i)=>({...r.visits[0],record_id:`visit:${i}`,title:`Row ${i}`}));
  for(const key of Object.keys(r.counts))r.counts[key]=r[key].length;
  await page.goto('/'); await upload(page,r);
  await expect(page.locator('#record-list tr')).toHaveCount(20);
  await page.locator('#record-pagination').getByRole('button',{name:'다음'}).click();
  await expect(page.locator('#record-list')).toContainText('Row 20');
  await page.locator('#source-pagination').getByRole('button',{name:'다음'}).click();
  await expect(page.locator('.source-item')).toHaveCount(2); await expect(page.locator('#source-badge')).toHaveText('S-31');
  await expect(page.locator('#record-total')).toHaveText('0개');
  await page.locator('#source-pagination').getByRole('button',{name:'이전'}).click();
  await expect(page.locator('#record-list')).toContainText('Row 0');
});

test('B-07 themes, responsive layouts and screenshots', async ({page},info) => {
  await page.goto('/?demo=1');
  for(const theme of ['light','dark']) {
    await page.locator('#theme').selectOption(theme);
    await expect(page.locator('html')).toHaveAttribute('data-theme',theme);
    for(const width of [1440,1024,850,768,560,390]) {
      await page.setViewportSize({width,height:1000});
      await expect(page.locator('#import-button')).toBeVisible();
      const metrics=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,
        source:document.querySelector('.source-item').getBoundingClientRect().toJSON(),
        inspector:document.querySelector('.inspector').getBoundingClientRect().toJSON()}));
      expect(metrics.scroll).toBeLessThanOrEqual(metrics.width+1);
      expect(metrics.source.width).toBeGreaterThan(100);
      if(width<=850)expect(metrics.inspector.y).toBeGreaterThan(metrics.source.y);
      if([1440,390].includes(width))await page.screenshot({path:info.outputPath(`${theme}-${width}.png`),fullPage:true});
    }
  }
  await page.emulateMedia({colorScheme:'dark',reducedMotion:'reduce'}); await page.locator('#theme').selectOption('auto');
  expect(await page.locator('body').evaluate(e=>getComputedStyle(e).backgroundColor)).toBe('rgb(24, 29, 32)');
  expect(await page.locator('#import-button').evaluate(e=>getComputedStyle(e).transitionDuration)).toBe('0s');
});

test('B-08 clearing removes report DOM and raw dialog content', async ({page}) => {
  await page.goto('/?demo=1'); await page.locator('#record-list .row-open').first().click();
  await expect(page.locator('#raw-content')).toContainText('Documentation overview'); await page.keyboard.press('Escape');
  await page.locator('#clear-button').click(); await expect(page.locator('#empty-workspace')).toBeVisible();
  await expect(page.locator('#source-list')).toBeEmpty(); await expect(page.locator('#record-list')).toBeEmpty();
  await expect(page.locator('#raw-content')).toBeEmpty(); await expect(page.locator('#save-report')).toBeDisabled();
});

test('B-09 no report persistence and exact browser environment', async ({page,browser,browserName},info) => {
  await page.goto('/?demo=1');
  const storage=await page.evaluate(()=>({local:localStorage.length,session:sessionStorage.length,cookies:document.cookie}));
  expect(storage).toEqual({local:0,session:0,cookies:''});
  await page.goto('/'); await expect(page.locator('#empty-workspace')).toBeVisible();
  await info.attach('environment.json',{body:JSON.stringify({platform:os.platform(),release:os.release(),arch:os.arch(),
    browser:browserName,version:browser.version(),node:process.version,sha:process.env.GITHUB_SHA||null,
    run:process.env.GITHUB_RUN_ID||null,image:process.env.ImageVersion||null,
    userAgent:await page.evaluate(()=>navigator.userAgent)},null,2),contentType:'application/json'});
});
