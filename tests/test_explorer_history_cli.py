"""Synthetic Explorer address/search REGF fixtures, never acquired user data."""
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
from plaintrace import explorer_history as eh
from plaintrace.registry_hive import Hive
from plaintrace.model import Report
from plaintrace.execution import analyze
from plaintrace.exports import write_report
from plaintrace.cli import main
from plaintrace.evidence import AnalysisError
from test_usb_registry_cli import hive_fixture,value,text,checksum,FT,UTC
T=eh.BASE+'\\TypedPaths';W=eh.BASE+'\\WordWheelQuery'

def order(*numbers):return value('MRUListEx',3,b''.join(struct.pack('<I',n) for n in numbers)+b'\xff'*4)
def query(name,s):return value(name,3,(s+'\0').encode('utf-16-le'))
def paths():return {T:[text('url9',r'  %USERPROFILE%\문서😀 '),text('url1',r'\\server\share')],W:[query('8','문서😀'),query('2','name:*.doc OR report'),order(2,8)]}

class ExplorerHistoryTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def file(self,name,data):p=self.folder/name;p.write_bytes(data);return p
    def parse(self,p=None,artifact='typed_paths',**kw):
        r=Report();keys,entries=eh.analyze_hive(hive_fixture(paths() if p is None else p,**kw),artifact,1,r);return keys,entries,r
    def codes(self,r):return {d['code'] for d in r.diagnostics}

    def test_typed_unicode_slots_not_mru_ranks(self):
        k,e,r=self.parse();self.assertEqual(k[0]['mru_status'],'not_applicable');self.assertEqual([x['slot_number'] for x in e],[9,1]);self.assertTrue(all(x['mru_rank'] is None for x in e));self.assertEqual(e[0]['stored_text'],r'  %USERPROFILE%\문서😀 ');self.assertFalse(r.diagnostics)

    def test_wordwheel_binary_unicode_and_order(self):
        k,e,r=self.parse(artifact='word_wheel_query');self.assertEqual(k[0]['mru_order'],[2,8]);self.assertEqual([x['mru_rank'] for x in e],[1,0]);self.assertEqual([x['stored_text'] for x in e],['문서😀','name:*.doc OR report']);self.assertFalse(r.diagnostics)

    def test_literals_duplicates_and_no_path_or_query_normalization(self):
        for artifact,path,make in (('typed_paths',T,text),('word_wheel_query',W,query)):
            content=['  x\n\t',r'https://a.invalid/?q=x%20y',r'..\x',r'cmd\1','same','same']
            p={path:[make('url'+str(i) if path==T else str(i),s) for i,s in enumerate(content)]}
            if path==W:p[path].append(order(*range(6)))
            _,e,_=self.parse(p,artifact);self.assertEqual([x['stored_text'] for x in e],content);self.assertTrue(all('visited_at' not in x and 'searched_at' not in x for x in e))

    def test_wordwheel_missing_refs_keep_rank_gaps(self):
        k,e,r=self.parse({W:[query('2','a'),query('8','b'),order(99,8,7,2)]},'word_wheel_query');self.assertEqual([x['mru_rank'] for x in e],[3,1]);self.assertEqual(k[0]['mru_order'],[99,8,7,2]);self.assertIn('explorer_history_missing_entry',self.codes(r))

    def test_wordwheel_unlisted_entries_keep_null_rank(self):
        _,e,r=self.parse({W:[query('2','a'),query('8','b'),order(2)]},'word_wheel_query');self.assertIsNone(e[1]['mru_rank']);self.assertIn('explorer_history_unlisted_entry',self.codes(r))

    def test_missing_control_no_size_or_slot_rank_guess(self):
        k,e,r=self.parse({W:[query('8','a'),query('2','b')]},'word_wheel_query');self.assertEqual(k[0]['mru_status'],'missing');self.assertTrue(all(x['mru_rank'] is None for x in e));self.assertIn('explorer_history_missing_mru',self.codes(r))

    def test_invalid_mrulistex_type_alignment_sentinel_duplicates(self):
        raws=[(1,b'\xff'*4),(3,b''),(3,b'\xff'*3),(3,struct.pack('<II',2,8)),(3,struct.pack('<III',2,2,0xffffffff)),(3,struct.pack('<III',0xffffffff,2,0xffffffff))]
        for kind,raw in raws:
            k,e,r=self.parse({W:[query('2','a'),value('MRUListEx',kind,raw)]},'word_wheel_query');self.assertEqual(k[0]['mru_status'],'invalid');self.assertIsNone(e[0]['mru_rank']);self.assertIn('explorer_history_invalid_mru',self.codes(r))

    def test_legacy_and_ambiguous_controls_not_selected(self):
        for controls,status in (([text('MRUList','a')],'unsupported'),([text('MRUList','a'),order(2)],'ambiguous')):
            k,e,_=self.parse({W:[query('2','x')]+controls},'word_wheel_query');self.assertEqual(k[0]['mru_status'],status);self.assertIsNone(e[0]['mru_rank']);self.assertEqual(len(k[0]['control_values']),len(controls))

    def test_valid_empty_mru_differs_from_missing(self):
        k,e,r=self.parse({W:[order()]},'word_wheel_query');self.assertEqual(k[0]['mru_status'],'valid');self.assertFalse(e or r.diagnostics)

    def test_typed_unexpected_controls_never_add_ranks(self):
        k,e,r=self.parse({T:[text('url1','x'),order(1),text('MRUList','a')]});self.assertEqual(k[0]['mru_status'],'not_applicable');self.assertIsNone(e[0]['mru_rank']);self.assertEqual(len(k[0]['control_values']),2);self.assertIn('explorer_history_unexpected_control',self.codes(r))

    def test_noncanonical_names_preserved_as_metadata(self):
        for artifact,path,names in (('typed_paths',T,['url01','url','url-1','url4294967295','url１','1','']),('word_wheel_query',W,['01','-1','4294967295','１','url1',''])):
            k,e,r=self.parse({path:[value(n,3,b'raw') for n in names]},artifact);self.assertFalse(e);self.assertEqual([v['name'] for v in k[0]['other_values']],names);self.assertIn('explorer_history_unknown_value',self.codes(r))

    def test_zero_and_maximum_slots_and_case_insensitive_names(self):
        k,e,_=self.parse({T.lower():[text('URL0','x'),text('Url4294967294','y')]});self.assertEqual([x['slot_number'] for x in e],[0,4294967294]);self.assertEqual(e[0]['value_name'],'URL0')
        k,e,_=self.parse({W.lower():[query('0','x'),value('mRuLiStEx',3,struct.pack('<II',0,0xffffffff))]},'word_wheel_query');self.assertEqual(e[0]['mru_rank'],0)

    def test_artifact_specific_registry_types_no_coercion(self):
        for artifact,path,name,kind in (('typed_paths',T,'url1',3),('word_wheel_query',W,'1',1)):
            _,e,r=self.parse({path:[value(name,kind,b'x\0\0\0')]},artifact);self.assertEqual(e[0]['status'],'wrong_type');self.assertIsNone(e[0]['stored_text']);self.assertIn('explorer_history_wrong_type',self.codes(r))

    def test_unterminated_and_odd_text_kept_raw(self):
        for raw in (b'',b'x\0',b'x\0a',b'\0'):
            for artifact,path,name,kind in (('typed_paths',T,'url1',1),('word_wheel_query',W,'1',3)):
                _,e,r=self.parse({path:[value(name,kind,raw)]},artifact);self.assertEqual(e[0]['status'],'unterminated');self.assertIsNone(e[0]['stored_text']);self.assertEqual(e[0]['value_data_hex'],raw.hex())

    def test_invalid_utf16_is_byte_escaped(self):
        _,e,r=self.parse({W:[value('0',3,b'\0\xd8\0\0'),order(0)]},'word_wheel_query');self.assertEqual(e[0]['stored_text'],r'\x00\xd8');self.assertEqual(e[0]['status'],'invalid_text');self.assertEqual(e[0]['text_utf16_hex'],'00d8')

    def test_aligned_terminator_tails_padding_and_status_precedence(self):
        for raw,expected,status in (('Āx\0'.encode('utf-16-le')+b'\0x','Āx','trailing'),(b'\0\0x','','trailing'),(b'\0\xd8\0\0x',r'\x00\xd8','invalid_text')):
            _,e,r=self.parse({T:[value('url1',1,raw)]});self.assertEqual((e[0]['stored_text'],e[0]['status']),(expected,status));self.assertTrue(e[0]['trailing_data_hex']);self.assertIn('explorer_history_trailing_data',self.codes(r))

    def test_empty_strings_retained_with_diagnostic(self):
        for artifact,path,v in (('typed_paths',T,text('url1','')),('word_wheel_query',W,query('1',''))):
            _,e,r=self.parse({path:[v]},artifact);self.assertEqual((e[0]['stored_text'],e[0]['status']),('','empty'));self.assertIn('explorer_history_empty_text',self.codes(r))

    def test_key_time_raw_offsets_and_entry_lineage(self):
        data=hive_fixture(paths());h=Hive(data)
        for artifact,path in (('typed_paths',T),('word_wheel_query',W)):
            k,e,_=self.parse(artifact=artifact);self.assertEqual((k[0]['key_last_written'],k[0]['key_last_write_raw']),(UTC,str(FT)));self.assertEqual(int(k[0]['record_id']),h.open(path)['offset']+4096)
            for row in e:self.assertEqual(data[int(row['record_id'])+4:int(row['record_id'])+6],b'vk');self.assertEqual(row['key_id'],k[0]['record_id']);self.assertNotIn('key_last_written',row)

    def test_absent_empty_roots_and_descendants(self):
        for artifact,path in (('typed_paths',T),('word_wheel_query',W)):
            k,e,r=self.parse({},artifact);self.assertFalse(k or e);self.assertIn('explorer_history_absent',self.codes(r))
            k,e,r=self.parse({path:[]},artifact);self.assertEqual(len(k),1);self.assertFalse(e)
            k,e,r=self.parse({path+'\\deep':[text('url1','ignored')]},artifact);self.assertFalse(e);self.assertIn('explorer_history_nested_keys',self.codes(r))

    def test_unknown_artifact_rejected(self):
        with self.assertRaises(AnalysisError):self.parse(artifact='other')

    def test_regf_versions_indexes_and_duplicate_names(self):
        for index in (b'li',b'lf',b'lh',b'ri'):
            for minor in (3,4,5):self.assertEqual(len(self.parse(index_kind=index,minor=minor)[1]),2)
        with self.assertRaises(AnalysisError):self.parse({T:[text('url1','x'),text('URL1','y')]})

    def test_dirty_and_corrupt_regf_rejected(self):
        data=bytearray(hive_fixture(paths()));struct.pack_into('<I',data,4,2)
        for raw in (b'bad',b'regf',checksum(data)):
            with self.assertRaises(AnalysisError):eh.analyze_hive(raw,'typed_paths',1,Report())

    def test_entry_string_and_output_limits(self):
        for constant in ('MAX_ENTRIES','MAX_STRING_UNITS','MAX_OUTPUT_BYTES'):
            with patch.object(eh,constant,1),self.assertRaises(AnalysisError):self.parse()
        with patch.object(eh,'MAX_STRING_UNITS',2):
            self.assertEqual(self.parse({T:[text('url1','😀')]})[1][0]['stored_text'],'😀')
            with self.assertRaises(AnalysisError):self.parse({T:[text('url1','😀x')]})

    def test_json_sqlite_schema_raw_values_and_foreign_keys(self):
        f=self.file('NTUSER',hive_fixture(paths()));r=analyze(explorer_hives=[('typed_paths',f),('word_wheel_query',f)]);j=self.folder/'out.json';s=self.folder/'out.sqlite';write_report(r,j);write_report(r,s,'sqlite');p=json.loads(j.read_text());self.assertEqual(p['format_version'],15);self.assertEqual(p['explorer_history_entries'],r.explorer_history_entries)
        with closing(sqlite3.connect(s)) as db:
            self.assertEqual(db.execute('pragma user_version').fetchone()[0],15);self.assertEqual(db.execute('pragma foreign_key_check').fetchall(),[]);self.assertEqual(db.execute('select count(*) from explorer_history_entries').fetchone()[0],4);db.execute('pragma foreign_keys=on')
            with self.assertRaises(sqlite3.IntegrityError):db.execute("update explorer_history_entries set key_id='missing'")

    def test_repeated_mixed_sources_hashes_and_input_preservation(self):
        data=hive_fixture(paths());f=self.file('renamed',data);r=analyze(run_mru_hives=[f],explorer_hives=[('typed_paths',f),('word_wheel_query',f),('typed_paths',f)]);self.assertEqual([s['source_kind'] for s in r.sources],['run_mru','typed_paths','word_wheel_query','typed_paths']);self.assertEqual(len(r.explorer_history_entries),6);self.assertTrue(all(s['sha256']==hashlib.sha256(data).hexdigest() for s in r.sources));self.assertEqual(f.read_bytes(),data)

    def test_cli_flags_source_groups_json_and_sqlite(self):
        f=self.file('NTUSER',hive_fixture(paths()));out=self.folder/'out.sqlite';args=[sys.executable,'-m','plaintrace','--word-wheel-query',str(f),'--typed-paths',str(f),'--typed-paths',str(f)]
        result=subprocess.run(args,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr);p=json.loads(result.stdout);self.assertEqual([s['source_kind'] for s in p['sources']],['typed_paths','typed_paths','word_wheel_query']);self.assertEqual(len(p['explorer_history_entries']),6)
        result=subprocess.run(args+['--format','sqlite','--output',str(out)],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr);self.assertTrue(out.is_file())

    def test_strict_warning_and_later_failure_atomic_publication(self):
        f=self.file('NTUSER',hive_fixture({W:[query('1','x')]}));bad=self.file('bad',b'bad');out=self.folder/'out.json'
        with redirect_stdout(io.StringIO()) as stdout,redirect_stderr(io.StringIO()):self.assertEqual(main(['--word-wheel-query',str(f),'--strict']),1)
        self.assertEqual(len(json.loads(stdout.getvalue())['explorer_history_entries']),1)
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):self.assertEqual(main(['--typed-paths',str(f),'--word-wheel-query',str(bad),'--output',str(out)]),2)
        self.assertFalse(out.exists());self.assertFalse(list(self.folder.glob('.plaintrace-*')))

    def test_input_existing_output_and_sidecar_protection(self):
        data=hive_fixture(paths());f=self.file('NTUSER',data);out=self.file('out',b'keep')
        for destination in (f,out,self.folder/'NTUSER-wal'):
            with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):self.assertEqual(main(['--typed-paths',str(f),'--output',str(destination)]),2)
        self.assertEqual(f.read_bytes(),data);self.assertEqual(out.read_bytes(),b'keep')

    def test_missing_input_and_sqlite_destination(self):
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            self.assertEqual(main(['--typed-paths',str(self.folder/'missing')]),2)
            with self.assertRaises(SystemExit) as error:main(['--word-wheel-query','missing','--format','sqlite'])
        self.assertEqual(error.exception.code,2)

    def test_no_stored_target_open_and_changed_input_rejected(self):
        f=self.file('NTUSER',hive_fixture(paths()));real=Path.open;opened=[]
        def track(p,*a,**kw):opened.append(str(p));return real(p,*a,**kw)
        with patch.object(Path,'open',track):analyze(explorer_hives=[('typed_paths',f),('word_wheel_query',f)])
        self.assertEqual(set(opened),{str(f.resolve())})
        with patch('plaintrace.binary.bounded_hash',side_effect=['first','second']),self.assertRaises(AnalysisError):analyze(explorer_hives=[('typed_paths',f)])

    def test_seeded_payload_mutations_keep_raw_values(self):
        rng=random.Random(31)
        for _ in range(80):
            raw=bytes(rng.randrange(256) for _ in range(rng.randrange(80)));_,e,_=self.parse({W:[value('0',3,raw),order(0)]},'word_wheel_query');self.assertEqual(e[0]['value_data_hex'],raw.hex());self.assertEqual(e[0]['mru_rank'],0)

if __name__=='__main__':unittest.main()
