"""Generated REGF and fixed byte-offset oracles; never live user evidence."""
from contextlib import closing, redirect_stdout, redirect_stderr
import codecs
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
from plaintrace import userassist as ua
from plaintrace.registry_hive import Hive
from plaintrace.model import Report
from plaintrace.execution import analyze
from plaintrace.exports import write_report
from plaintrace.cli import main
from plaintrace.evidence import AnalysisError
from test_usb_registry_cli import hive_fixture, value, checksum, FT, UTC

BASE=ua.KEY_PATH
G3='{75048700-EF1F-11D0-9888-006097DEACF9}'
G5='{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}'

def version(number):return value('Version',4,struct.pack('<I',number),True)
def entry(name,data,kind=3):return value(codecs.encode(name,'rot13'),kind,data)
def v3(count=8,ticks=FT):return struct.pack('<IIQ',7,count,ticks)
def v5(count=9,ticks=FT):return struct.pack('<IIII',0xffffffff,count,12,3456)+bytes(range(44))+struct.pack('<QI',ticks,0xffffffff)
def paths():return {BASE+'\\'+G3:[version(3)],BASE+'\\'+G3+'\\Count':[entry('UEME_RUNPATH:C:\\문서😀.exe',v3())],BASE+'\\'+G5:[version(5)],BASE+'\\'+G5+'\\Count':[entry(r'{ABC}\Program.exe',v5()),entry('UEME_CTLSESSION',bytes(1612))]}

class UserAssistTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def file(self,name,data):p=self.folder/name;p.write_bytes(data);return p
    def parse(self,p=None,**kwargs):
        report=Report();keys,rows=ua.analyze_hive(hive_fixture(paths() if p is None else p,**kwargs),1,report);return keys,rows,report
    def codes(self,report):return {r['code'] for r in report.diagnostics}

    def test_v3_offsets_unicode_and_unadjusted_count(self):
        keys,rows,_=self.parse();row=rows[0]
        self.assertEqual((row['first_dword_raw'],row['run_count_raw'],row['focus_count_raw']),(7,8,None))
        self.assertEqual(row['decoded_name'],'UEME_RUNPATH:C:\\문서😀.exe');self.assertEqual(row['last_run_at'],UTC)
        self.assertEqual(row['last_run_filetime_raw'],str(FT));self.assertEqual(row['value_data_hex'],v3().hex())
        self.assertNotIn('user_sid',row);self.assertNotIn('executed',row)

    def test_v5_metrics_and_opaque_ranges_are_exact(self):
        _,rows,_=self.parse();row=rows[1]
        self.assertEqual((row['first_dword_raw'],row['run_count_raw'],row['focus_count_raw'],row['focus_time_raw']),(0xffffffff,9,12,3456))
        self.assertEqual(row['opaque_data_hex'],(bytes(range(44))+b'\xff'*4).hex());self.assertEqual(row['last_run_at'],UTC)
        self.assertEqual(row['decoded_name'],r'{ABC}\Program.exe')

    def test_session_control_never_becomes_run_record(self):
        _,rows,r=self.parse();row=rows[2]
        self.assertEqual(row['status'],'session_control');self.assertIsNone(row['run_count_raw']);self.assertEqual(len(bytes.fromhex(row['opaque_data_hex'])),1612)
        self.assertIn('userassist_session_control',self.codes(r))

    def test_session_control_name_case_and_entry_sized_payload(self):
        p=paths();p[BASE+'\\'+G3+'\\Count']=[entry('ueme_ctlsession',v3())]
        _,rows,_=self.parse(p);self.assertEqual(rows[0]['status'],'session_control');self.assertIsNone(rows[0]['last_run_at'])

    def test_zero_and_out_of_range_filetimes(self):
        p=paths();p[BASE+'\\'+G3+'\\Count']=[entry('zero',v3(ticks=0)),entry('bad',v3(ticks=2**64-1))]
        _,rows,r=self.parse(p);self.assertIsNone(rows[0]['last_run_at']);self.assertEqual(rows[0]['last_run_filetime_raw'],'0')
        self.assertIsNone(rows[1]['last_run_at']);self.assertIn('invalid_filetime',self.codes(r))

    def test_unsigned_counts_and_no_legacy_bias_correction(self):
        p=paths();p[BASE+'\\'+G3+'\\Count']=[entry(str(n),v3(n)) for n in (0,5,6,0xffffffff)]
        _,rows,_=self.parse(p);self.assertEqual([x['run_count_raw'] for x in rows[:4]],[0,5,6,0xffffffff])

    def test_noencrypt_one_preserves_plain_names_and_control(self):
        p=paths();p[BASE+'\\Settings']=[value('NoEncrypt',4,struct.pack('<I',1))]
        p[BASE+'\\'+G3+'\\Count']=[value('Plain.exe',3,v3()),value('UEME_CTLSESSION',3,bytes(8))]
        _,rows,_=self.parse(p);self.assertEqual(rows[0]['decoded_name'],'Plain.exe');self.assertEqual(rows[0]['name_encoding'],'plain');self.assertEqual(rows[1]['status'],'session_control')

    def test_noencrypt_zero_default_and_nonascii_names(self):
        p=paths();p[BASE+'\\Settings']=[value('NoEncrypt',4,bytes(4))]
        _,rows,_=self.parse(p);self.assertEqual(rows[0]['name_encoding'],'rot13');self.assertIn('문서😀',rows[0]['decoded_name'])

    def test_invalid_noencrypt_does_not_guess_names_or_controls(self):
        for kind,data in ((4,b'\x02\0\0\0'),(3,bytes(4)),(4,b'\0')):
            p=paths();p[BASE+'\\Settings']=[value('NoEncrypt',kind,data)]
            _,rows,r=self.parse(p);self.assertTrue(all(x['decoded_name'] is None for x in rows));self.assertTrue(all(x['run_count_raw'] is None for x in rows));self.assertIn('userassist_invalid_noencrypt',self.codes(r))

    def test_missing_version_retains_values_without_size_guessing(self):
        p=paths();p[BASE+'\\'+G3]=[];_,rows,r=self.parse(p)
        self.assertEqual(rows[0]['status'],'unsupported_version');self.assertIsNone(rows[0]['run_count_raw']);self.assertEqual(rows[0]['value_data_hex'],v3().hex());self.assertIn('userassist_unsupported_version',self.codes(r))

    def test_unsupported_version_and_wrong_version_type(self):
        for control in (version(13),value('Version',3,struct.pack('<I',3)),value('Version',4,b'\x03')):
            p=paths();p[BASE+'\\'+G3]=[control];keys,rows,_=self.parse(p);self.assertEqual(rows[0]['status'],'unsupported_version');self.assertEqual(keys[1]['raw_values'][0]['data_hex'],control[2].hex())

    def test_wrong_size_truncation_tail_and_cross_version_rejected(self):
        for data in (b'',v3()[:-1],v3()+b'\0',v5()):
            p=paths();p[BASE+'\\'+G3+'\\Count']=[entry('app',data)];_,rows,r=self.parse(p)
            self.assertEqual(rows[0]['status'],'wrong_size');self.assertIsNone(rows[0]['last_run_at']);self.assertEqual(rows[0]['opaque_data_hex'],data.hex());self.assertIn('userassist_wrong_size',self.codes(r))

    def test_wrong_registry_type_not_parsed(self):
        p=paths();p[BASE+'\\'+G3+'\\Count']=[entry('app',v3(),1)];_,rows,r=self.parse(p)
        self.assertEqual(rows[0]['status'],'wrong_type');self.assertIn('userassist_wrong_type',self.codes(r))

    def test_keys_raw_metadata_parent_links_and_physical_offsets(self):
        p=paths();p[BASE]=[value('root-data',3,b'raw')];p[BASE+'\\Settings']=[value('NoLog',4,struct.pack('<I',1))]
        data=hive_fixture(p);keys,rows,_=self.parse(p);hive=Hive(data)
        ids={k['record_id'] for k in keys}
        for key in keys:
            self.assertEqual(key['record_id'],str(hive.open(key['key_path'])['offset']+4096));self.assertEqual(key['key_last_write_raw'],str(FT));self.assertEqual(key['key_last_written'],UTC)
            if key['parent_key_id']:self.assertIn(key['parent_key_id'],ids)
            for v in key['raw_values']:self.assertEqual(data[v['value_offset']+4:v['value_offset']+6],b'vk')
        for row in rows:self.assertIn(row['key_id'],ids);self.assertEqual(data[int(row['record_id'])+4:int(row['record_id'])+6],b'vk')
        self.assertEqual(keys[0]['raw_values'][0]['data_hex'],b'raw'.hex());self.assertEqual(len(rows),3)

    def test_absent_and_empty_supported_roots(self):
        k,e,r=self.parse({});self.assertFalse(k or e);self.assertIn('userassist_absent',self.codes(r))
        k,e,r=self.parse({BASE:[]});self.assertEqual(len(k),1);self.assertFalse(e or r.diagnostics)

    def test_unknown_guid_version_supported_without_identity_mapping(self):
        g='{11111111-2222-3333-4444-555555555555}';k,e,_=self.parse({BASE+'\\'+g:[version(3)],BASE+'\\'+g+'\\Count':[entry('%USERPROFILE%\\x.exe',v3())]})
        self.assertEqual(e[0]['group_guid'],g);self.assertEqual(e[0]['decoded_name'],'%USERPROFILE%\\x.exe');self.assertNotIn('application',e[0])

    def test_non_guid_children_missing_count_and_nested_scopes(self):
        p={BASE+'\\bad\\Count':[entry('ignored',v3())],BASE+'\\'+G3:[version(3)],BASE+'\\Settings\\deep':[],BASE+'\\'+G5:[version(5)],BASE+'\\'+G5+'\\Other':[],BASE+'\\'+G5+'\\Count\\deep':[entry('ignored',v5())]}
        _,rows,r=self.parse(p);self.assertFalse(rows);self.assertTrue({'userassist_nested_keys','userassist_missing_count','userassist_unsupported_scope'}<=self.codes(r))

    def test_case_insensitive_paths_versions_settings(self):
        p={BASE.lower()+'\\'+G3.lower():[value('vErSiOn',4,struct.pack('<I',3))],BASE.lower()+'\\'+G3.lower()+'\\cOuNt':[entry('App.exe',v3())],BASE.lower()+'\\sEtTiNgS':[value('nOeNcRyPt',4,bytes(4))]}
        _,rows,_=self.parse(p);self.assertEqual(rows[0]['status'],'parsed');self.assertEqual(rows[0]['decoded_name'],'App.exe')

    def test_all_regf_index_and_version_layouts(self):
        for index in (b'li',b'lf',b'lh',b'ri'):
            for minor in (3,4,5):self.assertEqual(len(self.parse(index_kind=index,minor=minor)[1]),3)

    def test_dirty_and_corrupt_hives_rejected(self):
        data=bytearray(hive_fixture(paths()));struct.pack_into('<I',data,4,2)
        for raw in (checksum(data),b'regf',b'bad'):
            with self.assertRaises(AnalysisError):ua.analyze_hive(raw,1,Report())

    def test_key_entry_and_output_budgets(self):
        for constant in ('MAX_KEYS','MAX_ENTRIES','MAX_OUTPUT_BYTES'):
            with patch.object(ua,constant,1),self.assertRaises(AnalysisError):self.parse()

    def test_duplicate_values_and_aliases_rejected(self):
        p=paths();p[BASE+'\\'+G3].append(value('VERSION',4,struct.pack('<I',3)))
        with self.assertRaises(AnalysisError):self.parse(p)

    def test_json_sqlite_schema_and_foreign_keys(self):
        f=self.file('NTUSER',hive_fixture(paths()));report=analyze(userassist_hives=[f]);j=self.folder/'out.json';s=self.folder/'out.sqlite'
        write_report(report,j);write_report(report,s,'sqlite');payload=json.loads(j.read_text());self.assertEqual(payload['format_version'],11)
        self.assertEqual(payload['userassist_entries'],report.userassist_entries)
        with closing(sqlite3.connect(s)) as db:
            self.assertEqual(db.execute('pragma user_version').fetchone()[0],11);self.assertEqual(db.execute('pragma foreign_key_check').fetchall(),[])
            self.assertEqual(db.execute('select last_run_filetime_raw from userassist_entries order by rowid').fetchone()[0],str(FT))
            self.assertEqual(json.loads(db.execute("select raw_values from userassist_keys where key_role='count' order by rowid").fetchone()[0])[0]['data_hex'],v3().hex())
            db.execute('pragma foreign_keys=on')
            with self.assertRaises(sqlite3.IntegrityError):db.execute("update userassist_entries set key_id='missing'")

    def test_repeated_sources_hashes_and_input_unchanged(self):
        data=hive_fixture(paths());f=self.file('NTUSER',data);report=analyze(userassist_hives=[f,f]);self.assertEqual(len(report.userassist_entries),6)
        self.assertEqual([s['source_id'] for s in report.sources],[1,2]);self.assertTrue(all(s['sha256']==hashlib.sha256(data).hexdigest() and s['source_kind']=='userassist' for s in report.sources));self.assertEqual(f.read_bytes(),data)

    def test_cli_subprocess_json_strict_and_sqlite(self):
        f=self.file('NTUSER',hive_fixture(paths()));s=self.folder/'out.sqlite'
        for extra in ([],['--strict'],['--format','sqlite','--output',str(s)]):
            r=subprocess.run([sys.executable,'-m','plaintrace','--userassist',str(f),*extra],capture_output=True,text=True)
            self.assertEqual(r.returncode,1 if '--strict' in extra else 0,r.stderr)
            if '--format' not in extra:self.assertEqual(len(json.loads(r.stdout)['userassist_entries']),3)
        self.assertTrue(s.is_file())

    def test_mixed_dialog_and_userassist_sources(self):
        f=self.file('NTUSER',hive_fixture(paths()));r=analyze(dialog_hives=[f],userassist_hives=[f]);self.assertEqual([x['source_kind'] for x in r.sources],['dialog_mru','userassist']);self.assertTrue(all(x['source_id']==2 for x in r.userassist_entries))

    def test_fatal_later_input_publishes_no_partial_output(self):
        good=self.file('good',hive_fixture(paths()));bad=self.file('bad',b'bad');out=self.folder/'out.json'
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):code=main(['--userassist',str(good),'--userassist',str(bad),'--output',str(out)])
        self.assertEqual(code,2);self.assertFalse(out.exists());self.assertFalse(list(self.folder.glob('.plaintrace-*')))

    def test_evidence_and_existing_outputs_protected(self):
        data=hive_fixture(paths());f=self.file('NTUSER',data)
        for output in (f,self.file('report',b'keep'),self.folder/'NTUSER-wal'):
            with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):code=main(['--userassist',str(f),'--output',str(output)])
            self.assertEqual(code,2)
        self.assertEqual(f.read_bytes(),data);self.assertEqual((self.folder/'report').read_bytes(),b'keep')

    def test_missing_input_and_sqlite_destination_rejected(self):
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            self.assertEqual(main(['--userassist',str(self.folder/'missing')]),2)
            with self.assertRaises(SystemExit) as error:main(['--userassist','missing','--format','sqlite'])
        self.assertEqual(error.exception.code,2)

    def test_no_decoded_target_is_opened(self):
        f=self.file('NTUSER',hive_fixture(paths()));real=Path.open;opened=[]
        def tracked(path,*a,**kw):opened.append(str(path));return real(path,*a,**kw)
        with patch.object(Path,'open',tracked):analyze(userassist_hives=[f])
        self.assertTrue(opened);self.assertEqual(set(opened),{str(f.resolve())})

    def test_changed_input_hash_rejected(self):
        f=self.file('NTUSER',hive_fixture(paths()))
        with patch('plaintrace.binary.bounded_hash',side_effect=['first','second']),self.assertRaises(AnalysisError):analyze(userassist_hives=[f])

    def test_seeded_binary_payload_mutations_are_bounded(self):
        rng=random.Random(77)
        for _ in range(80):
            raw=bytes(rng.randrange(256) for _ in range(rng.randrange(90)))
            p={BASE+'\\'+G5:[version(5)],BASE+'\\'+G5+'\\Count':[entry('App.exe',raw)]}
            _,rows,_=self.parse(p);self.assertEqual(rows[0]['value_data_hex'],raw.hex());self.assertEqual(rows[0]['status'],'parsed' if len(raw)==72 else 'wrong_size')

if __name__=='__main__':unittest.main()
