"""Synthetic application MRU hives; independent raw and timestamp oracles."""
from contextlib import closing,redirect_stdout,redirect_stderr
import hashlib
import io
import json
from pathlib import Path
import random
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from plaintrace import application_mru as app
from plaintrace.cli import main
from plaintrace.evidence import AnalysisError
from plaintrace.execution import analyze
from plaintrace.exports import write_report
from plaintrace.model import Report
from test_usb_registry_cli import hive_fixture,value,text,FT,UTC,system_paths

OFFICE=r'Software\Microsoft\Office\16.0\Word\File MRU'
HWP=r'Software\Hnc\Hwp\9.0\HwpFrame_KOR\RecentFile'
ADOBE=r'Software\Adobe\Acrobat Reader\DC\AVGeneral\cRecentFiles'
def paths():
    return {OFFICE:[text('Item 1',f'[F00000000][T{FT:016X}][O00000000]*C:\\a.docx'),text('Item 9','C:\\late.docx')],
            HWP:[value('file0',3,('한글😀.hwp\0').encode('utf-16-le'))],
            ADOBE:[value('iMax',4,b'\x32\0\0\0',inline=True)],ADOBE+'\\c1':[text('tDIText','/C/docs/a.pdf'),text('aFS','DOS')],
            ADOBE+'\\c3':[text('tDIText','/C/docs/b.pdf')]}

class ApplicationMRUTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def file(self,name,data):p=self.folder/name;p.write_bytes(data);return p
    def parse(self,source=None,**kwargs):
        report=Report();keys,entries=app.analyze_hive(hive_fixture(paths() if source is None else source,**kwargs),1,report)
        return keys,entries,report

    def test_three_families_sparse_slots_and_raw_time(self):
        keys,rows,report=self.parse();self.assertEqual(len(keys),5);self.assertEqual(len(rows),5);self.assertFalse(report.diagnostics)
        self.assertEqual(rows[0]['stored_path'],r'C:\a.docx');self.assertEqual(rows[0]['embedded_filetime_raw'],str(FT));self.assertEqual(rows[0]['embedded_at'],UTC)
        self.assertEqual(rows[1]['slot_number'],9);self.assertEqual(rows[2]['stored_path'],'한글😀.hwp')
        self.assertEqual([r['slot_number'] for r in rows if r['family']=='adobe'],[1,3])

    def test_office_versions_apps_places_and_user_scopes(self):
        source={}
        for version in ('13.0','14.0','15.0','16.0'):
            for name in ('Word','Excel','PowerPoint'):
                for tail in ('File MRU','Place MRU',r'User MRU\opaque-account\File MRU'):
                    source[f'Software\\Microsoft\\Office\\{version}\\{name}\\{tail}']=[text('Item 1','literal')]
        keys,rows,_=self.parse(source);self.assertEqual(len(rows),36)
        self.assertEqual({r['scope'] for r in rows},{None,'opaque-account'});self.assertEqual({r['list_kind'] for r in rows},{'File MRU','Place MRU'})
        self.assertEqual(len(keys),36)

    def test_office_prefix_delimiter_and_opaque_flags(self):
        _,rows,_=self.parse({OFFICE:[text('Item 1','[F00000001][Xopaque]*a*b.doc')]})
        self.assertEqual(rows[0]['stored_path'],'a*b.doc');self.assertEqual(rows[0]['metadata_tokens'],[{'tag':'F','raw':'00000001'},{'tag':'X','raw':'opaque'}])
        self.assertNotIn('pinned',rows[0])

    def test_invalid_and_duplicate_office_times_do_not_guess(self):
        for prefix in ('[Tbad]',f'[T{FT:016X}][T{FT:016X}]'):
            _,rows,report=self.parse({OFFICE:[text('Item 1',prefix+'*a')]})
            self.assertIsNone(rows[0]['embedded_at']);self.assertIsNone(rows[0]['embedded_filetime_raw']);self.assertEqual(rows[0]['stored_path'],'a')
            self.assertIn('app_mru_invalid_office_time',{d['code'] for d in report.diagnostics})

    def test_office_zero_and_overflow_filetime(self):
        for ticks in (0,2**64-1):
            _,rows,_=self.parse({OFFICE:[text('Item 1',f'[T{ticks:016X}]*a')]})
            self.assertEqual(rows[0]['embedded_filetime_raw'],str(ticks));self.assertIsNone(rows[0]['embedded_at'])

    def test_unrecognized_prefix_retains_raw_without_path(self):
        for path in ('[Tbad]a','[broken','[123]*a'):
            _,rows,_=self.parse({OFFICE:[text('Item 1',path)]});self.assertEqual(rows[0]['raw_text'],path);self.assertIsNone(rows[0]['stored_path'])

    def test_plain_office_path_no_time_or_normalization(self):
        path="%USERPROFILE%\\a,'\n😀.doc";_,rows,_=self.parse({OFFICE:[value('Item 1',2,(path+'\0').encode('utf-16-le'))]})
        self.assertEqual(rows[0]['stored_path'],path);self.assertIsNone(rows[0]['embedded_at']);self.assertEqual(rows[0]['path_basis'],'plain_value')

    def test_hwp_frames_versions_binary_bom_and_regsz(self):
        source={HWP:[value('file0',3,b'\xff\xfe'+('한글\0').encode('utf-16-le'))],HWP.replace('HwpFrame_KOR','HwpFrame'):[text('file9','next')],r'Software\Hnc\Common\9.6\CommonFrame\RecentFile':[text('file0','common')]}
        _,rows,_=self.parse(source);self.assertEqual([r['stored_path'] for r in rows],['한글','next','common']);self.assertEqual(rows[1]['slot_number'],9)

    def test_hwp_big_endian_not_interpreted(self):
        _,rows,report=self.parse({HWP:[value('file0',3,b'\xfe\xff\0a\0\0')]})
        self.assertIsNone(rows[0]['stored_path']);self.assertEqual(rows[0]['value_data_hex'],'feff00610000');self.assertTrue(report.diagnostics)

    def test_adobe_products_versions_and_literal_paths(self):
        source={}
        for product in ('Acrobat Reader','Adobe Acrobat'):
            for version in ('DC','11.0'):
                source[f'Software\\Adobe\\{product}\\{version}\\AVGeneral\\cRecentFiles\\c9']=[text('tDIText','/C/literal%20file.pdf')]
        keys,rows,_=self.parse(source);self.assertEqual(len(keys),8);self.assertEqual(len(rows),4)
        self.assertTrue(all(r['stored_path']=='/C/literal%20file.pdf' for r in rows));self.assertTrue(all(r['embedded_at'] is None for r in rows))

    def test_adobe_missing_path_unknown_slot_and_metadata(self):
        keys,rows,report=self.parse({ADOBE:[],ADOBE+'\\c1':[text('sDI','ascii')],ADOBE+'\\c01':[text('tDIText','not selected')]})
        self.assertFalse(rows);self.assertEqual(len(keys),2);self.assertEqual(keys[1]['metadata_values'][0]['name'],'sDI')
        self.assertTrue({'app_mru_missing_path','app_mru_unknown_adobe_slot'}<={d['code'] for d in report.diagnostics})

    def test_noncanonical_names_retained_as_metadata(self):
        keys,rows,_=self.parse({OFFICE:[text(n,'x') for n in ('Item 0','Item 01','Item 1000000000','Item ı','Unknown')],HWP:[text('file00','x')]})
        self.assertFalse(rows);self.assertEqual(sum(len(k['metadata_values']) for k in keys),6)

    def test_case_insensitive_canonical_names(self):
        _,rows,_=self.parse({OFFICE:[text('iTEM 2','a')],HWP:[text('FILE0','b')],ADOBE+'\\C4':[text('TDITEXT','c')]})
        self.assertEqual([r['slot_number'] for r in rows],[2,0,4])

    def test_wrong_type_and_invalid_unicode_keep_bytes(self):
        for val in (value('Item 1',3,b'raw'),value('Item 1',1,b'\0\xd8\0\0'),value('Item 1',1,b'a')):
            _,rows,_=self.parse({OFFICE:[val]});self.assertIsNone(rows[0]['stored_path']);self.assertEqual(rows[0]['value_data_hex'],val[2].hex())

    def test_embedded_nul_unterminated_and_empty_text(self):
        _,rows,report=self.parse({OFFICE:[text('Item 1','a\0b'),value('Item 2',1,b'A\0'),text('Item 3','')]})
        self.assertIsNone(rows[0]['stored_path']);self.assertEqual(rows[1]['stored_path'],'A');self.assertEqual(rows[2]['stored_path'],'')
        self.assertTrue({'app_mru_embedded_nul','app_mru_unterminated_text','app_mru_empty_path'}<={d['code'] for d in report.diagnostics})

    def test_duplicates_key_time_and_offsets_are_scoped(self):
        keys,rows,_=self.parse({OFFICE:[text('Item 1','a'),text('Item 3','a')],HWP:[text('file0','a')]})
        self.assertEqual(len(rows),3);self.assertTrue(all(k['key_last_written']==UTC and k['key_last_write_raw']==str(FT) for k in keys))
        self.assertTrue(all(int(r['record_id'])>=4096 and r['key_id'] in {k['record_id'] for k in keys} for r in rows));self.assertTrue(all(r['embedded_at'] is None for r in rows))
        self.assertNotIn('mru_rank',rows[0]);self.assertNotIn('opened_at',rows[0])

    def test_missing_families_and_existing_empty_key(self):
        keys,rows,report=self.parse({'Unrelated':[]});self.assertFalse(keys);self.assertFalse(rows);self.assertIn('app_mru_no_lists',{d['code'] for d in report.diagnostics})
        keys,rows,_=self.parse({OFFICE:[]});self.assertEqual(len(keys),1);self.assertFalse(rows)

    def test_regf_supported_indexes_and_dirty_header(self):
        for index in (b'li',b'lf',b'lh',b'ri'):
            self.assertEqual(len(self.parse(index_kind=index)[1]),5)
        data=bytearray(hive_fixture(paths()));data[8]^=1
        with self.assertRaises(AnalysisError):app.analyze_hive(bytes(data),1,Report())

    def test_adapter_budgets_reject_without_partial_output(self):
        for name in ('MAX_KEYS','MAX_ENTRIES','MAX_OUTPUT_BYTES'):
            with patch.object(app,name,1),self.assertRaises(AnalysisError):self.parse()

    def test_cli_repeated_sources_hashes_and_schema(self):
        path=self.file('NTUSER',hive_fixture(paths()));before=path.read_bytes()
        result=subprocess.run([sys.executable,'-m','plaintrace','--application-mru',str(path),'--application-mru',str(path)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);payload=json.loads(result.stdout);self.assertEqual(payload['format_version'],7)
        self.assertEqual(payload['counts']['application_mru'],10);self.assertEqual([s['source_id'] for s in payload['sources']],[1,2])
        self.assertEqual(payload['sources'][0]['sha256'],hashlib.sha256(before).hexdigest());self.assertEqual(path.read_bytes(),before)

    def test_json_sqlite_roundtrip_and_parent_foreign_key(self):
        path=self.file('hive',hive_fixture(paths()));report=analyze(application_hives=[path]);js=self.folder/'out.json';db=self.folder/'out.sqlite'
        write_report(report,js);write_report(report,db,'sqlite');payload=json.loads(js.read_text());self.assertEqual(payload['format_version'],7)
        with closing(sqlite3.connect(db)) as conn:
            self.assertEqual(conn.execute('PRAGMA user_version').fetchone()[0],7);self.assertFalse(conn.execute('PRAGMA foreign_key_check').fetchall())
            self.assertEqual(conn.execute('SELECT stored_path FROM application_mru ORDER BY rowid').fetchall(),[(r['stored_path'],) for r in report.application_mru])
            conn.execute('PRAGMA foreign_keys=ON')
            with self.assertRaises(sqlite3.IntegrityError):conn.execute("UPDATE application_mru SET key_id='absent'")

    def test_mixed_registry_sources_no_automatic_joins(self):
        from test_recent_docs_cli import paths as recent_paths
        source=paths();source.update(recent_paths());source.update(system_paths());path=self.file('combined',hive_fixture(source))
        report=analyze(usb_hives=[('system',path)],recent_hives=[path],application_hives=[path])
        self.assertEqual([s['source_kind'] for s in report.sources],['usb_registry','recent_docs','application_mru']);self.assertTrue(all(r['source_id']==3 for r in report.application_mru));self.assertTrue(report.recent_docs)

    def test_cli_strict_fatal_output_and_evidence_collision(self):
        path=self.file('hive',hive_fixture({OFFICE:[]}));output=self.folder/'strict.json'
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            self.assertEqual(main(['--application-mru',str(path),'--strict','--output',str(output)]),1)
            self.assertEqual(main(['--application-mru',str(path),'--output',str(path)]),2)
            broken=self.file('bad',b'bad');missing=self.folder/'absent.json'
            self.assertEqual(main(['--application-mru',str(path),'--application-mru',str(broken),'--output',str(missing)]),2)
        self.assertTrue(output.exists());self.assertFalse(missing.exists())

    def test_nested_list_keys_are_diagnosed(self):
        keys,rows,report=self.parse({OFFICE:[text('Item 1','a')],OFFICE+'\\nested':[text('Item 1','hidden')]})
        self.assertEqual(len(rows),1);self.assertEqual(len(keys),1);self.assertIn('app_mru_nested_keys',{d['code'] for d in report.diagnostics})

    def test_deterministic_mutations_have_controlled_failures(self):
        original=hive_fixture(paths());rng=random.Random(701)
        for _ in range(40):
            data=bytearray(original);offset=rng.randrange(len(data));data[offset]^=rng.randrange(1,256)
            try:keys,rows=app.analyze_hive(bytes(data),1,Report());json.dumps([keys,rows],allow_nan=False)
            except AnalysisError:pass
