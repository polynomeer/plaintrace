"""Synthetic SOFTWARE/SYSTEM fixtures and independent fixed time/value oracles."""
from contextlib import closing,redirect_stdout,redirect_stderr
import hashlib
import io
import json
from pathlib import Path
import random
import sqlite3
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from plaintrace import system_info as si
from plaintrace.registry_hive import Hive
from plaintrace.model import Report
from plaintrace.execution import analyze
from plaintrace.exports import write_report
from plaintrace.cli import main
from plaintrace.evidence import AnalysisError
from test_usb_registry_cli import hive_fixture,value,text,checksum,FT,UTC
OS=si.OS_PATH
CONTROL='ControlSet002'
NAME=CONTROL+r'\Control\ComputerName\ComputerName'
ACTIVE=CONTROL+r'\Control\ComputerName\ActiveComputerName'
TCP=CONTROL+r'\Services\Tcpip\Parameters'
TZ=CONTROL+r'\Control\TimeZoneInformation'
SHUT=CONTROL+r'\Control\Windows'

def dword(name,n):return value(name,4,struct.pack('<I',n&0xffffffff),True)
def software_paths():
    vals=[text(name,'value_'+name) for name in si.OS_STRINGS]
    vals += [dword('CurrentMajorVersionNumber',10),dword('CurrentMinorVersionNumber',0),dword('UBR',1234),dword('InstallDate',1577836800),value('InstallTime',11,struct.pack('<Q',FT)),value('DigitalProductId',3,b'opaque-license-bytes')]
    return {OS:vals}
def system_paths():return {'Select':[dword('Current',2),dword('Default',1),dword('LastKnownGood',1),dword('Failed',0)],NAME:[text('ComputerName','CONFIGURED')],ACTIVE:[text('ComputerName','ACTIVE')],TCP:[text('Hostname','host-a'),text('NV Hostname','host-b'),text('Domain','domain-a'),text('NV Domain','domain-b')],TZ:[text('TimeZoneKeyName','Korea Standard Time'),text('StandardName','한국 표준시😀'),text('DaylightName','일광 시간'),dword('Bias',-540),dword('ActiveTimeBias',-540),dword('StandardBias',0),dword('DaylightBias',-60),dword('DynamicDaylightTimeDisabled',1),dword('DisableAutoDaylightTimeSet',0)],SHUT:[value('ShutdownTime',3,struct.pack('<Q',FT))],r'ControlSet001\Control\ComputerName\ComputerName':[text('ComputerName','IGNORED')]}
def field(rows,kind,name):return next(v for r in rows if r['observation_kind']==kind for v in r['values'] if v['name'].casefold()==name.casefold())

class SystemInfoTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def file(self,name,data):p=self.folder/name;p.write_bytes(data);return p
    def parse(self,p=None,role='software',**kw):
        r=Report();rows=si.analyze_hive(hive_fixture((software_paths() if role=='software' else system_paths()) if p is None else p,**kw),role,1,r);return rows,r
    def codes(self,r):return {d['code'] for d in r.diagnostics}

    def test_software_version_owner_and_build_fields_kept_separate(self):
        rows,r=self.parse();self.assertEqual(len(rows),1);self.assertEqual(field(rows,'os_version','ProductName')['decoded'],'value_ProductName');self.assertEqual(field(rows,'os_version','CurrentMajorVersionNumber')['decoded'],10);self.assertEqual(field(rows,'os_version','UBR')['decoded'],1234);self.assertEqual(field(rows,'os_version','RegisteredOwner')['decoded'],'value_RegisteredOwner');self.assertFalse(r.diagnostics)
        self.assertNotIn('inferred_windows_version',rows[0]);self.assertIsNone(rows[0]['control_set'])

    def test_install_date_seconds_and_install_time_exact_filetime(self):
        rows,_=self.parse();sec=field(rows,'os_version','InstallDate');ft=field(rows,'os_version','InstallTime');self.assertEqual((sec['decoded'],sec['time_raw'],sec['time_unit'],sec['time']),(1577836800,'1577836800','unix_seconds','2020-01-01T00:00:00.000000Z'));self.assertEqual((ft['time_raw'],ft['time'],ft['time_unit']),(str(FT),UTC,'filetime_100ns'))

    def test_select_current_not_default_or_controlset001(self):
        rows,r=self.parse(role='system');self.assertEqual(len(rows),6);self.assertTrue(all(x['control_set']=='ControlSet002' for x in rows));self.assertEqual(field(rows,'computer_name','ComputerName')['decoded'],'CONFIGURED');self.assertNotIn('IGNORED',json.dumps(rows));self.assertFalse(r.diagnostics)

    def test_control_selection_metadata_and_conflicting_names_remain(self):
        rows,_=self.parse(role='system');self.assertEqual(field(rows,'control_set_selection','Default')['decoded'],1);self.assertEqual(field(rows,'active_computer_name','ComputerName')['decoded'],'ACTIVE');self.assertEqual(field(rows,'tcpip_parameters','Hostname')['decoded'],'host-a');self.assertEqual(field(rows,'tcpip_parameters','NV Hostname')['decoded'],'host-b');self.assertNotIn('effective_hostname',rows[0])

    def test_timezone_signed_biases_are_not_applied_to_timestamps(self):
        rows,_=self.parse(role='system');self.assertEqual(field(rows,'time_zone','Bias')['decoded'],-540);self.assertEqual(field(rows,'time_zone','Bias')['value_data_hex'],struct.pack('<i',-540).hex());self.assertEqual(field(rows,'time_zone','DaylightBias')['decoded'],-60);self.assertEqual(field(rows,'time_zone','StandardName')['decoded'],'한국 표준시😀');self.assertEqual(field(rows,'shutdown','ShutdownTime')['time'],UTC)

    def test_shutdown_binary_filetime_precision_and_no_boot_claim(self):
        rows,_=self.parse(role='system');v=field(rows,'shutdown','ShutdownTime');self.assertEqual((v['time_raw'],v['time'],v['decoded']),(str(FT),UTC,FT));self.assertNotIn('boot_time',rows[-1]);self.assertNotIn('uptime',rows[-1])

    def test_key_lastwrite_is_separate_from_embedded_times(self):
        rows,_=self.parse();self.assertEqual((rows[0]['key_last_written'],rows[0]['key_last_write_raw']),(UTC,str(FT)));self.assertNotEqual(field(rows,'os_version','InstallDate')['time'],rows[0]['key_last_written']);self.assertNotIn('time',rows[0])

    def test_opaque_unknown_and_license_values_never_decoded(self):
        p=software_paths();p[OS]+=[text('Unknown','literal'),value('DigitalProductId4',3,b'\xff'*32)];rows,_=self.parse(p)
        for name in ('DigitalProductId','DigitalProductId4','Unknown'):
            v=field(rows,'os_version',name);self.assertEqual(v['status'],'opaque');self.assertIsNone(v['decoded']);self.assertIsNone(v['time']);self.assertTrue(v['value_data_hex'])
        self.assertNotIn('product_key',rows[0])

    def test_strings_expandable_tokens_and_no_normalization(self):
        p=software_paths();p[OS]=[value('SystemRoot',2,('  %SYSTEMDRIVE%\\Windows\\..\0').encode('utf-16-le')),text('ProductName','Windows 10'),text('DisplayVersion','25H2')];rows,_=self.parse(p);self.assertEqual(field(rows,'os_version','SystemRoot')['decoded'],'  %SYSTEMDRIVE%\\Windows\\..');self.assertEqual(field(rows,'os_version','ProductName')['decoded'],'Windows 10')

    def test_unsigned_dword_maximum_and_zero(self):
        rows,_=self.parse({OS:[dword('UBR',0xffffffff),dword('CurrentMajorVersionNumber',0)]});self.assertEqual(field(rows,'os_version','UBR')['decoded'],4294967295);self.assertEqual(field(rows,'os_version','CurrentMajorVersionNumber')['decoded'],0)

    def test_zero_and_overflow_filetimes_retained(self):
        for number in (0,2**64-1):
            rows,r=self.parse({OS:[value('InstallTime',11,struct.pack('<Q',number)),dword('InstallDate',0)]});self.assertIsNone(field(rows,'os_version','InstallTime')['time']);self.assertEqual(field(rows,'os_version','InstallTime')['time_raw'],str(number));self.assertIsNone(field(rows,'os_version','InstallDate')['time'])
            if number:self.assertIn('invalid_filetime',self.codes(r))

    def test_wrong_types_not_coerced_for_known_fields(self):
        rows,r=self.parse({OS:[value('ProductName',3,b'raw'),text('UBR','123'),value('InstallDate',11,bytes(8)),value('InstallTime',3,bytes(8))]});self.assertTrue(all(v['status']=='wrong_type' and v['decoded'] is None for v in rows[0]['values']));self.assertIn('system_info_wrong_type',self.codes(r))

    def test_wrong_numeric_sizes_and_trailing_bytes_not_recovered(self):
        for name,kind,raw in (('UBR',4,b'\1'),('UBR',4,bytes(5)),('InstallTime',11,bytes(7)),('InstallTime',11,bytes(9))):
            rows,r=self.parse({OS:[value(name,kind,raw)]});v=rows[0]['values'][0];self.assertEqual(v['status'],'wrong_size');self.assertIsNone(v['time_raw']);self.assertEqual(v['value_data_hex'],raw.hex())
        p=system_paths();p[SHUT]=[value('ShutdownTime',11,bytes(8))];rows,_=self.parse(p,'system');self.assertEqual(field(rows,'shutdown','ShutdownTime')['status'],'wrong_type')

    def test_unterminated_odd_empty_and_invalid_utf16(self):
        for raw,status in ((b'','unterminated'),(b'x\0','unterminated'),(b'x\0z','unterminated'),(bytes(2),'empty'),(b'\0\xd8\0\0','invalid_text')):
            rows,_=self.parse({OS:[value('ProductName',1,raw)]});v=rows[0]['values'][0];self.assertEqual(v['status'],status);self.assertEqual(v['value_data_hex'],raw.hex())
            if status=='invalid_text':self.assertEqual(v['decoded'],r'\x00\xd8')

    def test_aligned_terminators_tails_and_invalid_status_precedence(self):
        for raw,status,decoded in (('Āx\0'.encode('utf-16-le')+b'\0x','trailing','Āx'),(b'\0\xd8\0\0x','invalid_text',r'\x00\xd8')):
            rows,r=self.parse({OS:[value('ProductName',1,raw)]});v=rows[0]['values'][0];self.assertEqual((v['status'],v['decoded']),(status,decoded));self.assertTrue(v['trailing_data_hex']);self.assertIn('system_info_trailing_data',self.codes(r))

    def test_missing_software_branch_and_optional_fields_diagnosed(self):
        rows,r=self.parse({});self.assertFalse(rows);self.assertIn('system_info_branch_absent',self.codes(r))
        rows,r=self.parse({OS:[]});self.assertEqual(len(rows),1);self.assertFalse(rows[0]['values']);self.assertIn('system_info_fields_absent',self.codes(r))

    def test_missing_optional_system_branches_no_invented_rows(self):
        p={'Select':[dword('Current',2)],CONTROL:[]};rows,r=self.parse(p,'system');self.assertEqual([x['observation_kind'] for x in rows],['control_set_selection']);self.assertIn('system_info_branch_absent',self.codes(r))

    def test_missing_invalid_or_unavailable_control_selection_fatal(self):
        for p in ({},{'Select':[]},{'Select':[text('Current','2')]},{'Select':[value('Current',4,b'\2')]},{'Select':[dword('Current',0)]},{'Select':[dword('Current',1000)]},{'Select':[dword('Current',2)],'ControlSet001':[]}):
            with self.assertRaises(AnalysisError):self.parse(p,'system')

    def test_high_controlset_and_case_insensitive_names(self):
        p={k.replace(CONTROL,'ControlSet047').lower():v for k,v in system_paths().items() if not k.startswith('ControlSet001')};p['select']=[dword('cUrReNt',47)];rows,_=self.parse(p,'system');self.assertTrue(all(r['control_set']=='ControlSet047' for r in rows));self.assertEqual(field(rows,'computer_name','ComputerName')['decoded'],'CONFIGURED')

    def test_nested_scopes_not_traversed_and_roles_not_auto_detected(self):
        rows,_=self.parse({OS+'\\Nested':[text('ProductName','ignored')]});self.assertEqual(len(rows),1);self.assertFalse(rows[0]['values'])
        with self.assertRaises(AnalysisError):self.parse(software_paths(),'system')
        rows,_=self.parse(system_paths(),'software');self.assertFalse(rows)
        with self.assertRaises(AnalysisError):self.parse(role='ntuser')

    def test_physical_key_and_value_offsets_raw_bytes(self):
        p=system_paths();data=hive_fixture(p);h=Hive(data);rows,_=self.parse(p,'system')
        for row in rows:
            self.assertEqual(int(row['record_id']),h.open(row['key_path'])['offset']+4096)
            for v in row['values']:
                self.assertEqual(data[v['value_offset']+4:v['value_offset']+6],b'vk');original=next(x for x in h.values(h.open(row['key_path'])) if x['name']==v['name']);self.assertEqual(v['value_data_hex'],original['raw'].hex())

    def test_all_regf_versions_indexes_and_duplicate_names(self):
        for index in (b'li',b'lf',b'lh',b'ri'):
            for minor in (3,4,5):self.assertEqual(len(self.parse(index_kind=index,minor=minor)[0]),1)
        with self.assertRaises(AnalysisError):self.parse({OS:[text('ProductName','x'),text('PRODUCTNAME','y')]})

    def test_dirty_and_corrupt_hives_rejected(self):
        data=bytearray(hive_fixture(software_paths()));struct.pack_into('<I',data,4,2)
        for raw in (b'bad',b'regf',checksum(data)):
            with self.assertRaises(AnalysisError):si.analyze_hive(raw,'software',1,Report())

    def test_observation_value_string_output_budgets(self):
        for constant in ('MAX_OBSERVATIONS','MAX_VALUES','MAX_STRING_UNITS','MAX_OUTPUT_BYTES'):
            with patch.object(si,constant,0),self.assertRaises(AnalysisError):self.parse()
        with patch.object(si,'MAX_STRING_UNITS',2):
            self.assertEqual(self.parse({OS:[text('ProductName','😀')]})[0][0]['values'][0]['decoded'],'😀')
            with self.assertRaises(AnalysisError):self.parse({OS:[text('ProductName','😀x')]})

    def test_json_sqlite_schema_values_and_foreign_keys(self):
        f=self.file('SOFTWARE',hive_fixture(software_paths()));r=analyze(system_info_hives=[('software',f)]);j=self.folder/'out.json';s=self.folder/'out.sqlite';write_report(r,j);write_report(r,s,'sqlite');p=json.loads(j.read_text());self.assertEqual(p['format_version'],15);self.assertEqual(p['system_info'],r.system_info)
        with closing(sqlite3.connect(s)) as db:
            self.assertEqual(db.execute('pragma user_version').fetchone()[0],15);self.assertEqual(db.execute('pragma foreign_key_check').fetchall(),[]);self.assertEqual(json.loads(db.execute('select values_json from system_info').fetchone()[0]),r.system_info[0]['values']);db.execute('pragma foreign_keys=on')
            with self.assertRaises(sqlite3.IntegrityError):db.execute('update system_info set source_id=999')

    def test_repeated_hives_source_hashes_and_input_bytes(self):
        data=hive_fixture(software_paths());f=self.file('renamed',data);r=analyze(system_info_hives=[('software',f),('software',f)]);self.assertEqual([s['source_id'] for s in r.sources],[1,2]);self.assertEqual(len(r.system_info),2);self.assertTrue(all(s['sha256']==hashlib.sha256(data).hexdigest() and s['source_kind']=='system_info' for s in r.sources));self.assertEqual(f.read_bytes(),data)

    def test_cli_roles_source_order_json_and_sqlite(self):
        f=self.file('software',hive_fixture(software_paths()));g=self.file('system',hive_fixture(system_paths()));out=self.folder/'out.sqlite';args=[sys.executable,'-m','plaintrace','--system-info-system',str(g),'--system-info-software',str(f),'--system-info-software',str(f)]
        r=subprocess.run(args,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);p=json.loads(r.stdout);self.assertEqual([s['schema_family'] for s in p['sources']],['registry_software','registry_software','registry_system']);self.assertEqual(len(p['system_info']),8)
        r=subprocess.run(args+['--format','sqlite','--output',str(out)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)

    def test_mixed_adapters_do_not_join_host_or_user(self):
        f=self.file('SOFTWARE',hive_fixture(software_paths()));r=analyze(explorer_hives=[('typed_paths',f)],system_info_hives=[('software',f)]);self.assertEqual([s['source_kind'] for s in r.sources],['typed_paths','system_info']);self.assertEqual(r.system_info[0]['source_id'],2);self.assertNotIn('user_sid',r.system_info[0])

    def test_strict_warning_and_fatal_later_input_atomic(self):
        f=self.file('software',hive_fixture({OS:[]}));bad=self.file('bad',b'bad');out=self.folder/'out.json'
        with redirect_stdout(io.StringIO()) as stdout,redirect_stderr(io.StringIO()):self.assertEqual(main(['--system-info-software',str(f),'--strict']),1)
        self.assertEqual(len(json.loads(stdout.getvalue())['system_info']),1)
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):self.assertEqual(main(['--system-info-software',str(f),'--system-info-system',str(bad),'--output',str(out)]),2)
        self.assertFalse(out.exists());self.assertFalse(list(self.folder.glob('.plaintrace-*')))

    def test_input_existing_output_and_sidecar_protection(self):
        data=hive_fixture(software_paths());f=self.file('SOFTWARE',data);out=self.file('out',b'keep')
        for dest in (f,out,self.folder/'SOFTWARE-wal'):
            with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):self.assertEqual(main(['--system-info-software',str(f),'--output',str(dest)]),2)
        self.assertEqual(f.read_bytes(),data);self.assertEqual(out.read_bytes(),b'keep')

    def test_missing_input_and_sqlite_destination(self):
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            self.assertEqual(main(['--system-info-software',str(self.folder/'missing')]),2)
            with self.assertRaises(SystemExit) as error:main(['--system-info-system','missing','--format','sqlite'])
        self.assertEqual(error.exception.code,2)

    def test_only_supplied_files_opened_and_changes_rejected(self):
        f=self.file('SOFTWARE',hive_fixture(software_paths()));real=Path.open;opened=[]
        def track(p,*a,**kw):opened.append(str(p));return real(p,*a,**kw)
        with patch.object(Path,'open',track):analyze(system_info_hives=[('software',f)])
        self.assertEqual(set(opened),{str(f.resolve())})
        with patch('plaintrace.binary.bounded_hash',side_effect=['first','second']),self.assertRaises(AnalysisError):analyze(system_info_hives=[('software',f)])

    def test_seeded_shutdown_payload_mutations_are_controlled(self):
        rng=random.Random(41)
        for _ in range(60):
            raw=bytes(rng.randrange(256) for _ in range(rng.randrange(20)));p=system_paths();p[SHUT]=[value('ShutdownTime',3,raw)];rows,_=self.parse(p,'system');v=field(rows,'shutdown','ShutdownTime');self.assertEqual(v['value_data_hex'],raw.hex());self.assertEqual(v['status'],'parsed' if len(raw)==8 else 'wrong_size')

if __name__=='__main__':unittest.main()
