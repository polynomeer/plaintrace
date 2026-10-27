// Data-only model. No DOM, network, storage or evidence-path access.
export const LIMITS = Object.freeze({ bytes: 16 * 1024 * 1024, rows: 100000, sources: 1000, depth: 64, nodes: 300000, string: 1024 * 1024 });
export const COLLECTIONS = Object.freeze(['sources', 'visits', 'keywords', 'downloads', 'diagnostics', 'links', 'prefetch', 'events', 'recycle_bin', 'usb_registry', 'recent_doc_keys', 'recent_docs', 'application_mru_keys', 'application_mru', 'jump_lists', 'jump_list_entries', 'shellbag_views', 'shellbag_keys', 'shellbag_entries', 'dialog_mru_keys', 'dialog_mru_entries', 'userassist_keys', 'userassist_entries', 'run_mru_keys', 'run_mru_entries', 'explorer_history_keys', 'explorer_history_entries', 'system_info', 'sam_accounts', 'sam_name_mappings']);
export const LABELS = Object.freeze({visits:'방문 기록', keywords:'검색어 후보', downloads:'다운로드 기록', links:'바로가기', prefetch:'Prefetch', events:'이벤트', recycle_bin:'휴지통 메타데이터', usb_registry:'USB 관측', recent_doc_keys:'RecentDocs 키',recent_docs:'RecentDocs', application_mru_keys:'애플리케이션 MRU 키',application_mru:'애플리케이션 MRU',jump_lists:'Jump List 컨테이너',jump_list_entries:'Jump List 항목',shellbag_views:'ShellBag 뷰',shellbag_keys:'ShellBag 키',shellbag_entries:'ShellBag 항목',dialog_mru_keys:'대화상자 MRU 키',dialog_mru_entries:'대화상자 MRU',userassist_keys:'UserAssist 키',userassist_entries:'UserAssist',run_mru_keys:'RunMRU 키',run_mru_entries:'RunMRU',explorer_history_keys:'탐색기 이력 키',explorer_history_entries:'탐색기 이력',system_info:'시스템 정보',sam_accounts:'SAM 계정 메타데이터',sam_name_mappings:'SAM 이름 매핑'});
export function check(condition, message) { if (!condition) throw new Error(message); }
const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const validId = v => (typeof v==='string'&&v.length>0&&v.length<=256)||(Number.isSafeInteger(v)&&v>0);
export const sourceKey = value => String(value);
export const textValue = value => value === null || value === undefined ? '' : typeof value === 'object' ? JSON.stringify(value) : String(value);
function checkStructure(text) {
  let depth=0, quoted=false, escaped=false, stringLength=0;
  for (let i=0;i<text.length;i++) {
    const c=text[i];
    if (quoted) { stringLength++; check(stringLength <= LIMITS.string * 6, '문자열이 표시 한도를 초과합니다.'); if(escaped) escaped=false; else if(c==='\\') escaped=true; else if(c==='"') quoted=false; }
    else if(c==='"') {quoted=true;stringLength=0;}
    else if(c==='{'||c==='[') check(++depth<=LIMITS.depth,'JSON 중첩이 64단계를 초과합니다.');
    else if(c==='}'||c===']') depth--;
  }
}
export function parseReport(text) {
  check(typeof text==='string' && text.length<=LIMITS.bytes && new TextEncoder().encode(text).byteLength<=LIMITS.bytes, '보고서는 16 MiB 이하의 UTF-8 JSON이어야 합니다.');
  checkStructure(text);
  let report;
  try { report=JSON.parse(text); } catch { throw new Error('올바른 JSON 보고서가 아닙니다.'); }
  const stack=[report]; let nodes=0;
  while(stack.length) {
    const value=stack.pop();check(++nodes<=LIMITS.nodes,'JSON 항목 수가 표시 한도를 초과합니다.');
    if(typeof value==='number') check(Number.isFinite(value)&&Math.abs(value)<=Number.MAX_SAFE_INTEGER,'정확히 표시할 수 없는 숫자가 있습니다. 원본 CLI 보고서를 사용하세요.');
    if(typeof value==='string') check(value.length<=LIMITS.string,'문자열이 표시 한도를 초과합니다.');
    if(value!==null && typeof value==='object') {const values=Object.values(value);check(values.length+nodes<=LIMITS.nodes,'JSON 항목 수가 표시 한도를 초과합니다.');for(const child of values)stack.push(child);}
  }
  check(object(report)&&report.tool==='plaintrace'&&report.format_version===15,'Plaintrace 스키마 15 보고서만 열 수 있습니다.');
  check(object(report.counts),'보고서 counts가 없습니다.');
  let total=0;
  for(const name of COLLECTIONS) { check(Array.isArray(report[name]),`보고서 컬렉션이 없습니다: ${name}`); total+=report[name].length; check(total<=LIMITS.rows,'전체 레코드 100,000개 표시 한도를 초과합니다.'); check(report.counts[name]===report[name].length,`레코드 개수가 맞지 않습니다: ${name}`); }
  check(report.sources.length<=LIMITS.sources,'소스 1,000개 표시 한도를 초과합니다.');
  const sources=new Map();
  for(const source of report.sources) {check(object(source)&&validId(source.source_id)&&typeof source.path==='string', '유효하지 않은 소스 식별자 또는 경로입니다.');for(const key of ['schema_family','source_kind','browser','sha256','database_sha256','wal_sha256'])check(source[key]===null||source[key]===undefined||typeof source[key]==='string',`소스 필드 타입이 맞지 않습니다: ${key}`);const id=sourceKey(source.source_id);check(!sources.has(id),'중복된 source_id가 있습니다.');sources.set(id,source);}
  const rows=new Map([...sources.keys()].map(id=>[id,[]]));const warnings=new Map([...sources.keys()].map(id=>[id,[]]));
  for(const name of COLLECTIONS.filter(n=>n!=='sources')) for(const row of report[name]) {check(object(row)&&Object.hasOwn(row,'source_id')&&validId(row.source_id)&&sources.has(sourceKey(row.source_id)),`소스 참조가 유효하지 않습니다: ${name}`); const id=sourceKey(row.source_id); (name==='diagnostics'?warnings:rows).get(id).push(name==='diagnostics'?row:{collection:name,record:row});}
  return {report,sources,rows,warnings};
}
export function family(source) { if(source.schema_family==='chromium'||source.schema_family==='firefox'||source.browser) return 'browser'; if(/^(registry_|evtx|lnk|prefetch|recycle|jump|shellbag)/.test(source.schema_family||'')||/^(lnk|prefetch|evtx|recycle_bin|usb_|recent_|application_|jump_|shellbag|dialog_|userassist|run_mru|typed_paths|word_wheel|system_info|sam_)/.test(source.source_kind||'')) return 'windows'; return 'other'; }
export function fileName(path) {return typeof path==='string'?path.split(/[\\/]/).pop()||path:'소스 경로 없음';}
export function visibleSources(model, filter='all', query='') {const q=query.trim().toLocaleLowerCase();return [...model.sources.values()].filter(s=>(filter==='all'||family(s)===filter)&&[s.path,s.browser,s.source_kind,s.source_id].some(v=>textValue(v).toLocaleLowerCase().includes(q)));}
export function description(row) {const r=row.record;if(r.event_id!==undefined&&r.event_id!==null)return `${textValue(r.provider||'Event')} / ${textValue(r.event_id)}`;return textValue(r.title||r.url||r.original_path||r.path||r.executable||r.command||r.value_name||r.key_path||r.account_name||r.name||r.record_id||'원시 레코드');}
const TIME_FIELDS={visits:[['visited_at','방문 기록']],keywords:[['searched_at','검색어 후보 · time_basis 확인']],downloads:[['started_at','다운로드 시작 기록'],['ended_at','다운로드 종료 기록']],events:[['created_at','이벤트 SystemTime']],recycle_bin:[['deleted_at','삭제 메타데이터 시각']]};
export function timeline(model, selected=null) {
  const items=[];
  for(const [id, rows] of model.rows) {if(selected!==null&&id!==selected)continue;for(const row of rows){for(const [field,baseLabel] of TIME_FIELDS[row.collection]||[]){const value=row.record[field];if(typeof value==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,7})?Z$/.test(value)&&Number.isFinite(Date.parse(value))&&new Date(value.slice(0,19)+'Z').toISOString().slice(0,19)===value.slice(0,19)){const label=row.collection==='visits'&&row.record.record_kind==='url_summary'?'URL 요약 시각 · 개별 방문 아님':baseLabel;items.push({sourceId:id,row,time:value,field,label});}}}}
  // Normalized UTC strings use differing fractions: pad to 7 digits without
  // converting to milliseconds, retaining 100 ns ordering where present.
  const key=t=>t.replace(/(?:\.(\d+))?Z$/,(_,f='')=>'.'+f.padEnd(7,'0')+'Z');
  return items.sort((a,b)=>key(a.time).localeCompare(key(b.time)));
}
export function page(items, number=0, size=25) {const pages=Math.max(1,Math.ceil(items.length/size));const index=Math.min(Math.max(0,number),pages-1);return {items:items.slice(index*size,(index+1)*size),index,pages,total:items.length};}
export function rawRecord(row) {return JSON.stringify(row.record,null,2);}
