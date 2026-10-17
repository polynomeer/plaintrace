"""Independent temporary REGF and UTF-16 oracles for literal Run dialog observations."""
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
from plaintrace import run_mru as rm
from plaintrace.registry_hive import Hive
from plaintrace.model import Report
from plaintrace.execution import analyze
from plaintrace.exports import write_report
from plaintrace.cli import main
from plaintrace.evidence import AnalysisError
from test_usb_registry_cli import hive_fixture,value,text,checksum,FT,UTC
BASE=rm.KEY_PATH

def paths():return {BASE:[text('a',r'cmd /c echo 한글😀\1'),text('c','  "C:\\Program Files\\x.exe" /x\n\t\\1'),text('MRUList','ca')]}

class RunMRUTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def file(self,name,data):p=self.folder/name;p.write_bytes(data);return p
    def parse(self,p=None,**kw):
        r=Report();keys,entries=rm.analyze_hive(hive_fixture(paths() if p is None else p,**kw),1,r);return keys,entries,r
    def codes(self,r):return {d['code'] for d in r.diagnostics}

    def test_unicode_literal_commands_and_order(self):
        k,e,r=self.parse();self.assertEqual(k[0]['mru_order'],['c','a']);self.assertEqual([x['mru_rank'] for x in e],[1,0]);self.assertEqual(e[0]['stored_command'],r'cmd /c echo 한글😀\1');self.assertFalse(r.diagnostics)

    def test_no_suffix_whitespace_argument_or_environment_normalization(self):
        commands=[r'cmd\1','cmd\x01','  cmd /x  ',r'%USERPROFILE%\x.exe',r'\\server\share\file','https://example.invalid/?q=a%20b','cmd']
        _,e,_=self.parse({BASE:[text(chr(97+i),s) for i,s in enumerate(commands)]+[text('MRUList','abcdefg')]})
        self.assertEqual([x['stored_command'] for x in e],commands);self.assertTrue(all('executed_at' not in x and 'executable' not in x for x in e))

    def test_duplicates_retained_across_slots(self):
        _,e,_=self.parse({BASE:[text('a','same'),text('b','same'),text('MRUList','ba')]});self.assertEqual([x['stored_command'] for x in e],['same','same']);self.assertEqual([x['mru_rank'] for x in e],[1,0])

    def test_missing_references_keep_rank_gaps(self):
        k,e,r=self.parse({BASE:[text('a','a'),text('c','c'),text('MRUList','zcbda')]});self.assertEqual([x['mru_rank'] for x in e],[4,1]);self.assertEqual(k[0]['mru_order'],list('zcbda'));self.assertIn('run_mru_missing_entry',self.codes(r))

    def test_unlisted_entry_has_null_rank(self):
        _,e,r=self.parse({BASE:[text('a','a'),text('b','b'),text('MRUList','a')]});self.assertIsNone(e[1]['mru_rank']);self.assertIn('run_mru_unlisted_entry',self.codes(r))

    def test_missing_control_does_not_guess_alphabetical_rank(self):
        k,e,r=self.parse({BASE:[text('c','c'),text('a','a')]});self.assertEqual(k[0]['mru_status'],'missing');self.assertTrue(all(x['mru_rank'] is None for x in e));self.assertIn('run_mru_missing_mru',self.codes(r))

    def test_invalid_controls_never_assign_rank(self):
        for v in (value('MRUList',3,b'a\0\0\0'),value('MRUList',1,b'a\0'),text('MRUList','aa'),text('MRUList','aA'),text('MRUList','a1'),text('MRUList','é'),value('MRUList',1,b'a\0\0\0\0\0'),value('MRUList',1,b'\x00\xd8\0\0'),value('MRUList',1,b'\0')):
            k,e,r=self.parse({BASE:[text('a','app'),v]});self.assertEqual(k[0]['mru_status'],'invalid');self.assertIsNone(e[0]['mru_rank']);self.assertIn('run_mru_invalid_mru',self.codes(r))

    def test_mrulistex_and_ambiguous_controls_not_selected(self):
        for controls,status in (([value('MRUListEx',3,b'\xff'*4)],'unsupported'),([text('MRUList','a'),value('MRUListEx',3,b'\xff'*4)],'ambiguous')):
            k,e,_=self.parse({BASE:[text('a','app')]+controls});self.assertEqual(k[0]['mru_status'],status);self.assertIsNone(e[0]['mru_rank']);self.assertEqual(len(k[0]['control_values']),len(controls))

    def test_valid_empty_order_distinct_from_missing(self):
        k,e,r=self.parse({BASE:[text('MRUList','')]});self.assertEqual(k[0]['mru_status'],'valid');self.assertFalse(e or r.diagnostics)

    def test_ascii_single_letter_names_and_unknown_metadata(self):
        k,e,r=self.parse({BASE:[text('a','app'),text('ab','meta'),text('1','number'),text('é','unicode'),text('','default'),text('MRUList','a')]});self.assertEqual(len(e),1);self.assertEqual([x['name'] for x in k[0]['other_values']],['ab','1','é','']);self.assertIn('run_mru_unknown_value',self.codes(r))

    def test_case_insensitive_control_path_and_slots(self):
        k,e,_=self.parse({BASE.lower():[text('A','App'),text('mRuLiSt','a')]});self.assertEqual(e[0]['value_name'],'A');self.assertEqual(e[0]['mru_rank'],0);self.assertEqual(k[0]['mru_status'],'valid')

    def test_wrong_value_types_kept_raw_without_string_decoding(self):
        for kind in (2,3,7):
            _,e,r=self.parse({BASE:[value('a',kind,b'a\0\0\0'),text('MRUList','a')]});self.assertEqual(e[0]['status'],'wrong_type');self.assertIsNone(e[0]['stored_command']);self.assertEqual(e[0]['value_data_hex'],'61000000');self.assertIn('run_mru_wrong_type',self.codes(r))

    def test_unterminated_and_odd_strings_retained(self):
        for raw in (b'',b'a\0',b'a\0x',b'\0'):
            _,e,r=self.parse({BASE:[value('a',1,raw),text('MRUList','a')]});self.assertEqual(e[0]['status'],'unterminated');self.assertIsNone(e[0]['stored_command']);self.assertIn('run_mru_unterminated',self.codes(r))

    def test_invalid_utf16_escaped_and_bytes_preserved(self):
        _,e,r=self.parse({BASE:[value('a',1,b'\0\xd8\0\0'),text('MRUList','a')]});self.assertEqual(e[0]['status'],'invalid_text');self.assertEqual(e[0]['stored_command'],r'\x00\xd8');self.assertEqual(e[0]['command_utf16_hex'],'00d8');self.assertIn('run_mru_invalid_text',self.codes(r))

    def test_first_aligned_terminator_and_trailing_bytes(self):
        raw='Ācmd\0'.encode('utf-16-le')+b'\0\0x';_,e,r=self.parse({BASE:[value('a',1,raw),text('MRUList','a')]});self.assertEqual(e[0]['stored_command'],'Ācmd');self.assertEqual(e[0]['trailing_data_hex'],'000078');self.assertEqual(e[0]['status'],'trailing');self.assertIn('run_mru_trailing_data',self.codes(r))

    def test_empty_command_kept_with_warning(self):
        _,e,r=self.parse({BASE:[text('a',''),text('MRUList','a')]});self.assertEqual(e[0]['stored_command'],'');self.assertEqual(e[0]['status'],'empty');self.assertIn('run_mru_empty_command',self.codes(r))

    def test_key_time_and_physical_offsets_not_per_command_times(self):
        p=paths();data=hive_fixture(p);h=Hive(data);k,e,_=self.parse(p);self.assertEqual(k[0]['key_last_written'],UTC);self.assertEqual(k[0]['key_last_write_raw'],str(FT));self.assertEqual(int(k[0]['record_id']),h.open(BASE)['offset']+4096)
        for row in e:
            offset=int(row['record_id']);self.assertEqual(data[offset+4:offset+6],b'vk');self.assertEqual(row['key_id'],k[0]['record_id']);self.assertNotIn('key_last_written',row)
            v=next(x for x in h.values(h.open(BASE)) if x['name']==row['value_name']);self.assertEqual(v['raw'].hex(),row['value_data_hex'])

    def test_absent_empty_and_nested_scopes(self):
        k,e,r=self.parse({});self.assertFalse(k or e);self.assertIn('run_mru_absent',self.codes(r))
        k,e,r=self.parse({BASE:[]});self.assertEqual(len(k),1);self.assertFalse(e);self.assertEqual(k[0]['mru_status'],'missing')
        k,e,r=self.parse({BASE+'\\sub':[text('a','ignored')]});self.assertFalse(e);self.assertIn('run_mru_nested_keys',self.codes(r))

    def test_all_regf_versions_and_index_kinds(self):
        for index in (b'li',b'lf',b'lh',b'ri'):
            for minor in (3,4,5):self.assertEqual(len(self.parse(index_kind=index,minor=minor)[1]),2)

    def test_dirty_corrupt_and_duplicate_aliases_rejected(self):
        data=bytearray(hive_fixture(paths()));struct.pack_into('<I',data,4,2)
        for raw in (b'bad',b'regf',checksum(data)):
            with self.assertRaises(AnalysisError):rm.analyze_hive(raw,1,Report())
        with self.assertRaises(AnalysisError):self.parse({BASE:[text('a','one'),text('A','two')]})

    def test_entry_string_and_output_limits(self):
        for constant in ('MAX_ENTRIES','MAX_STRING_UNITS','MAX_OUTPUT_BYTES'):
            with patch.object(rm,constant,1),self.assertRaises(AnalysisError):self.parse()
        with patch.object(rm,'MAX_STRING_UNITS',2):
            self.assertEqual(self.parse({BASE:[text('a','😀'),text('MRUList','a')]})[1][0]['stored_command'],'😀')
            with self.assertRaises(AnalysisError):self.parse({BASE:[text('a','😀a')]})

    def test_json_sqlite_schema_raw_data_and_foreign_keys(self):
        f=self.file('NTUSER',hive_fixture(paths()));r=analyze(run_mru_hives=[f]);j=self.folder/'out.json';s=self.folder/'out.sqlite';write_report(r,j);write_report(r,s,'sqlite')
        payload=json.loads(j.read_text());self.assertEqual(payload['format_version'],13);self.assertEqual(payload['run_mru_entries'],r.run_mru_entries)
        with closing(sqlite3.connect(s)) as db:
            self.assertEqual(db.execute('pragma user_version').fetchone()[0],13);self.assertEqual(db.execute('pragma foreign_key_check').fetchall(),[]);self.assertEqual(db.execute('select stored_command from run_mru_entries order by rowid').fetchone()[0],r.run_mru_entries[0]['stored_command'])
            self.assertEqual(json.loads(db.execute('select control_values from run_mru_keys').fetchone()[0])[0]['data_hex'],'ca\0'.encode('utf-16-le').hex());db.execute('pragma foreign_keys=on')
            with self.assertRaises(sqlite3.IntegrityError):db.execute("update run_mru_entries set key_id='missing'")

    def test_repeated_sources_hashes_and_input_unchanged(self):
        data=hive_fixture(paths());f=self.file('renamed.bin',data);r=analyze(run_mru_hives=[f,f]);self.assertEqual(len(r.run_mru_entries),4);self.assertEqual([s['source_id'] for s in r.sources],[1,2]);self.assertTrue(all(s['sha256']==hashlib.sha256(data).hexdigest() and s['source_kind']=='run_mru' for s in r.sources));self.assertEqual(f.read_bytes(),data)

    def test_cli_subprocess_json_strict_and_sqlite(self):
        p=paths();p[BASE].append(text('b','unlisted'));f=self.file('NTUSER',hive_fixture(p));out=self.folder/'out.sqlite'
        for extra in ([],['--strict'],['--format','sqlite','--output',str(out)]):
            r=subprocess.run([sys.executable,'-m','plaintrace','--run-mru',str(f),*extra],capture_output=True,text=True);self.assertEqual(r.returncode,1 if '--strict' in extra else 0,r.stderr)
            if '--format' not in extra:self.assertEqual(len(json.loads(r.stdout)['run_mru_entries']),3)
        self.assertTrue(out.is_file())

    def test_mixed_adapters_preserve_source_groups(self):
        f=self.file('NTUSER',hive_fixture(paths()));r=analyze(userassist_hives=[f],run_mru_hives=[f]);self.assertEqual([s['source_kind'] for s in r.sources],['userassist','run_mru']);self.assertTrue(all(x['source_id']==2 for x in r.run_mru_entries))

    def test_later_failure_publishes_no_partial_report(self):
        f=self.file('good',hive_fixture(paths()));b=self.file('bad',b'bad');out=self.folder/'out.json'
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):code=main(['--run-mru',str(f),'--run-mru',str(b),'--output',str(out)])
        self.assertEqual(code,2);self.assertFalse(out.exists());self.assertFalse(list(self.folder.glob('.plaintrace-*')))

    def test_input_existing_output_and_sidecar_protection(self):
        data=hive_fixture(paths());f=self.file('NTUSER',data);existing=self.file('out',b'keep')
        for out in (f,existing,self.folder/'NTUSER-wal'):
            with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):self.assertEqual(main(['--run-mru',str(f),'--output',str(out)]),2)
        self.assertEqual(f.read_bytes(),data);self.assertEqual(existing.read_bytes(),b'keep')

    def test_missing_input_and_sqlite_destination(self):
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            self.assertEqual(main(['--run-mru',str(self.folder/'missing')]),2)
            with self.assertRaises(SystemExit) as error:main(['--run-mru','missing','--format','sqlite'])
        self.assertEqual(error.exception.code,2)

    def test_no_target_open_and_changed_input_rejected(self):
        f=self.file('NTUSER',hive_fixture(paths()));real=Path.open;opened=[]
        def track(p,*a,**kw):opened.append(str(p));return real(p,*a,**kw)
        with patch.object(Path,'open',track):analyze(run_mru_hives=[f])
        self.assertEqual(set(opened),{str(f.resolve())})
        with patch('plaintrace.binary.bounded_hash',side_effect=['first','second']),self.assertRaises(AnalysisError):analyze(run_mru_hives=[f])

    def test_seeded_string_mutations_preserve_full_raw_values(self):
        rng=random.Random(19)
        for _ in range(80):
            raw=bytes(rng.randrange(256) for _ in range(rng.randrange(80)));_,e,_=self.parse({BASE:[value('a',1,raw),text('MRUList','a')]});self.assertEqual(e[0]['value_data_hex'],raw.hex());self.assertEqual(e[0]['mru_rank'],0)

if __name__=='__main__':unittest.main()
