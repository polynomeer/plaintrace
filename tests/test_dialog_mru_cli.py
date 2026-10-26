"""Generated Common Dialog PIDLs, prefix bounds and source/SQLite lineage."""
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
from plaintrace import dialog_mru,shell_items
from plaintrace.cli import main
from plaintrace.evidence import AnalysisError
from plaintrace.execution import analyze
from plaintrace.exports import write_report
from plaintrace.model import Report
from dialog_fixtures import BASE,OPEN,LAST,paths,mru,pidl,opened,visited,root_item,volume,network,file_item
from test_usb_registry_cli import hive_fixture,value,text,FT,UTC

class DialogMRUTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def file(self,name,data):p=self.folder/name;p.write_bytes(data);return p
    def parse(self,source=None,codepage='cp1252',**kw):
        report=Report();keys,rows=dialog_mru.analyze_hive(hive_fixture(paths() if source is None else source,**kw),1,report,codepage);return keys,rows,report

    def test_both_lists_categories_application_and_folder_references(self):
        keys,rows,report=self.parse();self.assertFalse(report.diagnostics);self.assertEqual(len(keys),4);self.assertEqual(len(rows),5)
        self.assertEqual(rows[0]['path_candidate'],'C:\\문서😀.doc');self.assertEqual(rows[0]['category'],'*');self.assertIsNone(rows[0]['application_name'])
        self.assertEqual(rows[3]['application_name'],'editor.exe');self.assertEqual(rows[3]['path_candidate'],'C:\\Documents');self.assertEqual(rows[4]['path_candidate'],'\\\\server\\share\\Folder')
        self.assertEqual(rows[4]['application_name'],'뷰어😀.exe');self.assertTrue(rows[4]['application_name_valid'])

    def test_open_save_root_is_container_without_fabricated_order(self):
        keys,rows,report=self.parse({OPEN:[],OPEN+'\\txt':[mru()],LAST:[mru()]})
        self.assertEqual(keys[0]['mru_status'],'container');self.assertFalse(keys[0]['control_values']);self.assertFalse(rows);self.assertFalse(report.diagnostics)
        self.assertEqual(keys[1]['parent_key_id'],keys[0]['record_id']);self.assertIsNone(keys[-1]['parent_key_id'])

    def test_open_save_root_numeric_values_are_preserved(self):
        _,rows,_=self.parse({OPEN:[opened(1,volume()),mru(1)],LAST:[mru()]})
        self.assertEqual(len(rows),1);self.assertIsNone(rows[0]['category']);self.assertEqual(rows[0]['path_candidate'],'C:\\')

    def test_last_visited_utf16_prefix_and_pidl_offsets_are_exact(self):
        keys,rows,_=self.parse();row=rows[-1];expected='뷰어😀.exe'.encode('utf-16-le')
        self.assertEqual(row['application_utf16_hex'],expected.hex());self.assertEqual(row['pidl_offset'],len(expected)+2)
        raw=bytes.fromhex(row['value_data_hex']);self.assertEqual(raw[row['pidl_offset']:].hex(),row['pidl_hex']);self.assertEqual(row['items'][0]['offset'],0)
        self.assertTrue(all(int(k['record_id'])>=4096 for k in keys));self.assertTrue(all(int(r['record_id'])>=4096 for r in rows))

    def test_application_literal_not_normalized_or_verified_executable(self):
        application='%TEMP%\\not,a\nprogram';_,rows,_=self.parse({LAST:[visited(0,application,volume()),mru(0)]})
        self.assertEqual(rows[0]['application_name'],application);self.assertTrue(rows[0]['application_name_valid']);self.assertNotIn('executed_at',rows[0])

    def test_invalid_application_unicode_does_not_hide_independent_pidl(self):
        raw=b'\0\xd8\0\0'+pidl(volume());_,rows,report=self.parse({LAST:[value('0',3,raw),mru(0)]})
        self.assertFalse(rows[0]['application_name_valid']);self.assertEqual(rows[0]['application_utf16_hex'],'00d8');self.assertEqual(rows[0]['path_candidate'],'C:\\')
        self.assertIn('dialog_mru_invalid_application',{d['code'] for d in report.diagnostics})

    def test_empty_application_label_is_not_attributed(self):
        _,rows,report=self.parse({LAST:[visited(0,'',volume()),mru(0)]});self.assertEqual(rows[0]['application_name'],'');self.assertFalse(rows[0]['application_name_valid'])
        self.assertEqual(rows[0]['path_candidate'],'C:\\');self.assertIn('dialog_mru_empty_application',{d['code'] for d in report.diagnostics})

    def test_unterminated_application_never_searches_for_pidl_signature(self):
        raw='application'.encode('utf-16-le')+b'\xff';_,rows,report=self.parse({LAST:[value('0',3,raw),mru(0)]})
        self.assertEqual(rows[0]['pidl_status'],'invalid_prefix');self.assertIsNone(rows[0]['pidl_offset']);self.assertIsNone(rows[0]['pidl_hex']);self.assertEqual(rows[0]['value_data_hex'],raw.hex())
        self.assertIn('dialog_mru_unterminated_application',{d['code'] for d in report.diagnostics})

    def test_unterminated_pidl_keeps_components_but_no_path(self):
        _,rows,report=self.parse({OPEN+'\\txt':[value('0',3,pidl(volume(),terminal=False)),mru(0)]})
        self.assertEqual(rows[0]['pidl_status'],'unterminated');self.assertTrue(rows[0]['items']);self.assertIsNone(rows[0]['path_candidate']);self.assertFalse(rows[0]['ancestry_complete'])
        self.assertIn('dialog_mru_unterminated_pidl',{d['code'] for d in report.diagnostics})

    def test_trailing_pidl_and_empty_lists_retained(self):
        for raw,status in ((pidl(volume())+b'opaque','trailing'),(bytes(2),'empty'),(b'','unterminated')):
            _,rows,_=self.parse({OPEN+'\\*':[value('0',3,raw),mru(0)]});self.assertEqual(rows[0]['pidl_status'],status);self.assertEqual(rows[0]['value_data_hex'],raw.hex());self.assertIsNone(rows[0]['path_candidate'])

    def test_wrong_value_types_do_not_decode_application_or_pidl(self):
        for path in (OPEN+'\\txt',LAST):
            _,rows,_=self.parse({path:[text('0','not binary'),mru(0)]});self.assertEqual(rows[0]['pidl_status'],'wrong_type');self.assertIsNone(rows[0]['application_name']);self.assertIsNone(rows[0]['pidl_offset'])

    def test_malformed_pidl_lengths_strings_and_extensions_keep_raw(self):
        for raw in (b'\x01\0x',b'\xff\xffx',struct.pack('<HB',3,0x1f),b'x'):
            _,rows,_=self.parse({OPEN+'\\*':[value('0',3,raw),mru(0)]});self.assertEqual(rows[0]['pidl_status'],'malformed');self.assertEqual(rows[0]['value_data_hex'],raw.hex())
        bad=bytearray(file_item(long_name='Long'));bad[-2:]=b'\xff\xff'
        _,rows,_=self.parse({LAST:[value('0',3,b'A\0\0\0'+pidl(bytes(bad))),mru(0)]});self.assertEqual(rows[0]['pidl_status'],'malformed');self.assertEqual(rows[0]['application_name'],'A')

    def test_unknown_item_classes_do_not_create_guessed_paths(self):
        _,rows,report=self.parse({OPEN+'\\*':[opened(0,struct.pack('<HB',3,0x61),file_item()),mru(0)]})
        self.assertEqual(rows[0]['pidl_status'],'parsed');self.assertIsNone(rows[0]['path_candidate']);self.assertIn('dialog_mru_unsupported_item',{d['code'] for d in report.diagnostics})

    def test_explicit_absolute_anchor_and_namespace_or_relative_bases(self):
        samples=((pidl(root_item(),file_item('Folder')),'shell_namespace_hierarchy'),(pidl(file_item('Relative')),'relative_hierarchy'),(pidl(struct.pack('<HB',3,0x61),volume()),'stored_volume_hierarchy'))
        for raw,basis in samples:
            _,rows,_=self.parse({OPEN+'\\*':[value('0',3,raw),mru(0)]});self.assertEqual(rows[0]['path_basis'],basis)

    def test_dot_device_and_separator_components_are_not_resolved(self):
        for item in (file_item('..',wide=True),file_item('a\\b',wide=True),network('\\\\?\\Volume{opaque}')):
            _,rows,_=self.parse({OPEN+'\\*':[opened(0,item),mru(0)]});self.assertIsNone(rows[0]['path_candidate'])

    def test_mru_sparse_missing_and_unlisted_ranks_keep_gaps(self):
        keys,rows,report=self.parse({OPEN+'\\txt':[opened(1,volume()),opened(9,volume()),opened(2,volume()),mru(9,7,1)]})
        key=keys[-1];self.assertEqual(key['mru_order'],['9','7','1']);self.assertEqual([r['mru_rank'] for r in rows],[2,0,None])
        self.assertTrue({'dialog_mru_missing_entry','dialog_mru_unlisted_entry'}<={d['code'] for d in report.diagnostics})

    def test_invalid_mru_types_sentinels_duplicates_keep_no_ranks(self):
        for control in (mru(1,1),value('MRUListEx',3,b''),value('MRUListEx',3,bytes(4)),value('MRUListEx',3,b'\xff'*4+bytes(4)),text('MRUListEx','bad')):
            keys,rows,_=self.parse({LAST:[visited(1,'app',volume()),control]});self.assertEqual(keys[0]['mru_status'],'invalid');self.assertIsNone(rows[0]['mru_rank']);self.assertEqual(keys[0]['control_values'][0]['data_hex'],control[2].hex())

    def test_missing_legacy_and_ambiguous_controls_never_guess_order(self):
        for controls in ([],[text('MRUList','a')],[mru(0),text('MRUList','a')]):
            keys,rows,_=self.parse({LAST:[visited(0,'app',volume()),*controls]});self.assertNotEqual(keys[0]['mru_status'],'valid');self.assertIsNone(rows[0]['mru_rank']);self.assertEqual(len(keys[0]['control_values']),len(controls))

    def test_canonical_names_unknown_metadata_and_raw_offsets(self):
        keys,rows,report=self.parse({LAST:[visited(0,'app',volume()),text('01','unknown'),text('4294967295','sentinel'),text('Metadata','unknown'),mru(0)]})
        self.assertEqual(len(rows),1);self.assertEqual(len(keys[0]['other_values']),3);self.assertTrue(all(v['value_offset']>=4096 for v in keys[0]['other_values']))
        self.assertIn('dialog_mru_unknown_value',{d['code'] for d in report.diagnostics})

    def test_missing_branches_and_valid_empty_key_are_distinct(self):
        keys,rows,report=self.parse({'Unrelated':[]});self.assertFalse(keys or rows);self.assertEqual(len(report.diagnostics),2)
        keys,rows,report=self.parse({OPEN:[],LAST:[mru()]});self.assertEqual(len(keys),2);self.assertFalse(rows);self.assertFalse(report.diagnostics)

    def test_nested_scopes_diagnosed_not_silently_traversed(self):
        keys,rows,report=self.parse({OPEN+'\\txt\\nested':[opened(0,volume()),mru(0)],LAST+'\\nested':[visited(0,'app',volume()),mru(0)]})
        self.assertEqual(len(keys),3);self.assertFalse(rows);self.assertIn('dialog_mru_nested_keys',{d['code'] for d in report.diagnostics})

    def test_duplicate_paths_across_categories_and_apps_remain_independent(self):
        keys,rows,_=self.parse({OPEN+'\\*':[opened(0,volume()),mru(0)],OPEN+'\\txt':[opened(0,volume()),mru(0)],LAST:[visited(0,'one',volume()),visited(2,'two',volume()),mru(2,0)]})
        self.assertEqual(len(rows),4);self.assertEqual(len({r['record_id'] for r in rows}),4);self.assertTrue(all(r['path_candidate']=='C:\\' for r in rows))

    def test_key_filetimes_and_item_fat_times_are_not_entry_open_times(self):
        keys,rows,_=self.parse();self.assertTrue(all(k['key_last_written']==UTC and k['key_last_write_raw']==str(FT) for k in keys))
        item=rows[3]['items'][-1];self.assertEqual(item['metadata']['modified_fat']['time_basis'],'stored_fat_no_timezone');self.assertNotIn('opened_at',rows[3]);self.assertNotIn('key_last_written',rows[3])

    def test_ansi_codepage_and_unicode_application_are_separate(self):
        raw=('뷰어.exe\0').encode('utf-16-le')+pidl(volume(),file_item('경로',encoding='cp949'))
        _,rows,_=self.parse({LAST:[value('0',3,raw),mru(0)]},codepage='cp949');self.assertEqual(rows[0]['application_name'],'뷰어.exe');self.assertEqual(rows[0]['path_candidate'],'C:\\경로')

    def test_invalid_codepage_is_fatal(self):
        for name in ('missing-codepage','utf-16-le'):
            with self.assertRaises(AnalysisError):self.parse(codepage=name)

    def test_item_diagnostics_are_adapter_scoped_and_value_identified(self):
        _,rows,report=self.parse({OPEN+'\\*':[opened(0,struct.pack('<HB',3,0x61)),mru(0)]})
        codes={d['code'] for d in report.diagnostics};self.assertIn('dialog_mru_unsupported_item',codes);self.assertTrue(all(not c.startswith('shellbag_') for c in codes))
        self.assertEqual(next(d for d in report.diagnostics if d['code']=='dialog_mru_unsupported_item')['record_id'],rows[0]['record_id'])

    def test_key_entry_application_path_output_budgets_are_fatal(self):
        for name in ('MAX_KEYS','MAX_ENTRIES','MAX_APP_UNITS','MAX_PATH_CHARS','MAX_OUTPUT_BYTES'):
            with patch.object(dialog_mru,name,1),self.assertRaises(AnalysisError):self.parse()

    def test_shell_item_resource_limits_are_not_downgraded(self):
        with patch.object(shell_items,'MAX_ITEMS',1),self.assertRaises(AnalysisError):self.parse()
        with patch.object(shell_items,'MAX_EXTENSIONS',0),self.assertRaises(AnalysisError):self.parse()

    def test_regf_versions_indexes_case_and_dirty_inputs(self):
        for minor in (3,4,5):
            for index in (b'li',b'lf',b'lh',b'ri'):self.assertEqual(len(self.parse(minor=minor,index_kind=index)[1]),5)
        self.assertEqual(len(self.parse({p.upper():v for p,v in paths().items()})[1]),5)
        data=bytearray(hive_fixture(paths()));data[8]^=1
        with self.assertRaises(AnalysisError):dialog_mru.analyze_hive(bytes(data),1,Report())

    def test_cli_repeated_hives_source_hash_and_schema(self):
        p=self.file('renamed',hive_fixture(paths()));before=p.read_bytes()
        result=subprocess.run([sys.executable,'-m','plaintrace','--dialog-mru',str(p),'--dialog-mru',str(p)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);payload=json.loads(result.stdout);self.assertEqual(payload['format_version'],15);self.assertEqual(payload['counts']['dialog_mru_entries'],10)
        self.assertEqual([s['source_id'] for s in payload['sources']],[1,2]);self.assertEqual(payload['sources'][0]['sha256'],hashlib.sha256(before).hexdigest());self.assertEqual(p.read_bytes(),before)

    def test_json_sqlite_schema_raw_unicode_and_foreign_keys(self):
        p=self.file('hive',hive_fixture(paths()));report=analyze(dialog_hives=[p]);js=self.folder/'out.json';db=self.folder/'out.sqlite'
        write_report(report,js);write_report(report,db,'sqlite');self.assertEqual(json.loads(js.read_text())['format_version'],15)
        with closing(sqlite3.connect(db)) as c:
            self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],15);self.assertFalse(c.execute('PRAGMA foreign_key_check').fetchall())
            self.assertEqual(c.execute('SELECT application_name FROM dialog_mru_entries ORDER BY rowid').fetchall(),[(r['application_name'],) for r in report.dialog_mru_entries])
            self.assertEqual(c.execute('SELECT value_data_hex FROM dialog_mru_entries ORDER BY rowid').fetchall(),[(r['value_data_hex'],) for r in report.dialog_mru_entries])
            c.execute('PRAGMA foreign_keys=ON')
            with self.assertRaises(sqlite3.IntegrityError):c.execute("UPDATE dialog_mru_entries SET key_id='missing'")
            c.rollback()
            with self.assertRaises(sqlite3.IntegrityError):c.execute("UPDATE dialog_mru_keys SET parent_key_id='missing'")

    def test_cli_codepage_option_and_sqlite(self):
        p=self.file('hive',hive_fixture({OPEN+'\\txt':[opened(0,volume(),file_item('경로',encoding='cp949')),mru(0)],LAST:[mru()]}));out=self.folder/'out.sqlite'
        result=subprocess.run([sys.executable,'-m','plaintrace','--dialog-mru',str(p),'--dialog-mru-codepage','cp949','--format','sqlite','--output',str(out)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        with closing(sqlite3.connect(out)) as c:self.assertEqual(c.execute('SELECT path_candidate FROM dialog_mru_entries').fetchone()[0],'C:\\경로')

    def test_mixed_adapters_keep_source_order_and_no_automatic_joins(self):
        from shellbag_fixtures import paths as bags
        source=paths();source.update(bags());p=self.file('hive',hive_fixture(source));report=analyze(shellbag_hives=[('ntuser',p)],dialog_hives=[p])
        self.assertEqual([s['source_kind'] for s in report.sources],['shellbags','dialog_mru']);self.assertTrue(report.shellbag_entries);self.assertTrue(all(r['source_id']==2 for r in report.dialog_mru_entries))

    def test_cli_strict_later_failure_atomic_and_evidence_protection(self):
        p=self.file('hive',hive_fixture({LAST:[]}));bad=self.file('bad',b'bad');out=self.folder/'strict.json';absent=self.folder/'absent.json'
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            self.assertEqual(main(['--dialog-mru',str(p),'--strict','--output',str(out)]),1)
            self.assertEqual(main(['--dialog-mru',str(p),'--output',str(p)]),2)
            self.assertEqual(main(['--dialog-mru',str(p),'--dialog-mru',str(bad),'--output',str(absent)]),2)
        self.assertTrue(out.exists());self.assertFalse(absent.exists())

    def test_only_supplied_hive_opened_and_changes_rejected(self):
        p=self.file('hive',hive_fixture(paths()));opened_paths=[];real=Path.open
        def watch(path,*args,**kw):opened_paths.append(path);return real(path,*args,**kw)
        with patch.object(Path,'open',watch):analyze(dialog_hives=[p])
        self.assertEqual(set(opened_paths),{p.resolve()})
        with patch('plaintrace.binary.bounded_hash',side_effect=['a','b']),self.assertRaises(AnalysisError):analyze(dialog_hives=[p])

    def test_mutated_hives_have_controlled_failures(self):
        data=hive_fixture(paths());rng=random.Random(1010)
        for _ in range(60):
            raw=bytearray(data);offset=rng.randrange(len(raw));raw[offset]^=rng.randrange(1,256)
            try:keys,rows=dialog_mru.analyze_hive(bytes(raw),1,Report());json.dumps([keys,rows],allow_nan=False)
            except AnalysisError:pass
