"""Synthetic CFB/DestList/custom categories and CLI lineage regressions."""
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
from plaintrace import jump_lists as jump,compound
from plaintrace.cli import main
from plaintrace.evidence import AnalysisError
from plaintrace.execution import analyze
from plaintrace.exports import write_report
from plaintrace.model import Report
from jump_fixtures import link,destlist,custom,compound as cfb,FT,UTC


def automatic(version=1,**kw):return cfb({'DestList':destlist(version,**kw),'1':link()})

class JumpListTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def file(self,name,data):p=self.folder/name;p.write_bytes(data);return p
    def parse(self,data=None):
        report=Report();summary,rows=jump.parse(automatic() if data is None else data,1,report);return summary,rows,report

    def test_automatic_v1_raw_time_guid_and_link_association(self):
        summary,rows,report=self.parse();self.assertEqual(summary['container_kind'],'automatic');self.assertEqual(summary['version'],1)
        r=rows[0];self.assertEqual(r['stored_path'],r'C:\document.txt');self.assertEqual(r['association'],'matched');self.assertEqual(r['link_status'],'parsed')
        self.assertEqual(r['last_modified_filetime_raw'],str(FT));self.assertEqual(r['last_modified_at'],UTC);self.assertEqual(r['hostname'],'HOST')
        self.assertEqual(r['droids']['volume'],'03020100-0504-0706-0809-0a0b0c0d0e0f');self.assertEqual(r['link']['relative_path'],'relative.txt');self.assertFalse(report.diagnostics)
        self.assertEqual(r['link']['record_id'],r['record_id']);self.assertNotIn('opened_at',r)

    def test_v3_v4_extensions_and_pinned_state(self):
        for version in (3,4):
            summary,rows,report=self.parse(automatic(version,records=[dict(number=1,path='한글😀',pin=3,extension=b'opaque')]))
            self.assertEqual(summary['version'],version);self.assertEqual(rows[0]['extension_hex'],b'opaque'.hex());self.assertTrue(rows[0]['pinned']);self.assertEqual(rows[0]['pin_status'],3)
            self.assertIn('jump_opaque_extension',{d['code'] for d in report.diagnostics})

    def test_destlist_version_two_and_future_rejected(self):
        for version in (0,2,5):
            with self.assertRaises(AnalysisError):self.parse(automatic(version))

    def test_mini_and_regular_streams_cfb_v3_v4_fragmented(self):
        large=destlist(records=[dict(number=i,path='x'*80) for i in range(1,21)])
        for version in (3,4):
            data=cfb({'DestList':large,'1':link()},version,fragment=True);summary,rows,_=self.parse(data)
            self.assertEqual(len(rows),20);self.assertEqual(rows[0]['association'],'matched')
            stream=next(s for s in summary['streams'] if s['name']=='DestList');self.assertFalse(stream['mini'])
            self.assertGreater(stream['block_offsets'][0],stream['block_offsets'][-1])
            for row in rows:
                offset=row['file_offset'];self.assertEqual(data[offset:offset+8],bytes.fromhex(row['raw_entry_hex'])[:8])

    def test_ministream_many_mini_sectors_and_physical_offsets(self):
        summary,rows,_=self.parse(cfb({'DestList':destlist(records=[dict(number=i,path='text') for i in range(1,15)]),'1':link()}))
        self.assertEqual(len(rows),14);self.assertTrue(summary['streams'][0]['mini'])
        self.assertTrue(all(r['file_offset']>=512 for r in rows));self.assertEqual(rows[-1]['entry_number'],'14')

    def test_missing_empty_destlist_and_unassociated_links(self):
        for streams,code in (({'1':link()},'jump_missing_destlist'),({'DestList':b'','1':link()},'jump_empty_destlist')):
            summary,rows,report=self.parse(cfb(streams));self.assertEqual(rows[0]['association'],'unassociated');self.assertIsNone(rows[0]['last_modified_at'])
            self.assertIn(code,{d['code'] for d in report.diagnostics})

    def test_missing_links_and_orphans_are_not_discarded(self):
        _,rows,report=self.parse(cfb({'DestList':destlist(records=[dict(number=9,path='missing')]),'1':link()}))
        self.assertEqual([r['association'] for r in rows],['missing','unassociated']);self.assertIsNone(rows[0]['link']);self.assertEqual(rows[1]['link_status'],'parsed')
        self.assertTrue({'jump_missing_link','jump_unassociated_link'}<={d['code'] for d in report.diagnostics})

    def test_duplicate_ids_ambiguous_no_silent_join(self):
        _,rows,_=self.parse(cfb({'DestList':destlist(records=[dict(number=1,path='a'),dict(number=1,path='b')]),'1':link()}))
        self.assertEqual([r['association'] for r in rows],['ambiguous','ambiguous','unassociated']);self.assertTrue(all(r['link'] is None for r in rows[:2]))

    def test_numbered_stream_case_and_unknown_metadata_retained(self):
        payload=destlist(records=[dict(number=10,path='A')]);summary,rows,report=self.parse(cfb({'DestList':payload,'A':link(),'01':b'opaque','Meta':b'raw'}))
        self.assertEqual(rows[0]['link_stream_name'],'A');self.assertEqual(rows[0]['association'],'matched')
        self.assertEqual(next(s for s in summary['streams'] if s['name']=='Meta')['raw_hex'],b'raw'.hex());self.assertIn('jump_unknown_stream',{d['code'] for d in report.diagnostics})

    def test_declared_count_trailing_bytes_retained_not_carved(self):
        summary,rows,report=self.parse(automatic(trailing=b'not another record'));self.assertEqual(len(rows),1)
        self.assertEqual(summary['trailing_data_hex'],b'not another record'.hex());self.assertIn('jump_destlist_trailing',{d['code'] for d in report.diagnostics})

    def test_invalid_utf16_nul_and_unknown_pin_retained(self):
        _,rows,report=self.parse(automatic(records=[dict(number=1,raw=b'\0\xd8\0\0',pin=-2)]))
        self.assertEqual(rows[0]['path_utf16_hex'],'00d80000');self.assertIsNone(rows[0]['pinned']);self.assertEqual(rows[0]['pin_status'],-2)
        self.assertIn('jump_invalid_pin',{d['code'] for d in report.diagnostics});self.assertIn('invalid_artifact_text',{d['code'] for d in report.diagnostics})

    def test_zero_overflow_and_pinned_count_diagnostic(self):
        for ticks in (0,2**64-1):
            _,rows,report=self.parse(automatic(records=[dict(number=1,path='x',ticks=ticks)],pinned=1))
            self.assertIsNone(rows[0]['last_modified_at']);self.assertEqual(rows[0]['last_modified_filetime_raw'],str(ticks));self.assertIn('jump_pinned_count',{d['code'] for d in report.diagnostics})

    def test_invalid_embedded_lnk_raw_retained(self):
        _,rows,report=self.parse(cfb({'DestList':destlist(),'1':b'not a shortcut'}))
        self.assertEqual(rows[0]['link_status'],'invalid');self.assertEqual(rows[0]['lnk_hex'],b'not a shortcut'.hex());self.assertIn('jump_invalid_link',{d['code'] for d in report.diagnostics})

    def test_lnk_diagnostics_use_unique_entry_identity(self):
        empty=bytearray(link());struct.pack_into('<I',empty,20,0);empty=bytes(empty[:76])+bytes(4)
        _,rows,report=self.parse(cfb({'DestList':destlist(),'1':empty,'2':empty}))
        identities={r['record_id'] for r in rows};self.assertEqual({d['record_id'] for d in report.diagnostics},identities)

    def test_cfb_fat_cycle_overlap_and_truncation_rejected(self):
        original=cfb({'DestList':destlist(),'1':link()});c=compound.Compound(original)
        fat_sid=int.from_bytes(original[76:80],'little');fat_offset=(fat_sid+1)*512
        mini_sid=int.from_bytes(original[60:64],'little')
        for offset,value in ((fat_offset+mini_sid*4,mini_sid),(48,0xffffffff)):
            data=bytearray(original);struct.pack_into('<I',data,offset,value)
            with self.assertRaises(AnalysisError):self.parse(bytes(data))
        for size in (0,7,511,len(original)-1):
            with self.assertRaises(AnalysisError):self.parse(original[:size])

    def test_cfb_minifat_cycle_and_duplicate_ownership_rejected(self):
        original=cfb({'DestList':destlist(),'1':link()});mini_sid=int.from_bytes(original[60:64],'little');data=bytearray(original)
        struct.pack_into('<I',data,(mini_sid+1)*512,0)
        with self.assertRaises(AnalysisError):self.parse(bytes(data))
        c=compound.Compound(original);directory_sid=int.from_bytes(original[48:52],'little');base=(directory_sid+1)*512
        data=bytearray(original);struct.pack_into('<I',data,base+2*128+116,c.streams[0]['start'])
        with self.assertRaises(AnalysisError):self.parse(bytes(data))

    def test_cfb_directory_cycle_nested_unreachable_and_duplicate_names(self):
        original=cfb({'DestList':destlist(),'1':link()});base=(int.from_bytes(original[48:52],'little')+1)*512
        for offset,value,width in ((base+128+72,1,4),(base+128+66,1,1),(base+76,0xffffffff,4)):
            data=bytearray(original);data[offset:offset+width]=value.to_bytes(width,'little')
            with self.assertRaises(AnalysisError):self.parse(bytes(data))
        with self.assertRaises(AnalysisError):self.parse(cfb({'DestList':b'','DESTLIST':b''}))

    def test_cfb_header_counts_format_and_stream_size_limits(self):
        original=cfb({'DestList':destlist()})
        for offset,width,value in ((26,2,2),(30,2,10),(32,2,7),(56,4,2048),(44,4,1000000),(64,4,1000000),(72,4,1000000)):
            data=bytearray(original);data[offset:offset+width]=value.to_bytes(width,'little')
            with self.assertRaises(AnalysisError):self.parse(bytes(data))
        with patch.object(compound,'MAX_STREAMS',1),self.assertRaises(AnalysisError):self.parse()

    def test_cfb_extended_difat_and_large_regular_stream(self):
        payload=b'x'*(8*1024*1024);data=cfb({'raw':payload});self.assertGreater(int.from_bytes(data[72:76],'little'),0)
        c=compound.Compound(data);self.assertEqual(c.payloads['raw'],payload)
        for offset,count in ((44,513),(64,4097)):
            bounded=bytearray(data);struct.pack_into('<I',bounded,offset,count)
            with self.assertRaises(AnalysisError):compound.Compound(bytes(bounded))
        dif=int.from_bytes(data[68:72],'little');bad=bytearray(data);struct.pack_into('<I',bad,(dif+1)*512+508,dif)
        with self.assertRaises(AnalysisError):compound.Compound(bytes(bad))

    def test_destlist_truncated_path_and_extension_are_fatal(self):
        for data in (destlist()[:-1],destlist(3,records=[dict(number=1,path='x',extension=b'abc')])[:-1]):
            with self.assertRaises(AnalysisError):self.parse(cfb({'DestList':data}))

    def test_custom_named_tasks_known_categories_and_full_lnk(self):
        summary,rows,report=self.parse(custom([dict(kind=0,name='문서😀',links=[link('a'),link('b')]),dict(kind=1,known=2),dict(kind=2,links=[link('task')])]))
        self.assertEqual(summary['container_kind'],'custom');self.assertEqual([c['kind'] for c in summary['categories']],[0,1,2]);self.assertEqual(len(rows),3)
        self.assertEqual([r['link']['relative_path'] for r in rows],['a','b','task']);self.assertEqual(rows[2]['category_index'],2);self.assertFalse(report.diagnostics)
        self.assertTrue(all(r['last_modified_at'] is None for r in rows));self.assertTrue(all(r['association']=='custom' for r in rows))

    def test_custom_clsid_body_preserves_original_and_normalized_lnk(self):
        original=link('body');_,rows,_=self.parse(custom([dict(kind=2,links=[original[4:]])]))
        self.assertEqual(rows[0]['raw_entry_hex'],original[4:].hex());self.assertEqual(rows[0]['lnk_hex'],original.hex());self.assertEqual(rows[0]['link_representation'],'clsid_body')

    def test_custom_does_not_split_embedded_signatures(self):
        text=(struct.pack('<I',jump.FOOTER)+b'L\0N\0K\0').decode('utf-16-le')
        _,rows,_=self.parse(custom([dict(kind=2,links=[link(text),link('next')])]))
        self.assertEqual(len(rows),2);self.assertEqual(rows[0]['link']['relative_path'],text)

    def test_custom_lnk_sections_codepage_and_extra_blocks(self):
        from test_execution_cli import shell_link,local_info,tracker
        payload=shell_link(strings={'relative_path':'경로'},unicode=False,encoding='cp949',info=local_info(),pidl=b'\0\0',extra=tracker())
        report=Report();_,rows=jump.parse(custom([dict(kind=2,links=[payload])]),1,report,'cp949')
        self.assertEqual(rows[0]['link']['relative_path'],'경로');self.assertEqual(rows[0]['link']['tracker']['machine_id'],'HOST')

    def test_custom_empty_file_and_empty_category(self):
        for data,count in ((custom([]),0),(custom([dict(kind=2,links=[])]),1)):
            summary,rows,_=self.parse(data);self.assertFalse(rows);self.assertEqual(len(summary['categories']),count)

    def test_custom_unsupported_version_category_footer_trailing_rejected(self):
        original=custom()
        for offset,value in ((0,3),(12,9),(len(original)-4,0)):
            data=bytearray(original);struct.pack_into('<I',data,offset,value)
            with self.assertRaises(AnalysisError):self.parse(bytes(data))
        with self.assertRaises(AnalysisError):self.parse(original+b'junk')
        with self.assertRaises(AnalysisError):self.parse(custom([dict(kind=2,links=[b'invalid shell object'])]))

    def test_custom_declared_count_and_lnk_length_are_bounded(self):
        original=bytearray(custom([dict(kind=2,links=[link()])]))
        struct.pack_into('<I',original,16,2)
        with self.assertRaises(AnalysisError):self.parse(bytes(original))
        bad=bytearray(link());struct.pack_into('<H',bad,76,65535)
        with self.assertRaises(AnalysisError):self.parse(custom([dict(kind=2,links=[bytes(bad)])]))

    def test_input_entry_category_path_link_output_budgets(self):
        for name,data in (('MAX_JUMP_BYTES',automatic()),('MAX_ENTRIES',automatic(records=[dict(number=1,path='x'),dict(number=2,path='y')])),('MAX_CATEGORIES',custom([dict(kind=2),dict(kind=2)])),('MAX_PATH_UNITS',automatic()),('MAX_LINK_BYTES',automatic()),('MAX_OUTPUT_BYTES',automatic())):
            with patch.object(jump,name,1),self.assertRaises(AnalysisError):self.parse(data)

    def test_cli_repeated_inputs_renamed_detection_hash_and_app_hint(self):
        original=automatic();a=self.file('0123456789abcdef.automaticDestinations-ms',original);b=self.file('renamed.bin',custom())
        result=subprocess.run([sys.executable,'-m','plaintrace','--jump-list',str(a),'--jump-list',str(b)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);payload=json.loads(result.stdout);self.assertEqual(payload['format_version'],8)
        self.assertEqual(payload['jump_lists'][0]['app_id_hint'],'0123456789abcdef');self.assertIsNone(payload['jump_lists'][1]['app_id_hint']);self.assertEqual([s['schema_family'] for s in payload['sources']],['jump_automatic','jump_custom'])
        self.assertEqual(payload['sources'][0]['sha256'],hashlib.sha256(original).hexdigest());self.assertEqual(a.read_bytes(),original)

    def test_json_sqlite_schema_lineage_raw_roundtrip(self):
        path=self.file('jump',automatic(3));report=analyze(jump_files=[path]);js=self.folder/'out.json';db=self.folder/'out.sqlite'
        write_report(report,js);write_report(report,db,'sqlite');self.assertEqual(json.loads(js.read_text())['format_version'],8)
        with closing(sqlite3.connect(db)) as conn:
            self.assertEqual(conn.execute('PRAGMA user_version').fetchone()[0],8);self.assertFalse(conn.execute('PRAGMA foreign_key_check').fetchall())
            self.assertEqual(json.loads(conn.execute('SELECT link FROM jump_list_entries').fetchone()[0])['relative_path'],'relative.txt')
            self.assertEqual(conn.execute('SELECT raw_entry_hex FROM jump_list_entries').fetchone()[0],report.jump_list_entries[0]['raw_entry_hex'])
            conn.execute('PRAGMA foreign_keys=ON')
            with self.assertRaises(sqlite3.IntegrityError):conn.execute("UPDATE jump_list_entries SET container_id='absent'")

    def test_mixed_inputs_preserve_previous_ids_and_no_link_duplication(self):
        from test_application_mru_cli import paths
        from test_usb_registry_cli import hive_fixture
        hive=self.file('hive',hive_fixture(paths()));path=self.file('jump',automatic());lnk=self.file('link',link())
        report=analyze(links=[lnk],application_hives=[hive],jump_files=[path])
        self.assertEqual([s['source_kind'] for s in report.sources],['lnk','application_mru','jump_list']);self.assertEqual(len(report.links),1);self.assertEqual(report.jump_list_entries[0]['source_id'],3)

    def test_cli_strict_fatal_atomic_and_output_protection(self):
        path=self.file('jump',cfb({'1':link()}));bad=self.file('bad',b'bad');output=self.folder/'strict.json';absent=self.folder/'absent.json'
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            self.assertEqual(main(['--jump-list',str(path),'--strict','--output',str(output)]),1)
            self.assertEqual(main(['--jump-list',str(path),'--output',str(path)]),2)
            self.assertEqual(main(['--jump-list',str(path),'--jump-list',str(bad),'--output',str(absent)]),2)
        self.assertTrue(output.exists());self.assertFalse(absent.exists())

    def test_only_supplied_input_opened_and_changing_read_rejected(self):
        path=self.file('jump',automatic());real=Path.open;opened=[]
        def watch(obj,*args,**kwargs):opened.append(obj);return real(obj,*args,**kwargs)
        with patch.object(Path,'open',watch):analyze(jump_files=[path])
        self.assertTrue(opened);self.assertEqual(set(opened),{path.resolve()})
        with patch('plaintrace.binary.bounded_hash',side_effect=['a','b']),self.assertRaises(AnalysisError):analyze(jump_files=[path])

    def test_invalid_codepage_is_fatal_not_a_bad_link(self):
        for encoding in ('not-a-codepage','utf-16-le'):
            with self.assertRaises(AnalysisError):jump.parse(automatic(),1,Report(),encoding)

    def test_mutated_containers_fail_with_controlled_errors(self):
        rng=random.Random(809)
        for original in (automatic(),custom()):
            for _ in range(60):
                data=bytearray(original);offset=rng.randrange(len(data));data[offset]^=rng.randrange(1,256)
                try:summary,rows=jump.parse(bytes(data),1,Report());json.dumps([summary,rows],allow_nan=False)
                except AnalysisError:pass
