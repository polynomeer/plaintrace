"""Generated NTUSER RecentDocs records and independent MRU oracles."""
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
from plaintrace import recent_docs
from plaintrace.registry_hive import Hive
from plaintrace.model import Report
from plaintrace.execution import analyze
from plaintrace.exports import write_report
from plaintrace.cli import main
from plaintrace.evidence import AnalysisError
from test_usb_registry_cli import hive_fixture,value,text,system_paths,FT,UTC

BASE=recent_docs.KEY_PATH

def entry(name,document,tail=b''):return value(name,3,(document+'\0').encode('utf-16-le')+tail)
def mru(*names):return value('MRUListEx',3,b''.join(struct.pack('<I',name) for name in names)+b'\xff'*4)
def paths():return {BASE:[entry('0','older.txt'),entry('7','最新😀.txt'),mru(7,0)],BASE+'\\.txt':[entry('0','older.txt'),mru(0)]}


class RecentDocsTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def file(self,name,data):path=self.folder/name;path.write_bytes(data);return path
    def parse(self,source=None,**kwargs):
        report=Report();keys,docs=recent_docs.analyze_hive(hive_fixture(paths() if source is None else source,**kwargs),1,report);return keys,docs,report

    def test_modern_sparse_order_unicode_and_key_time(self):
        keys,docs,report=self.parse();self.assertEqual(keys[0]['mru_order'],['7','0'])
        self.assertEqual([d['document_name'] for d in docs],['最新😀.txt','older.txt','older.txt'])
        self.assertEqual([d['mru_rank'] for d in docs],[0,1,0]);self.assertEqual(keys[0]['key_last_written'],UTC)
        self.assertEqual(keys[0]['key_last_write_raw'],str(FT));self.assertFalse(report.diagnostics)
        self.assertNotIn('opened_at',docs[0]);self.assertNotIn('timestamp',docs[0])

    def test_scopes_folder_and_duplicates_are_not_deduplicated(self):
        source=paths();source[BASE+'\\Folder']=[entry('3','Folder'),mru(3)]
        keys,docs,_=self.parse(source);self.assertEqual(len(keys),3);self.assertEqual(len(docs),4)
        self.assertEqual(len([d for d in docs if d['document_name']=='older.txt']),2)
        self.assertEqual({k['category'] for k in keys},{None,'.txt','Folder'})

    def test_legacy_mrulist_letters_and_regsz(self):
        keys,docs,report=self.parse({BASE:[text('MRUList','ba'),entry('a','A.doc'),text('b','B.doc')]})
        self.assertEqual(keys[0]['mru_format'],'MRUList');self.assertEqual(keys[0]['mru_order'],['b','a'])
        self.assertEqual([d['document_name'] for d in docs],['B.doc','A.doc']);self.assertFalse(report.diagnostics)

    def test_both_controls_are_ambiguous_no_ranks(self):
        keys,docs,report=self.parse({BASE:[mru(1),text('MRUList','a'),entry('1','one'),entry('a','alpha')]})
        self.assertEqual(keys[0]['mru_status'],'ambiguous');self.assertEqual(len(keys[0]['mru_values']),2)
        self.assertTrue(all(d['mru_rank'] is None for d in docs));self.assertIn('recent_docs_ambiguous_mru',{d['code'] for d in report.diagnostics})

    def test_missing_control_and_empty_key_preserved(self):
        keys,docs,report=self.parse({BASE:[entry('0','A')],BASE+'\\.empty':[]})
        self.assertEqual(len(keys),2);self.assertEqual(len(docs),1);self.assertIsNone(docs[0]['mru_rank'])
        self.assertEqual(keys[1]['mru_status'],'missing');self.assertIn('recent_docs_missing_mru',{d['code'] for d in report.diagnostics})

    def test_valid_empty_control_is_not_missing(self):
        keys,docs,report=self.parse({BASE:[mru()]});self.assertEqual(keys[0]['mru_status'],'valid')
        self.assertFalse(docs);self.assertFalse(report.diagnostics)

    def test_invalid_modern_sentinel_length_type_and_duplicates(self):
        for control in [value('MRUListEx',3,b''),value('MRUListEx',3,b'\0'*3),value('MRUListEx',3,b'\0'*4),value('MRUListEx',3,b'\xff'*4+b'\0'*4),mru(0,0),text('MRUListEx','bad')]:
            keys,docs,report=self.parse({BASE:[control,entry('0','A')]})
            self.assertEqual(keys[0]['mru_status'],'invalid');self.assertIsNone(docs[0]['mru_rank'])
            self.assertEqual(keys[0]['mru_values'][0]['data_hex'],control[2].hex());self.assertTrue(report.diagnostics)

    def test_invalid_legacy_mru_keeps_raw(self):
        for control in [text('MRUList','aa'),text('MRUList','A1'),text('MRUList','K'),value('MRUList',1,b'a\0'),value('MRUList',1,b'\0\xd8'),value('MRUList',3,b'a\0\0\0')]:
            keys,docs,report=self.parse({BASE:[control,entry('a','A')]})
            self.assertEqual(keys[0]['mru_status'],'invalid');self.assertIsNone(docs[0]['mru_rank']);self.assertTrue(report.diagnostics)

    def test_missing_and_unlisted_entries_keep_rank_gaps(self):
        keys,docs,report=self.parse({BASE:[mru(9,7),entry('7','known'),entry('2','unlisted')]})
        self.assertEqual(keys[0]['mru_order'],['9','7']);self.assertEqual([d['mru_rank'] for d in docs],[1,None])
        self.assertEqual({d['code'] for d in report.diagnostics},{'recent_docs_missing_entry','recent_docs_unlisted_entry'})

    def test_noncanonical_numeric_and_unknown_values_are_key_metadata(self):
        keys,docs,report=self.parse({BASE:[mru(),entry('01','not canonical'),entry('4294967295','sentinel'),text('Metadata','unknown'),value('',3,b'raw')]})
        self.assertFalse(docs);self.assertEqual(len(keys[0]['other_values']),4);self.assertTrue(report.diagnostics)

    def test_opaque_shell_tail_and_literal_names_are_preserved(self):
        name="C:\\literal\\%TEMP%\\a,b'\n😀";tail=b'\xff\x00\x10'
        keys,docs,report=self.parse({BASE:[entry('0',name,tail),mru(0)]})
        self.assertEqual(docs[0]['document_name'],name);self.assertEqual(docs[0]['name_utf16_hex'],name.encode('utf-16-le').hex())
        self.assertEqual(docs[0]['trailing_data_hex'],tail.hex());self.assertIn('recent_docs_opaque_tail',{d['code'] for d in report.diagnostics})

    def test_missing_terminator_wrong_type_and_empty_name_retained(self):
        keys,docs,report=self.parse({BASE:[mru(0,1,2),value('0',3,b'A\0'),text('1','wrong type'),entry('2','')]})
        self.assertIsNone(docs[0]['document_name']);self.assertIsNone(docs[1]['document_name']);self.assertEqual(docs[2]['document_name'],'')
        self.assertTrue(all(d['value_data_hex'] for d in docs));self.assertEqual(len(report.diagnostics),3)

    def test_unpaired_surrogate_and_aligned_nul(self):
        keys,docs,report=self.parse({BASE:[mru(0,1),value('0',3,b'\0\xd8\0\0'),entry('1','ĀA')]})
        self.assertEqual(docs[0]['document_name'],'\\x00\\xd8');self.assertEqual(docs[1]['document_name'],'ĀA')
        self.assertIn('recent_docs_invalid_name',{d['code'] for d in report.diagnostics})

    def test_nested_scopes_are_diagnosed_not_traversed(self):
        keys,docs,report=self.parse({BASE:[mru()],BASE+'\\.txt':[mru()],BASE+'\\.txt\\nested':[entry('0','hidden'),mru(0)]})
        self.assertEqual(len(keys),2);self.assertFalse(docs);self.assertEqual(report.diagnostics[0]['code'],'recent_docs_nested_keys')

    def test_missing_branch_and_wrong_hive_do_not_invent_documents(self):
        for source in [{},{'Unrelated':[text('Value','A')]}]:
            keys,docs,report=self.parse(source);self.assertFalse(keys);self.assertFalse(docs)
            self.assertEqual(report.diagnostics[0]['code'],'recent_docs_absent')

    def test_regf_versions_indexes_and_case_insensitive_path(self):
        for index in (b'li',b'lf',b'lh',b'ri'):
            for minor in (3,4,5):
                keys,docs,_=self.parse({BASE.lower():[entry('0','A'),value('mrulistex',3,b'\0'*4+b'\xff'*4)]},index_kind=index,minor=minor)
                self.assertEqual(docs[0]['mru_rank'],0);self.assertEqual(keys[0]['mru_format'],'MRUListEx')

    def test_key_document_and_output_budgets(self):
        for name,limit in [('MAX_KEYS',1),('MAX_DOCUMENTS',1),('MAX_OUTPUT_BYTES',1)]:
            with patch.object(recent_docs,name,limit),self.assertRaises(AnalysisError):self.parse()
        source=paths();source[BASE].append(value('Big',3,b'x'*16345))
        with self.assertRaises(AnalysisError):self.parse(source)

    def test_dirty_corrupt_truncated_hives_fail(self):
        good=hive_fixture(paths())
        for data in [b'',good[:-1],b'bad!'+good[4:]]:
            with self.assertRaises(AnalysisError):recent_docs.analyze_hive(data,1,Report())
        bad=bytearray(good);bad[8]=2
        with self.assertRaises(AnalysisError):recent_docs.analyze_hive(bad,1,Report())

    def test_repeated_renamed_sources_hashes_and_offsets(self):
        path=self.file('renamed.bin',hive_fixture(paths()));before=path.read_bytes();report=analyze(recent_hives=[path,path])
        self.assertEqual([s['source_kind'] for s in report.sources],['recent_docs','recent_docs'])
        self.assertEqual(report.sources[0]['sha256'],hashlib.sha256(before).hexdigest());self.assertEqual(path.read_bytes(),before)
        self.assertEqual([d['source_id'] for d in report.recent_docs],[1,1,1,2,2,2])
        hive=Hive(before);self.assertEqual(report.recent_doc_keys[0]['record_id'],str(hive.open(BASE)['offset']+4096))
        self.assertTrue(all(d['key_id'] in {k['record_id'] for k in report.recent_doc_keys} for d in report.recent_docs))

    def test_json_sqlite_current_schema_and_raw_metadata_roundtrip(self):
        path=self.file('NTUSER.DAT',hive_fixture(paths()));report=analyze(recent_hives=[path])
        js=self.folder/'out.json';sq=self.folder/'out.sqlite';write_report(report,js);write_report(report,sq,'sqlite')
        payload=json.loads(js.read_text());self.assertEqual(payload['format_version'],13)
        self.assertEqual(payload['counts']['recent_doc_keys'],2);self.assertEqual(payload['counts']['recent_docs'],3)
        with closing(sqlite3.connect(sq)) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],13);self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
            self.assertEqual(json.loads(db.execute('SELECT mru_order FROM recent_doc_keys LIMIT 1').fetchone()[0]),['7','0'])
            self.assertEqual(db.execute('SELECT document_name,mru_rank FROM recent_docs LIMIT 1').fetchone(),('最新😀.txt',0))

    def test_cli_real_subprocess_strict_and_sqlite(self):
        path=self.file('NTUSER.DAT',hive_fixture(paths()));args=[sys.executable,'-m','plaintrace','--recent-docs',str(path)]
        result=subprocess.run(args,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(len(json.loads(result.stdout)['recent_docs']),3)
        output=self.folder/'cli.sqlite';result=subprocess.run(args+['--format','sqlite','--output',str(output)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        missing=self.file('EMPTY',hive_fixture());out=io.StringIO()
        with redirect_stdout(out),redirect_stderr(io.StringIO()):code=main(['--recent-docs',str(missing),'--strict'])
        self.assertEqual(code,1);self.assertFalse(json.loads(out.getvalue())['recent_docs'])

    def test_later_failure_atomic_and_outputs_protected(self):
        path=self.file('NTUSER.DAT',hive_fixture(paths()));bad=self.file('BAD',b'corrupt');output=self.folder/'out.json'
        with redirect_stderr(io.StringIO()):code=main(['--recent-docs',str(path),'--recent-docs',str(bad),'--output',str(output)])
        self.assertEqual(code,2);self.assertFalse(output.exists());report=analyze(recent_hives=[path]);before=path.read_bytes()
        with self.assertRaises(AnalysisError):write_report(report,path)
        existing=self.file('existing',b'other')
        with self.assertRaises(AnalysisError):write_report(report,existing)
        self.assertEqual(path.read_bytes(),before);self.assertEqual(existing.read_bytes(),b'other')

    def test_only_acquired_hive_opened_and_changing_input_rejected(self):
        path=self.file('NTUSER.DAT',hive_fixture(paths()));self.file('NTUSER.DAT.LOG1',b'not opened')
        opened=[];original=Path.open
        def track(current,*args,**kwargs):opened.append(current);return original(current,*args,**kwargs)
        with patch.object(Path,'open',track):analyze(recent_hives=[path])
        self.assertEqual(set(opened),{path.resolve()})
        with patch('plaintrace.binary.bounded_hash',side_effect=['before','after']),self.assertRaises(AnalysisError):analyze(recent_hives=[path])

    def test_mixed_browser_usb_recycle_and_recent_lineage(self):
        from test_browser_cli import chromium
        from test_recycle_bin_cli import index_fixture
        browser=self.folder/'History'
        with closing(sqlite3.connect(browser)) as db:chromium(db)
        system=self.file('SYSTEM',hive_fixture(system_paths()));recycle=self.file('$IABC',index_fixture());recent=self.file('NTUSER',hive_fixture(paths()))
        report=analyze([browser],recycle_bins=[recycle],usb_hives=[('system',system)],recent_hives=[recent])
        self.assertEqual([s['source_kind'] for s in report.sources],['browser','recycle_bin','usb_registry','recent_docs'])
        self.assertEqual(report.recent_docs[0]['source_id'],4)

    def test_review_mru_mutations_do_not_escape_contract(self):
        rng=random.Random(2017)
        for _ in range(100):
            raw=bytearray(mru(7,0)[2]);raw[rng.randrange(len(raw))]^=rng.randrange(1,256)
            keys,docs,_=self.parse({BASE:[value('MRUListEx',3,raw),entry('0','A'),entry('7','B')]})
            self.assertEqual(len(docs),2);self.assertIn(keys[0]['mru_status'],('valid','invalid'))

    def test_review_large_unsigned_slot_and_case_insensitive_legacy(self):
        keys,docs,report=self.parse({BASE:[mru(0xfffffffe),entry('4294967294','large')]})
        self.assertEqual(docs[0]['mru_rank'],0);self.assertFalse(report.diagnostics)
        keys,docs,report=self.parse({BASE:[text('MRUList','a'),entry('A','legacy')]})
        self.assertEqual(docs[0]['mru_rank'],0);self.assertFalse(report.diagnostics)

    def test_review_sqlite_key_lineage_foreign_key_rejects_orphan(self):
        path=self.file('NTUSER',hive_fixture(paths()));report=analyze(recent_hives=[path]);report.recent_docs[0]['key_id']='nonexistent'
        output=self.folder/'orphan.sqlite'
        with self.assertRaises(sqlite3.IntegrityError):write_report(report,output,'sqlite')
        self.assertFalse(output.exists());self.assertFalse(list(self.folder.glob('.plaintrace-*')))
