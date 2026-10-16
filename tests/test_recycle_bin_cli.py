"""Independent synthetic $I layouts; no acquired evidence or $R recovery."""
from contextlib import closing, redirect_stderr, redirect_stdout
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

from plaintrace import recycle_bin
from plaintrace.cli import main
from plaintrace.evidence import AnalysisError
from plaintrace.execution import analyze
from plaintrace.exports import write_report
from plaintrace.model import Report
from test_browser_cli import chromium
from test_execution_cli import shell_link, pf_fixture
from test_evtx_cli import HAS_DECODER, evtx_fixture

FT = 132223104001234567
UTC = '2020-01-01T00:00:00.123456Z'


def index_fixture(version=2, path='C:\\Users\\한글\\자료.txt', size=123456, ticks=FT, raw=None, count=None, extra=b''):
    raw = (path+'\0').encode('utf-16-le') if raw is None else raw
    header = struct.pack('<QQQ',version,size,ticks)
    if version == 1:
        return header+raw+b'\0'*(520-len(raw))+extra
    return header+struct.pack('<I',len(raw)//2 if count is None else count)+raw+extra


class RecycleBinTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.folder=Path(self.temporary.name)
    def tearDown(self):self.temporary.cleanup()
    def file(self,name,data):
        path=self.folder/name;path.write_bytes(data);return path
    def parse(self,data):
        report=Report();row=recycle_bin.parse(data,1,report);return row,report

    def test_version_one_fixed_layout_and_raw_fields(self):
        row,report=self.parse(index_fixture(1))
        self.assertEqual(row['version'],1);self.assertIsNone(row['path_length_units'])
        self.assertEqual(row['original_path'],'C:\\Users\\한글\\자료.txt');self.assertEqual(row['original_size'],'123456')
        self.assertEqual(row['deleted_at'],UTC);self.assertEqual(row['deletion_filetime_raw'],str(FT))
        self.assertEqual(len(bytes.fromhex(row['path_utf16_hex'])),520);self.assertEqual(row['trailing_data_hex'],'')
        self.assertFalse(report.diagnostics)

    def test_version_two_counted_layout_and_utf16_units(self):
        path='C:\\😀\\A.txt';raw=(path+'\0').encode('utf-16-le')
        row,report=self.parse(index_fixture(path=path))
        self.assertEqual(row['path_length_units'],len(raw)//2);self.assertNotEqual(row['path_length_units'],len(path)+1)
        self.assertEqual(row['original_path'],path);self.assertEqual(row['path_utf16_hex'],raw.hex());self.assertFalse(report.diagnostics)

    def test_literal_unc_extended_relative_and_special_paths(self):
        for path in ['\\\\server\\share\\資料.txt','\\\\?\\C:\\long\\a.txt','..\\relative','C:\\%TEMP%\\A,B\'C\n.txt','http://literal','C:/mixed/../a']:
            row,report=self.parse(index_fixture(path=path));self.assertEqual(row['original_path'],path);self.assertFalse(report.diagnostics)

    def test_unsigned_sizes_and_zero_size_preserved(self):
        for size in (0,2**63,2**64-1):
            row,report=self.parse(index_fixture(size=size));self.assertEqual(row['original_size'],str(size));self.assertFalse(report.diagnostics)

    def test_zero_and_overflow_deletion_times_are_diagnostic(self):
        for ticks,code in [(0,'recycle_missing_deletion_time'),(2**64-1,'invalid_filetime')]:
            row,report=self.parse(index_fixture(ticks=ticks));self.assertIsNone(row['deleted_at']);self.assertEqual(row['deletion_filetime_raw'],str(ticks))
            self.assertIn(code,{d['code'] for d in report.diagnostics})

    def test_empty_paths_are_retained_with_warning(self):
        for version in (1,2):
            row,report=self.parse(index_fixture(version,path=''));self.assertEqual(row['original_path'],'')
            self.assertEqual(report.diagnostics[0]['code'],'recycle_empty_path')

    def test_malformed_utf16_preserves_bytes_and_escapes(self):
        raw=b'C\0:\0\\\0\x00\xd8\0\0'
        row,report=self.parse(index_fixture(raw=raw));self.assertEqual(row['path_utf16_hex'],raw.hex())
        self.assertIn('\\x00\\xd8',row['original_path']);self.assertEqual(report.diagnostics[0]['code'],'invalid_artifact_text')

    def test_version_one_nonzero_padding_retained_and_diagnosed(self):
        raw='C:\\A\0REMNANT'.encode('utf-16-le');row,report=self.parse(index_fixture(1,raw=raw))
        self.assertEqual(row['original_path'],'C:\\A');self.assertEqual(bytes.fromhex(row['path_utf16_hex'])[:len(raw)],raw)
        self.assertEqual(report.diagnostics[0]['code'],'recycle_path_padding')

    def test_version_two_early_terminator_and_padding_warn(self):
        for raw in ['C:\\A\0OLD\0'.encode('utf-16-le'),'C:\\A\0\0'.encode('utf-16-le')]:
            row,report=self.parse(index_fixture(raw=raw));self.assertEqual(row['original_path'],'C:\\A')
            self.assertIn('recycle_path_length_mismatch',{d['code'] for d in report.diagnostics});self.assertEqual(row['path_utf16_hex'],raw.hex())

    def test_trailing_bytes_are_opaque_and_diagnosed(self):
        for version in (1,2):
            for extra in (b'\0',b'\x01\xff\x00'):
                row,report=self.parse(index_fixture(version,extra=extra));self.assertEqual(row['trailing_data_hex'],extra.hex())
                self.assertEqual(report.diagnostics[0]['code'],'recycle_trailing_data')

    def test_unknown_versions_and_short_headers_rejected(self):
        for data in [b'',b'\0'*23,struct.pack('<Q',0),struct.pack('<Q',3),struct.pack('<Q',2**64-1),struct.pack('<QQQ',2,1,FT)]:
            with self.assertRaises(AnalysisError):self.parse(data)

    def test_invalid_lengths_counts_and_missing_terminators_rejected(self):
        for data in [index_fixture(count=0),index_fixture(count=2**32-1),index_fixture(count=100),index_fixture(raw=b'A\0',count=1),index_fixture(1,raw=b'A\0'*260),index_fixture()[:-1]]:
            with self.assertRaises(AnalysisError):self.parse(data)

    def test_every_truncated_prefix_of_both_layouts_fails(self):
        for version in (1,2):
            data=index_fixture(version)
            for length in range(len(data)):
                with self.subTest(version=version,length=length),self.assertRaises(AnalysisError):self.parse(data[:length])

    def test_path_and_input_limits_cover_direct_parser_and_cli(self):
        raw=('A'*(recycle_bin.MAX_PATH_UNITS-1)+'\0').encode('utf-16-le')
        row,report=self.parse(index_fixture(raw=raw));self.assertEqual(len(row['original_path']),32767);self.assertFalse(report.diagnostics)
        with self.assertRaises(AnalysisError):self.parse(index_fixture(raw=raw+b'\0\0'))
        with self.assertRaises(AnalysisError):self.parse(b'\0'*(recycle_bin.MAX_RECYCLE_BYTES+1))
        path=self.file('large',b'\0'*(recycle_bin.MAX_RECYCLE_BYTES+1))
        with self.assertRaises(AnalysisError):analyze(recycle_bins=[path])

    def test_renamed_and_repeated_sources_have_stable_hash_and_lineage(self):
        path=self.file('renamed.bin',index_fixture());before=path.read_bytes();report=analyze(recycle_bins=[path,path])
        self.assertEqual([r['source_id'] for r in report.recycle_bin],[1,2]);self.assertEqual([r['record_id'] for r in report.recycle_bin],['0','0'])
        self.assertEqual([s['source_kind'] for s in report.sources],['recycle_bin','recycle_bin']);self.assertEqual(report.sources[0]['sha256'],hashlib.sha256(before).hexdigest())
        self.assertIsNone(report.sources[0]['database_sha256']);self.assertEqual(path.read_bytes(),before)

    def test_changed_input_fails_without_publication(self):
        path=self.file('$IABC',index_fixture());output=self.folder/'out.json'
        with patch('plaintrace.binary.bounded_hash',side_effect=['changed','changed']),redirect_stderr(io.StringIO()):
            code=main(['--recycle-bin',str(path),'--output',str(output)])
        self.assertEqual(code,2);self.assertFalse(output.exists())

    def test_json_sqlite_schema_four_and_unsigned_size_roundtrip(self):
        path=self.file('$IBIG',index_fixture(size=2**64-1,path="C:\\A,B'\n😀"));report=analyze(recycle_bins=[path])
        json_path=self.folder/'out.json';sql_path=self.folder/'out.sqlite';write_report(report,json_path);write_report(report,sql_path,'sqlite')
        payload=json.loads(json_path.read_text());self.assertEqual(payload['format_version'],10);self.assertEqual(payload['counts']['recycle_bin'],1)
        self.assertEqual(payload['recycle_bin'][0]['original_size'],str(2**64-1))
        with closing(sqlite3.connect(sql_path)) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],10)
            self.assertEqual(db.execute('SELECT original_size,original_path,deletion_filetime_raw FROM recycle_bin').fetchone(),(str(2**64-1),"C:\\A,B'\n😀",str(FT)))
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
            self.assertEqual(json.loads(db.execute("SELECT value FROM metadata WHERE key='counts'").fetchone()[0])['recycle_bin'],1)

    def test_cli_stdout_strict_and_real_subprocess(self):
        path=self.file('$IABC',index_fixture(ticks=0));out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):code=main(['--recycle-bin',str(path),'--strict'])
        self.assertEqual(code,1);self.assertEqual(len(json.loads(out.getvalue())['recycle_bin']),1);self.assertIn('recycle_missing_deletion_time',err.getvalue())
        valid=self.file('$IVALID',index_fixture(1));result=subprocess.run([sys.executable,'-m','plaintrace','--recycle-bin',str(valid)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout)['recycle_bin'][0]['deleted_at'],UTC)

    def test_cli_all_or_nothing_when_later_input_fails(self):
        good=self.file('$IGOOD',index_fixture());bad=self.file('$IBAD',b'broken');output=self.folder/'out.json';out=io.StringIO()
        with redirect_stdout(out),redirect_stderr(io.StringIO()):code=main(['--recycle-bin',str(good),'--recycle-bin',str(bad),'--output',str(output)])
        self.assertEqual(code,2);self.assertFalse(output.exists());self.assertFalse(out.getvalue());self.assertFalse(list(self.folder.glob('.plaintrace-*')))

    def test_existing_output_sidecar_and_evidence_collision_preserved(self):
        path=self.file('$IABC',index_fixture());report=analyze(recycle_bins=[path]);before=path.read_bytes()
        for output in [path,Path(str(path)+'-wal')]:
            with self.assertRaises(AnalysisError):write_report(report,output)
        output=self.file('existing.json',b'other');old=output.read_bytes()
        with self.assertRaises(AnalysisError):write_report(report,output)
        sql=self.folder/'sidecar.sqlite';sidecar=self.file(sql.name+'-wal',b'other-wal')
        with self.assertRaises(AnalysisError):write_report(report,sql,'sqlite')
        self.assertEqual(path.read_bytes(),before);self.assertEqual(output.read_bytes(),old);self.assertEqual(sidecar.read_bytes(),b'other-wal')

    def test_no_payload_sid_owner_or_target_filesystem_inference(self):
        sid_dir=self.folder/'S-1-5-21-123';sid_dir.mkdir();path=sid_dir/'$IABC';path.write_bytes(index_fixture(path=str(self.folder/'DO-NOT-OPEN')))
        sibling=sid_dir/'$RABC';sibling.write_bytes(b'not a metadata file')
        opened=[]
        original_open=Path.open
        def tracked_open(current,*args,**kwargs):
            opened.append(current)
            return original_open(current,*args,**kwargs)
        with patch.object(Path,'open',tracked_open):report=analyze(recycle_bins=[path])
        self.assertEqual(set(opened),{path.resolve()})
        row=report.recycle_bin[0]
        self.assertNotIn('sid',row);self.assertNotIn('owner',row);self.assertNotIn('payload_exists',row)
        self.assertEqual(row['original_path'],str(self.folder/'DO-NOT-OPEN'));self.assertEqual(sibling.read_bytes(),b'not a metadata file')
        self.assertEqual(len(report.sources),1)

    def test_mixed_browser_link_prefetch_and_recycle_sources(self):
        browser=self.folder/'History'
        with closing(sqlite3.connect(browser)) as db:chromium(db)
        link=self.file('a.lnk',shell_link({'relative_path':'APP.EXE'}));pf=self.file('a.pf',pf_fixture());index=self.file('$IABC',index_fixture())
        report=analyze([browser],[link],[pf],recycle_bins=[index])
        self.assertEqual([s['source_kind'] for s in report.sources],['browser','lnk','prefetch','recycle_bin'])
        self.assertEqual(report.recycle_bin[0]['source_id'],4);self.assertEqual(report.as_dict()['format_version'],10)

    @unittest.skipUnless(HAS_DECODER,'optional python-evtx==0.8.1 not installed')
    def test_mixed_five_source_cli_with_actual_evtx_decoder(self):
        browser=self.folder/'History'
        with closing(sqlite3.connect(browser)) as db:chromium(db)
        link=self.file('a.lnk',shell_link({'relative_path':'APP.EXE'}));pf=self.file('a.pf',pf_fixture());log=self.file('a.evtx',evtx_fixture());index=self.file('$IABC',index_fixture())
        args=[sys.executable,'-m','plaintrace','--input',str(browser),'--lnk',str(link),'--prefetch',str(pf),'--evtx',str(log),'--recycle-bin',str(index)]
        result=subprocess.run(args,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr);payload=json.loads(result.stdout)
        self.assertEqual([s['source_kind'] for s in payload['sources']],['browser','lnk','prefetch','evtx','recycle_bin']);self.assertEqual(payload['recycle_bin'][0]['source_id'],5)
        output=self.folder/'mixed.sqlite';result=subprocess.run(args+['--format','sqlite','--output',str(output)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        with closing(sqlite3.connect(output)) as db:self.assertEqual(db.execute('SELECT source_id FROM recycle_bin').fetchone()[0],5)

    def test_mutated_inputs_only_raise_contract_errors(self):
        rng=random.Random(2017)
        for version in (1,2):
            data=index_fixture(version)
            for _ in range(100):
                mutated=bytearray(data);offset=rng.randrange(len(data));mutated[offset]^=rng.randrange(1,256)
                try:self.parse(mutated)
                except AnalysisError:pass

    def test_review_utf16_terminator_is_aligned_not_byte_substring(self):
        row,report=self.parse(index_fixture(path='C:\\ĀA'))
        self.assertEqual(row['original_path'],'C:\\ĀA');self.assertFalse(report.diagnostics)

    def test_review_version_one_543_byte_anomaly_is_not_guessed(self):
        canonical=index_fixture(1);anomalous=canonical[:15]+canonical[16:]
        self.assertEqual(len(anomalous),543)
        with self.assertRaises(AnalysisError):self.parse(anomalous)

    def test_review_directory_and_unknown_files_fail_without_report(self):
        for path in [self.folder,self.folder/'missing',self.file('$RABC',b'payload'),self.file('INFO2',b'INFO2\0'*100)]:
            output=self.folder/'out.json'
            with redirect_stderr(io.StringIO()):code=main(['--recycle-bin',str(path),'--output',str(output)])
            self.assertEqual(code,2);self.assertFalse(output.exists())

    def test_review_other_artifact_options_do_not_change_recycle_parsing(self):
        path=self.file('renamed.bin',index_fixture());out=io.StringIO()
        with redirect_stdout(out):code=main(['--recycle-bin',str(path),'--browser','firefox','--lnk-codepage','nonexistent'])
        self.assertEqual(code,0);self.assertEqual(json.loads(out.getvalue())['recycle_bin'][0]['original_path'],'C:\\Users\\한글\\자료.txt')
