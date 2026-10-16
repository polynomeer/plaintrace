"""Independent synthetic Shell Link/SCCA/XPRESS fixtures; no real evidence."""
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import random
import sqlite3
import struct
import tempfile
import unittest
import uuid
from unittest.mock import patch

from plaintrace.binary import MAX_ARTIFACT_BYTES
from plaintrace.cli import main
from plaintrace.evidence import AnalysisError
from plaintrace.execution import analyze
from plaintrace.exports import write_report
from plaintrace.model import Report
from plaintrace import lnk, prefetch
from plaintrace.xpress import decompress
from test_browser_cli import chromium

FT = 132223104001234567  # UTC 2020-01-01T00:00:00.1234567, independently specified.
UTC = "2020-01-01T00:00:00.123456Z"


def u32(buffer,offset,value): struct.pack_into('<I',buffer,offset,value)
def u64(buffer,offset,value): struct.pack_into('<Q',buffer,offset,value)


def shell_link(strings=None, unicode=True, info=b'', pidl=None, extra=b'', times=(FT,FT+10000000,FT+20000000),encoding='cp1252'):
    strings = strings or {}
    flags = (128 if unicode else 0) | (2 if info else 0) | (1 if pidl is not None else 0)
    header = bytearray(76)
    u32(header,0,76);header[4:20]=uuid.UUID('00021401-0000-0000-c000-000000000046').bytes_le
    u32(header,24,32);u32(header,52,123)
    for offset,time in zip((28,36,44),times):u64(header,offset,time)
    payload = b''
    if pidl is not None:payload+=struct.pack('<H',len(pidl))+pidl
    payload+=info
    for mask,name in [(4,'name'),(8,'relative_path'),(16,'working_directory'),(32,'arguments'),(64,'icon_location')]:
        if name in strings:
            flags |= mask
            encoded=strings[name].encode('utf-16-le' if unicode else encoding)
            payload+=struct.pack('<H',len(encoded)//2 if unicode else len(encoded))+encoded
    u32(header,20,flags)
    return bytes(header)+payload+extra+b'\0'*4


def local_info(unicode=False):
    header = bytearray(36 if unicode else 28)
    u32(header,4,len(header));u32(header,8,1)
    volume=bytearray(16);u32(volume,4,3);u32(volume,8,0xAABBCCDD);u32(volume,12,16)
    volume+=b'LABEL\0';u32(volume,0,len(volume))
    u32(header,12,len(header))
    base=b'C:\\Tools\\APP.EXE\0';suffix=b'APP.EXE\0'
    u32(header,16,len(header)+len(volume));u32(header,24,len(header)+len(volume)+len(base))
    payload=volume+base+suffix
    if unicode:
        u32(header,28,len(header)+len(payload));payload+='C:\\한글\\APP.EXE\0'.encode('utf-16-le')
        u32(header,32,len(header)+len(payload));payload+='APP.EXE\0'.encode('utf-16-le')
    result=header+payload;u32(result,0,len(result));return bytes(result)


def network_info():
    header=bytearray(28);u32(header,4,28);u32(header,8,2)
    network=bytearray(20);u32(network,8,20)
    network+=b'\\\\server\\share\0';u32(network,0,len(network))
    u32(header,20,28);u32(header,24,28+len(network))
    result=header+network+b'dir\\APP.EXE\0';u32(result,0,len(result));return bytes(result)


def tracker():
    data=bytearray(96);u32(data,0,96);u32(data,4,0xA0000003);u32(data,8,88)
    data[16:32]=b'HOST\0'+b'\0'*11
    for offset in (32,48,64,80):data[offset:offset+16]=uuid.UUID('00112233-4455-1677-8899-aabbccddeeff').bytes_le
    return bytes(data)


def environment():
    data=bytearray(788);u32(data,0,788);u32(data,4,0xA0000001)
    data[8:8+len(b'%TEMP%\\APP.EXE\0')]=b'%TEMP%\\APP.EXE\0'
    text='%TEMP%\\한글.EXE\0'.encode('utf-16-le');data[268:268+len(text)]=text
    return bytes(data)


def pf_fixture(version=23,variant=1,volumes=True,references=None):
    size={17:152,23:240,26:304,30:304 if variant==1 else 296,31:296}[version]
    data=bytearray(size);u32(data,0,version);data[4:8]=b'SCCA'
    exe='APP.EXE\0'.encode('utf-16-le');data[16:16+len(exe)]=exe;u32(data,76,0x1234ABCD)
    u32(data,84,size)
    refs = references if references is not None else ['\\DEVICE\\HARDDISKVOLUME7\\APP.EXE','\\DEVICE\\HARDDISKVOLUME7\\DLL.DLL']
    string_data=('\0'.join(refs)+'\0').encode('utf-16-le') if refs else b''
    u32(data,100,len(data));u32(data,104,len(string_data));data+=string_data
    if volumes:
        entry_size={17:40,23:104,26:104,30:96,31:96}[version]
        volume=bytearray(entry_size);path='\\DEVICE\\HARDDISKVOLUME7'.encode('utf-16-le')
        u32(volume,0,entry_size);u32(volume,4,len(path)//2);u64(volume,8,FT);u32(volume,16,0xABCDEF12)
        volume+=path;u32(data,108,len(data));u32(data,112,1);u32(data,116,len(volume));data+=volume
    time_offset=120 if version==17 else 128
    count_offset={17:144,23:152,26:208,30:208 if variant==1 else 200,31:200}[version]
    u64(data,time_offset,FT);u32(data,count_offset,7);u32(data,12,len(data))
    return bytes(data)


def huffman_symbols(symbols):
    # Complete 512-symbol, fixed 9-bit canonical table. Independent fixture encoder.
    bits=''.join(f'{symbol:09b}' for symbol in symbols)
    bits+='0'*((-len(bits))%16)
    words=b''.join(struct.pack('<H',int(bits[i:i+16],2)) for i in range(0,len(bits),16))
    return b'\x99'*256+words+b'\0\0'


def mam_fixture(payload):
    encoded=b''.join(huffman_symbols(payload[i:i+65536]) for i in range(0,len(payload),65536))
    return b'MAM\x04'+struct.pack('<I',len(payload))+encoded


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='plaintrace-execution-');self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)

    def file(self,name,data):
        path=self.folder/name;path.write_bytes(data);return path

    def test_lnk_unicode_strings_and_correct_time_order(self):
        path=self.file('link.lnk',shell_link({'name':'한글','relative_path':'APP.EXE','working_directory':'C:\\Tools','arguments':'--value "한글"'}))
        record=analyze(links=[path]).links[0]
        self.assertEqual(record['created_at'],UTC)
        self.assertEqual(record['accessed_at'],'2020-01-01T00:00:01.123456Z')
        self.assertEqual(record['written_at'],'2020-01-01T00:00:02.123456Z')
        self.assertEqual(record['filetimes_raw']['created'],str(FT))
        self.assertEqual(record['arguments'],'--value "한글"')
        self.assertEqual(record['target_candidates'][0]['path'],'C:\\Tools\\APP.EXE')

    def test_lnk_ansi_codepage(self):
        path=self.file('ansi.lnk',shell_link({'relative_path':'한글.EXE'},unicode=False,encoding='cp949'))
        self.assertEqual(analyze(links=[path],codepage='cp949').links[0]['relative_path'],'한글.EXE')
        with self.assertRaises(AnalysisError):analyze(links=[path],codepage='utf-16')

    def test_lnk_local_volume_no_duplicate_suffix(self):
        record=lnk.parse(shell_link(info=local_info()),1,Report())
        self.assertEqual(record['volume'],{'drive_type':3,'serial':'AABBCCDD','label':'LABEL'})
        self.assertEqual(record['target_candidates'][0]['path'],'C:\\Tools\\APP.EXE')

    def test_lnk_unicode_link_info_preferred(self):
        record=lnk.parse(shell_link(info=local_info(True)),1,Report())
        self.assertEqual(record['local_base_path'],'C:\\한글\\APP.EXE')

    def test_lnk_network_path(self):
        record=lnk.parse(shell_link(info=network_info()),1,Report())
        self.assertEqual(record['target_candidates'][0]['path'],'\\\\server\\share\\dir\\APP.EXE')

    def test_lnk_tracker_environment_and_opaque_items(self):
        report=Report()
        record=lnk.parse(shell_link(pidl=b'\x04\x00XX\0\0',extra=tracker()+environment()),1,report)
        self.assertEqual(record['tracker']['machine_id'],'HOST')
        self.assertEqual(record['tracker']['droid_file'],'00112233-4455-1677-8899-aabbccddeeff')
        self.assertEqual(record['environment_target'],'%TEMP%\\한글.EXE')
        self.assertEqual(record['id_list_hex'],'040058580000')
        self.assertEqual(report.diagnostics[0]['code'],'opaque_id_list')

    def test_lnk_unknown_extra_and_unresolved_are_diagnosed(self):
        report=Report();record=lnk.parse(shell_link(extra=struct.pack('<II',8,0xDEADBEEF)),1,report)
        self.assertEqual({d['code'] for d in report.diagnostics},{'opaque_extra_block','lnk_target_unresolved'})
        self.assertEqual(record['extra_blocks'][0]['signature'],'DEADBEEF')

    def test_lnk_invalid_sizes_offsets_and_missing_terminal(self):
        data=bytearray(shell_link(info=local_info()));u32(data,76+16,999999)
        for value in [bytes(data),shell_link()[:-4],shell_link(pidl=b'\x01\0'),b'no link',shell_link(info=b'\x04\0\0\0')]:
            with self.assertRaises(AnalysisError):lnk.parse(value,1,Report())

    def test_every_lnk_truncated_prefix_fails(self):
        data=shell_link({'relative_path':'APP.EXE'},info=local_info(),extra=tracker())
        for end in range(len(data)):
            with self.subTest(end=end),self.assertRaises(AnalysisError):lnk.parse(data[:end],1,Report())

    def test_lnk_invalid_utf16_and_filetime_preserved(self):
        data=bytearray(shell_link({'name':'X'},times=(2**64-1,0,0)));data[78:80]=b'\x00\xd8'
        report=Report();record=lnk.parse(bytes(data),1,report)
        self.assertIsNone(record['created_at']);self.assertEqual(record['name'],'\\x00\\xd8')
        self.assertIn('invalid_artifact_text',{d['code'] for d in report.diagnostics})

    def test_prefetch_versions_and_v30_variants(self):
        for version,variant in [(17,1),(23,1),(26,1),(30,1),(30,2),(31,2)]:
            with self.subTest(version=version,variant=variant):
                report=Report();record=prefetch.parse(pf_fixture(version,variant),1,report)
                self.assertEqual(record['run_count'],7);self.assertEqual(record['last_run_times'][0],UTC)
                self.assertEqual(record['prefetch_hash'],'1234ABCD');self.assertEqual(record['volumes'][0]['serial'],'ABCDEF12')
                self.assertEqual(len(record['last_run_times']),1 if version in (17,23) else 8)
                self.assertEqual(record['executable_path_candidates'],['\\DEVICE\\HARDDISKVOLUME7\\APP.EXE'])
                self.assertFalse(report.diagnostics)

    def test_prefetch_version_and_size_rejection(self):
        for offset,value in [(0,999),(12,1),(84,100)]:
            data=bytearray(pf_fixture());u32(data,offset,value)
            with self.assertRaises(AnalysisError):prefetch.parse(bytes(data),1,Report())

    def test_prefetch_section_bounds_and_unterminated_strings(self):
        for offset,value in [(100,999999),(104,3),(112,999999),(88,999999)]:
            data=bytearray(pf_fixture());u32(data,offset,value)
            with self.assertRaises(AnalysisError):prefetch.parse(bytes(data),1,Report())
        data=bytearray(pf_fixture());offset=struct.unpack_from('<I',data,100)[0];size=struct.unpack_from('<I',data,104)[0]
        data[offset+size-2:offset+size]=b'A\0'
        with self.assertRaises(AnalysisError):prefetch.parse(bytes(data),1,Report())

    def test_every_prefetch_truncated_prefix_fails(self):
        data=pf_fixture()
        for end in range(len(data)):
            with self.subTest(end=end),self.assertRaises(AnalysisError):prefetch.parse(data[:end],1,Report())

    def test_mam_prefetch_portable_decompression(self):
        data=pf_fixture(30,2)
        record=prefetch.parse(mam_fixture(data),1,Report())
        self.assertTrue(record['compressed']);self.assertEqual(record['run_count'],7)
        self.assertEqual(record['last_run_times'][0],UTC)

    def test_xpress_overlapping_match_and_extended_length(self):
        self.assertEqual(decompress(huffman_symbols([65,258]),6),b'A'*6)
        self.assertEqual(decompress(huffman_symbols([65,271])+b'\x03',22),b'A'*22)
        self.assertEqual(decompress(huffman_symbols([65,271])+b'\xff\x16\x00',26),b'A'*26)

    def test_xpress_multiple_blocks(self):
        data=bytes(range(256))*300
        encoded=b''.join(huffman_symbols(data[i:i+65536]) for i in range(0,len(data),65536))
        self.assertEqual(decompress(encoded,len(data)),data)

    def test_xpress_invalid_table_match_and_truncation(self):
        for data,size in [(b'\0'*260,1),(b'\x11'*260,1),(huffman_symbols([256]),3),(huffman_symbols([65,258]),5),(b'\x99'*256+b'\0',1)]:
            with self.assertRaises(AnalysisError):decompress(data,size)

    def test_mam_checksum_and_size_limits_fail(self):
        for data in [b'MAM\x84'+b'\0'*10,b'MAM\x04'+struct.pack('<I',MAX_ARTIFACT_BYTES+1),b'MAM\x04'+struct.pack('<I',2)]:
            with self.assertRaises(AnalysisError):prefetch.parse(data,1,Report())

    def test_mixed_browser_execution_json_sqlite_and_source_hashes(self):
        browser=self.folder/'History';db=sqlite3.connect(browser)
        try:chromium(db)
        finally:db.close()
        link=self.file('A.LNK',shell_link({'relative_path':'APP.EXE'}));pf=self.file('A.pf',pf_fixture())
        before={p:p.read_bytes() for p in (browser,link,pf)}
        report=analyze([browser],[link],[pf])
        self.assertEqual([s['source_kind'] for s in report.sources],['browser','lnk','prefetch'])
        self.assertEqual(report.links[0]['source_id'],2);self.assertEqual(report.prefetch[0]['source_id'],3)
        self.assertEqual(report.sources[1]['sha256'],hashlib.sha256(before[link]).hexdigest())
        for format in ('json','sqlite'):
            output=self.folder/('report.'+format);write_report(report,output,format)
            if format=='json':self.assertEqual(json.loads(output.read_text())['format_version'],10)
            else:
                db=sqlite3.connect(output)
                try:
                    self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],10)
                    self.assertEqual(json.loads(db.execute('SELECT last_run_times FROM prefetch').fetchone()[0])[0],UTC)
                    self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
                finally:db.close()
        self.assertTrue(all(p.read_bytes()==value for p,value in before.items()))

    def test_execution_cli_strict_and_fatal_atomicity(self):
        link=self.file('test.lnk',shell_link());out=io.StringIO();err=io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):code=main(['--lnk',str(link),'--strict'])
        self.assertEqual(code,1);self.assertEqual(len(json.loads(out.getvalue())['links']),1)
        target=self.folder/'output.json'
        with redirect_stderr(io.StringIO()):code=main(['--lnk',str(link),'--prefetch',str(self.file('bad.pf',b'bad')),'--output',str(target)])
        self.assertEqual(code,2);self.assertFalse(target.exists())

    def test_execution_file_size_limit_and_changing_input(self):
        link=self.file('large.lnk',b'X'*100)
        with patch('plaintrace.binary.MAX_ARTIFACT_BYTES',50):
            with self.assertRaises(AnalysisError):analyze(links=[link])
        with patch('plaintrace.binary.bounded_hash',side_effect=['before','after']):
            with self.assertRaises(AnalysisError):analyze(links=[link])

    def test_mutated_binary_inputs_never_escape_contract_errors(self):
        rng=random.Random(2017)
        for parser,seed in [(lnk.parse,shell_link({'relative_path':'APP.EXE'},info=local_info())),(prefetch.parse,pf_fixture())]:
            for _ in range(100):
                data=bytearray(seed);data[rng.randrange(len(data))]=rng.randrange(256)
                try:parser(bytes(data),1,Report())
                except AnalysisError:pass

    def test_review_xpress_direct_api_limits(self):
        for value in (0,-1,MAX_ARTIFACT_BYTES+1,True):
            with self.assertRaises(AnalysisError):decompress(b'',value)

    def test_review_unicode_volume_and_network(self):
        volume=bytearray(20);u32(volume,4,3);u32(volume,8,42);u32(volume,12,20);u32(volume,16,20)
        volume+='한글\0'.encode('utf-16-le');u32(volume,0,len(volume))
        old=local_info();new=bytearray(old[:28]);payload=volume+b'C:\\Tools\\APP.EXE\0'+b'APP.EXE\0'
        u32(new,12,28);u32(new,16,28+len(volume));u32(new,24,28+len(volume)+len(b'C:\\Tools\\APP.EXE\0'))
        new+=payload;u32(new,0,len(new))
        self.assertEqual(lnk.parse(shell_link(info=bytes(new)),1,Report())['volume']['label'],'한글')
        network=bytearray(28);u32(network,8,28);u32(network,20,29)
        network+=b'X'+('\\\\서버\\공유\0').encode('utf-16-le');u32(network,0,len(network))
        info=bytearray(28);u32(info,4,28);u32(info,8,2);u32(info,20,28);u32(info,24,28+len(network))
        info+=network+b'APP.EXE\0';u32(info,0,len(info))
        self.assertEqual(lnk.parse(shell_link(info=bytes(info)),1,Report())['network_share'],'\\\\서버\\공유')

    def test_review_prefetch_volume_bounds_and_overflow_time(self):
        data=bytearray(pf_fixture());volume_offset=struct.unpack_from('<I',data,108)[0]
        u32(data,volume_offset,1)
        with self.assertRaises(AnalysisError):prefetch.parse(bytes(data),1,Report())
        data=bytearray(pf_fixture());u64(data,128,2**64-1)
        report=Report();record=prefetch.parse(bytes(data),1,report)
        self.assertIsNone(record['last_run_times'][0]);self.assertEqual(record['last_run_times_raw'][0],str(2**64-1))

    def test_review_terminal_trailing_bytes_and_source_collision(self):
        report=Report();lnk.parse(shell_link()+b'trailing',1,report)
        self.assertIn('lnk_trailing_bytes',{d['code'] for d in report.diagnostics})
        path=self.file('input.lnk',shell_link({'relative_path':'APP.EXE'}))
        report=analyze(links=[path])
        with self.assertRaises(AnalysisError):write_report(report,path)
        self.assertEqual(path.read_bytes(),shell_link({'relative_path':'APP.EXE'}))

    def test_review_prefetch_overlapping_sections_are_rejected(self):
        data=bytearray(pf_fixture());u32(data,88,1)
        with self.assertRaisesRegex(AnalysisError,'sections overlap'):
            prefetch.parse(bytes(data),1,Report())

    def test_review_lnk_suffix_with_leading_separator(self):
        self.assertEqual(lnk.combine('C:\\Tools\\APP.EXE','\\APP.EXE'),'C:\\Tools\\APP.EXE')

    def test_review_empty_target_candidates_are_unresolved(self):
        info=bytearray(local_info())
        for offset in (16,24):
            start=struct.unpack_from('<I',info,offset)[0];info[start]=0
        report=Report();record=lnk.parse(shell_link(info=bytes(info)),1,report)
        self.assertFalse(record['target_candidates'])
        self.assertIn('lnk_target_unresolved',{d['code'] for d in report.diagnostics})


if __name__=='__main__':unittest.main()
