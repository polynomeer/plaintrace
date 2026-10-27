import {COLLECTIONS} from './core.mjs';
// Authored synthetic UI examples. No acquired evidence or claimed source hash.
export function demoReport() {
  const report={tool:'plaintrace',tool_version:'0.15.0',format_version:15,counts:{}};
  for(const name of COLLECTIONS) report[name]=[];
  const source=(id,path,kind,family,browser=null)=>({source_id:id,path,source_kind:kind,schema_family:family,browser,sha256:null,database_sha256:null,wal_sha256:null});
  report.sources=[source(1,'/demo/windows/Chrome/History','browser','chromium','chromium'),source(2,'/demo/windows/Security.evtx','evtx','evtx'),source(3,'/demo/windows/SYSTEM','system_info_system','registry_system')];
  report.visits=[{source_id:1,browser:'chromium',record_id:'visits:41',source_table:'visits',record_kind:'visit',url:'https://example.org/docs',title:'Documentation overview',visited_at:'2026-10-27T10:24:08.123456Z',timestamp_raw:'13437570248123456',timestamp_unit:'chromium_us',transition:1},{source_id:1,browser:'chromium',record_id:'visits:42',source_table:'visits',record_kind:'visit',url:'https://example.org/reference',title:'Reference notes',visited_at:'2026-10-27T10:25:32.000000Z',timestamp_raw:'13437570332000000',timestamp_unit:'chromium_us',transition:1}];
  report.downloads=[{source_id:1,browser:'chromium',record_id:'downloads:7',source_table:'downloads',record_kind:'download',path:'C:\\Downloads\\reference.pdf',url:'https://example.org/reference.pdf',url_chain:['https://example.org/reference.pdf'],started_at:'2026-10-27T10:28:14.000000Z',ended_at:'2026-10-27T10:28:16.000000Z',start_time_basis:'recorded',total_bytes:24012,state:1}];
  report.events=[{source_id:2,record_id:'4608',provider:'Microsoft-Windows-Security-Auditing',channel:'Security',event_id:4624,created_at:'2026-10-27T10:23:10.000000Z',time_created_raw:'2026-10-27T10:23:10.0000000Z',container_filetime_raw:'134375701900000000',category:'logon',action:'logon',xml:'<Event><System><EventID>4624</EventID></System></Event>',details:{note:'Synthetic event for UI preview only'}}];
  report.system_info=[{source_id:3,record_id:'sys:1',field:'computer_name',value:'DEMO-WORKSTATION',key_path:'ControlSet001\\Control\\ComputerName\\ComputerName',key_last_written:null,key_last_write_raw:'0'}];
  report.diagnostics=[{source_id:3,severity:'warning',code:'demo_only',message:'합성 미리보기입니다. 실제 시스템이나 사용자를 나타내지 않습니다.',record_id:'sys:1'}];
  for(const name of COLLECTIONS) report.counts[name]=report[name].length;
  return report;
}
