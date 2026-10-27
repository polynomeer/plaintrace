"""Generated EVTX/BinXML bytes and XML oracles; no real evidence fixtures."""
from contextlib import closing, redirect_stderr, redirect_stdout
from importlib.metadata import PackageNotFoundError, version
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
import xml.etree.ElementTree as ET
import zlib

from plaintrace import evtx
from plaintrace.binary import read_artifact
from plaintrace.cli import main
from plaintrace.evidence import AnalysisError
from plaintrace.execution import analyze
from plaintrace.exports import write_report
from plaintrace.model import Report
from test_browser_cli import chromium
from test_execution_cli import shell_link, pf_fixture

FT = 132223104001234567
UTC = '2020-01-01T00:00:00.123456Z'
RAW_TIME = '2020-01-01T00:00:00.1234567Z'
NS = evtx.EVENT_NAMESPACE
try:
    HAS_DECODER = version('python-evtx') == evtx.DECODER_VERSION
except PackageNotFoundError:
    HAS_DECODER = False


def event_xml(event_id=4624, provider='Microsoft-Windows-Security-Auditing', channel='Security', record_id=7, data=None, time=RAW_TIME, namespace=True):
    root = ET.Element('Event', {'xmlns':NS} if namespace else {})
    system = ET.SubElement(root,'System')
    ET.SubElement(system,'Provider',Name=provider,Guid='{00112233-4455-6677-8899-aabbccddeeff}')
    ET.SubElement(system,'EventID',Qualifiers='0').text = str(event_id)
    for name,text in [('Version','2'),('Level','0'),('Task','12544'),('Opcode','0'),('Keywords','0x8020000000000000'),('EventRecordID',str(record_id)),('Channel',channel),('Computer','HOST')]:
        ET.SubElement(system,name).text = text
    ET.SubElement(system,'TimeCreated',SystemTime=time)
    ET.SubElement(system,'Execution',ProcessID='123',ThreadID='456')
    ET.SubElement(system,'Security',UserID='S-1-5-18')
    ET.SubElement(system,'Correlation',ActivityID='{activity}',RelatedActivityID='{related}')
    payload = ET.SubElement(root,'EventData')
    if data is None:
        data = [('TargetUserName',"한글,O'Brien\n"),('TargetDomainName','DOMAIN'),('TargetUserSid','S-1-5-21-1'),('TargetLogonId','0xffffffffffffffff'),('LogonType','3'),('IpAddress','::1')]
    for name,value in data:
        ET.SubElement(payload,'Data',{} if name is None else {'Name':name}).text = value
    return ET.tostring(root,encoding='unicode')


def binxml(xml, start, substitutions=()):
    # Independently encode literal template nodes and chunk-relative inline names.
    # start is the chunk-relative offset of the template's first XML token.
    root = ET.fromstring(xml)
    def name(value):
        raw=value.encode('utf-16-le')
        return struct.pack('<IHH',0,0,len(raw)//2)+raw+b'\0\0'
    def value(text):
        if text in substitutions:
            return struct.pack('<BHB',13,substitutions.index(text),1)
        raw=text.encode('utf-16-le')
        return b'\x05\x01'+struct.pack('<H',len(raw)//2)+raw
    def element(node, offset):
        tag = node.tag.split('}')[-1]
        attrs = dict(node.attrib)
        if offset == start and node.tag.startswith('{'):
            attrs = {'xmlns':NS,**attrs}
        inline = name(tag)
        header = struct.pack('<BHII',0x41 if attrs else 1,0xffff,0,offset+11)
        result = header+inline
        attribute_data = b''
        cursor = offset+len(result)+(4 if attrs else 0)
        for key,text in attrs.items():
            encoded_name = name(key)
            attribute_data += b'\x06'+struct.pack('<I',cursor+5)+encoded_name+value(text)
            cursor = offset+len(result)+4+len(attribute_data)
        if attrs:result += struct.pack('<I',len(attribute_data))+attribute_data
        result += b'\x02'
        if node.text:result += value(node.text)
        for child in node:
            result += element(child,offset+len(result))
            if child.tail:result += value(child.tail)
        result += b'\x04'
        mutable = bytearray(result);struct.pack_into('<I',mutable,3,len(result)-7)
        return bytes(mutable)
    return element(root,start)+b'\0'


def evtx_fixture(xmls=None, minor=1, flags=0, ids=None, ticks=FT, substitutions=(), shared=False):
    xmls = [event_xml()] if xmls is None else xmls
    chunk = bytearray(65536)
    chunk[:8] = b'ElfChnk\0'
    struct.pack_into('<I',chunk,40,128)
    cursor,last = 512,0
    resident_offset = None
    for ordinal,xml in enumerate(xmls):
        record_id = ids[ordinal] if ids else 7+ordinal
        template_offset = cursor+24+4+10
        template_xml = binxml(xml,template_offset+24,substitutions)
        template = struct.pack('<I',0)+bytes.fromhex('00112233445566778899aabbccddeeff')+struct.pack('<I',len(template_xml))+template_xml
        if shared and resident_offset is not None:
            template_offset,template = resident_offset,b''
        else:
            resident_offset = template_offset
        values = [text.encode('utf-16-le') for text in substitutions]
        declarations = b''.join(struct.pack('<HBB',len(value),1,0) for value in values)
        fragment = b'\x0f\x01\x01\0'+struct.pack('<BBII',12,0,0x33221100,template_offset)+template+struct.pack('<I',len(values))+declarations+b''.join(values)
        size = (24+len(fragment)+4+7)//8*8
        record = struct.pack('<IIQQ',0x2a2a,size,record_id,ticks)+fragment
        record += b'\0'*(size-4-len(record))+struct.pack('<I',size)
        chunk[cursor:cursor+size] = record
        last,cursor = cursor,cursor+size
    if xmls:
        for offset,value in [(8,1),(16,len(xmls)),(24,ids[0] if ids else 7),(32,ids[-1] if ids else 6+len(xmls))]:struct.pack_into('<Q',chunk,offset,value)
    struct.pack_into('<II',chunk,44,last,cursor)
    struct.pack_into('<I',chunk,52,zlib.crc32(chunk[512:cursor]))
    struct.pack_into('<I',chunk,124,zlib.crc32(chunk[:120]+chunk[128:512]))
    header = bytearray(4096);header[:8]=b'ElfFile\0'
    struct.pack_into('<Q',header,24,8+len(xmls))
    struct.pack_into('<IHHHI',header,32,128,minor,3,4096,1)
    struct.pack_into('<I',header,120,flags)
    struct.pack_into('<I',header,124,zlib.crc32(header[:120]))
    return bytes(header+chunk)


def rechecksum(data):
    data=bytearray(data)
    struct.pack_into('<I',data,124,zlib.crc32(data[:120]))
    for start in range(4096,len(data),65536):
        end=struct.unpack_from('<I',data,start+48)[0]
        if 512<=end<=65536:struct.pack_into('<I',data,start+52,zlib.crc32(data[start+512:start+end]))
        struct.pack_into('<I',data,start+124,zlib.crc32(data[start:start+120]+data[start+128:start+512]))
    return bytes(data)


class EvtxTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.folder=Path(self.temporary.name)
    def tearDown(self):self.temporary.cleanup()
    def file(self,name,data):
        path=self.folder/name;path.write_bytes(data);return path
    def parse_xml(self,xml,record_id='7',ticks=FT):
        report=Report()
        row=evtx.parse_event(xml,dict(chunk_index=0,record_offset=4608,container_record_id=record_id,container_filetime_raw=str(ticks)),report,1)
        return row,report

    def test_common_fields_and_logon_details(self):
        row,report=self.parse_xml(event_xml())
        self.assertEqual((row['event_id'],row['provider'],row['channel'],row['process_id'],row['thread_id']),(4624,'Microsoft-Windows-Security-Auditing','Security',123,456))
        self.assertEqual(row['created_at'],UTC);self.assertEqual(row['time_created_raw'],RAW_TIME)
        self.assertEqual(row['container_filetime_raw'],str(FT));self.assertEqual(row['container_time'],UTC)
        self.assertEqual(row['details']['user'],"한글,O'Brien\n");self.assertEqual(row['details']['logon_id'],'0xffffffffffffffff')
        self.assertEqual((row['category'],row['action']),('logon','logon'));self.assertFalse(report.diagnostics)

    def test_security_logoff_variants_and_system_accounts_preserved(self):
        for event_id,action in [(4634,'logoff'),(4647,'user_initiated_logoff')]:
            row,_=self.parse_xml(event_xml(event_id,data=[('TargetDomainName','NT AUTHORITY'),('TargetUserName','SYSTEM')]))
            self.assertEqual(row['action'],action);self.assertEqual(row['details']['user'],'SYSTEM')

    def test_provider_and_channel_qualify_classification(self):
        for provider,channel in [('Other','Security'),('Microsoft-Windows-Security-Auditing','Application')]:
            row,_=self.parse_xml(event_xml(provider=provider,channel=channel))
            self.assertEqual(row['category'],'event');self.assertIsNone(row['action'])
        for event_id,action in [(12,'os_started'),(13,'os_shutdown_started')]:
            row,_=self.parse_xml(event_xml(event_id,'Microsoft-Windows-Kernel-General','System'))
            self.assertEqual((row['category'],row['action']),('power',action))

    def test_driver_frameworks_never_infers_usb_state(self):
        row,_=self.parse_xml(event_xml(2003,'Microsoft-Windows-DriverFrameworks-UserMode','Microsoft-Windows-DriverFrameworks-UserMode/Operational'))
        self.assertEqual(row['category'],'driver_frameworks');self.assertIsNone(row['action']);self.assertFalse(row['details'])

    def test_repeated_unnamed_nested_data_and_user_data_preserved(self):
        xml=event_xml(data=[('TargetUserName','first'),('TargetUserName','second'),(None,'unnamed'),('Empty','')])
        xml=xml.replace('</EventData>','<Binary>00ff</Binary></EventData><UserData><Custom xmlns="urn:custom"><Value>A&amp;B</Value></Custom></UserData>')
        row,report=self.parse_xml(xml)
        self.assertIsNone(row['details']['user']);self.assertEqual(len(row['event_data']),5)
        self.assertEqual(row['event_data'][2]['name'],None);self.assertEqual(row['event_data'][3]['value'],'')
        self.assertIn('urn:custom',row['user_data_xml']);self.assertEqual(row['xml'],xml)
        self.assertIn('evtx_duplicate_data',{d['code'] for d in report.diagnostics})

    def test_unknown_and_namespace_free_events_retained(self):
        row,_=self.parse_xml(event_xml(9999,'Custom','Application',namespace=False))
        self.assertEqual(row['category'],'event');self.assertEqual(row['event_id'],9999)

    def test_invalid_and_missing_time_and_numeric_fields(self):
        xml=event_xml(time='2020-01-01T00:00:00').replace('<Level>0</Level>','<Level>999</Level>').replace('ProcessID="123"','ProcessID="-1"')
        row,report=self.parse_xml(xml);self.assertIsNone(row['created_at']);self.assertIsNone(row['level']);self.assertIsNone(row['process_id'])
        self.assertEqual(row['time_created_raw'],'2020-01-01T00:00:00');self.assertGreaterEqual(len(report.diagnostics),3)
        row,report=self.parse_xml(event_xml().replace('SystemTime="'+RAW_TIME+'"',''))
        self.assertIsNone(row['created_at']);self.assertIn('evtx_missing_time',{d['code'] for d in report.diagnostics})

    def test_time_zone_precision_overflow_and_mismatch(self):
        row,report=self.parse_xml(event_xml(time='2020-01-01T09:00:00.1234567+09:00'))
        self.assertEqual(row['created_at'],UTC);self.assertFalse(report.diagnostics)
        for time in ['0001-01-01T00:00:00+01:00','2020-01-01T00:00:00+24:00','2020-01-01T00:00:00+00:99']:
            row,report=self.parse_xml(event_xml(time=time));self.assertIsNone(row['created_at']);self.assertTrue(report.diagnostics)
        row,report=self.parse_xml(event_xml(time='2021-01-01T00:00:00Z',record_id=8))
        self.assertEqual({d['code'] for d in report.diagnostics},{'evtx_time_mismatch','evtx_record_id_mismatch'})

    def test_fractional_systemtime_one_to_seven_digits_preserves_raw_text(self):
        for length in range(1, 8):
            fraction = '1234567'[:length]
            for clock, zone in [('00', 'Z'), ('09', '+09:00')]:
                raw = f'2020-01-01T{clock}:00:00.{fraction}{zone}'
                with self.subTest(raw=raw):
                    row, report = self.parse_xml(event_xml(time=raw))
                    expected = (fraction + '000000')[:6]
                    self.assertEqual(row['created_at'], f'2020-01-01T00:00:00.{expected}Z')
                    self.assertEqual(row['time_created_raw'], raw)
                    self.assertEqual(row['container_filetime_raw'], str(FT))
                    self.assertNotIn('evtx_invalid_time', {d['code'] for d in report.diagnostics})

    def test_unsigned_record_ids_remain_text_in_sqlite(self):
        row,_=self.parse_xml(event_xml(record_id=2**64-1),record_id=str(2**64-1))
        report=Report();report.events=[row];report.sources=[dict(source_id=1,path='synthetic',browser=None,schema_family='evtx',database_sha256=None,wal_sha256=None,source_kind='evtx',sha256='abc')]
        output=self.folder/'report.sqlite';write_report(report,output,'sqlite')
        with closing(sqlite3.connect(output)) as db:
            self.assertEqual(db.execute('SELECT event_record_id, container_record_id FROM events').fetchone(),(str(2**64-1),str(2**64-1)))
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],15)
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_xml_dtd_entities_roots_and_duplicate_system_rejected(self):
        for xml in ['<!DOCTYPE Event [<!ENTITY x "bad">]>'+event_xml(),'<Wrong/>',event_xml().replace(NS,'urn:foreign'),event_xml().replace('</Event>','<System/></Event>'),event_xml().replace('<Level>0</Level>','<Level>0</Level><Level>1</Level>'),'<Event/>','<Event>']:
            with self.assertRaises(AnalysisError):self.parse_xml(xml)

    def test_xml_size_depth_and_node_limits(self):
        with self.assertRaises(AnalysisError):self.parse_xml('x'*(evtx.MAX_XML_BYTES+1))
        xml=event_xml().replace('</Event>','<UserData>'+'<x>'*65+'v'+'</x>'*65+'</UserData></Event>')
        with self.assertRaises(AnalysisError):self.parse_xml(xml)
        with patch.object(evtx,'MAX_XML_BYTES',10):
            with self.assertRaises(AnalysisError):self.parse_xml(event_xml())

    def test_container_versions_empty_and_dirty(self):
        for minor in (1,2):
            report=Report();records=evtx.envelopes(evtx_fixture(minor=minor),report,1)
            self.assertEqual(len(records),1);self.assertEqual(records[0]['record_offset'],4608);self.assertFalse(report.diagnostics)
        self.assertEqual(evtx.envelopes(evtx_fixture([]),Report(),1),[])
        report=Report();evtx.envelopes(evtx_fixture(flags=1),report,1)
        self.assertEqual(report.diagnostics[0]['code'],'evtx_dirty')

    def test_container_header_checksums_count_version_and_alignment(self):
        good=evtx_fixture()
        variants=[b'',good[:-1]]
        for offset,value,size in [(0,0,1),(32,127,4),(36,9,2),(40,512,2),(42,2,4),(120,4,4)]:
            data=bytearray(good);data[offset:offset+size]=value.to_bytes(size,'little');variants.append(rechecksum(data))
        data=bytearray(good);data[124]^=1;variants.append(bytes(data))
        for data in variants:
            with self.assertRaises(AnalysisError):evtx.envelopes(data,Report(),1)

    def test_chunk_and_record_envelope_corruption_rejected(self):
        good=evtx_fixture()
        for offset,value,size in [(4096,0,1),(4136,127,4),(4144,511,4),(4140,513,4),(4608,0,4),(4612,0,4),(4612,33,4),(4612,65536,4)]:
            data=bytearray(good);data[offset:offset+size]=value.to_bytes(size,'little')
            with self.assertRaises(AnalysisError):evtx.envelopes(rechecksum(data),Report(),1)
        end=struct.unpack_from('<I',good,4144)[0]
        data=bytearray(good);struct.pack_into('<I',data,4096+end-4,32)
        with self.assertRaises(AnalysisError):evtx.envelopes(rechecksum(data),Report(),1)
        for offset in (4096+124,4096+52,4700):
            data=bytearray(good);data[offset]^=1
            with self.assertRaises(AnalysisError):evtx.envelopes(data,Report(),1)

    def test_inactive_chunks_diagnosed_without_carving(self):
        data=evtx_fixture()+bytes(65536);report=Report()
        self.assertEqual(len(evtx.envelopes(data,report,1)),1)
        self.assertEqual(report.diagnostics[0]['code'],'evtx_inactive_chunks')

    def test_record_and_input_limits_and_changing_file(self):
        with patch.object(evtx,'MAX_RECORDS',0):
            with self.assertRaises(AnalysisError):evtx.envelopes(evtx_fixture(),Report(),1)
        with patch.object(evtx,'MAX_EVTX_BYTES',10):
            with self.assertRaises(AnalysisError):evtx.envelopes(evtx_fixture(),Report(),1)
        path=self.file('a.evtx',evtx_fixture())
        with patch('plaintrace.binary.bounded_hash',side_effect=['before','after']):
            with self.assertRaises(AnalysisError):read_artifact(path,evtx.MAX_EVTX_BYTES)
        with self.assertRaises(AnalysisError):read_artifact(path,0)

    def test_missing_or_wrong_dependency_is_actionable(self):
        for effect in [PackageNotFoundError('python-evtx'),'0.9.0']:
            with patch.object(evtx,'version',side_effect=effect if isinstance(effect,Exception) else None,return_value=effect):
                with self.assertRaisesRegex(AnalysisError,'python-evtx'):evtx.decode_snapshot(evtx_fixture(),[])

    def test_worker_timeout_and_exit_failure_abort(self):
        with patch.object(evtx,'version',return_value='0.8.1'),patch.object(evtx.subprocess,'run',side_effect=subprocess.TimeoutExpired('worker',60)):
            with self.assertRaisesRegex(AnalysisError,'timeout'):evtx.decode_snapshot(evtx_fixture(),[])
        with patch.object(evtx,'version',return_value='0.8.1'),patch.object(evtx.subprocess,'run',return_value=subprocess.CompletedProcess([],2)):
            with self.assertRaisesRegex(AnalysisError,'worker terminated'):evtx.decode_snapshot(evtx_fixture(),[])

    def test_decoder_lineage_counts_and_output_caps(self):
        records=evtx.envelopes(evtx_fixture(),Report(),1)
        for payload in [b'',b'bad\n',b'{"record_offset":0,"xml":"<Event/>"}\n',b'{"record_offset":4608,"xml":null}\n',json.dumps(dict(record_offset=4608,xml=event_xml())).encode()+b'\nextra']:
            def run(command,**kwargs):
                Path(command[-2]).write_bytes(payload);return subprocess.CompletedProcess([],0)
            with patch.object(evtx,'version',return_value='0.8.1'),patch.object(evtx.subprocess,'run',side_effect=run):
                with self.assertRaises(AnalysisError):evtx.decode_snapshot(evtx_fixture(),records)
        with patch.object(evtx,'decode_snapshot',return_value=[]):
            with self.assertRaises(AnalysisError):evtx.parse(evtx_fixture(),1,Report())

    def test_mutated_and_truncated_envelopes_only_raise_contract_errors(self):
        good=evtx_fixture();rng=random.Random(2017)
        for size in [0,7,127,128,4095,4096,4607,len(good)-1]:
            with self.assertRaises(AnalysisError):evtx.envelopes(good[:size],Report(),1)
        for _ in range(100):
            data=bytearray(good);offset=rng.randrange(len(data));data[offset]^=rng.randrange(1,256)
            try:evtx.envelopes(data,Report(),1)
            except AnalysisError:pass

    @unittest.skipUnless(HAS_DECODER,'optional python-evtx==0.8.1 not installed')
    def test_real_decoder_synthetic_binxml_end_to_end(self):
        xmls=[event_xml(),event_xml(4634,record_id=8)]
        path=self.file('Security.evtx',evtx_fixture(xmls));before=path.read_bytes()
        report=analyze(event_logs=[path])
        self.assertEqual([r['action'] for r in report.events],['logon','logoff'])
        self.assertEqual(report.events[0]['details']['user'],"한글,O'Brien\n")
        self.assertEqual(report.events[0]['created_at'],UTC);self.assertFalse(report.diagnostics)
        self.assertEqual(path.read_bytes(),before);self.assertEqual(report.sources[0]['sha256'],hashlib.sha256(before).hexdigest())

    @unittest.skipUnless(HAS_DECODER,'optional python-evtx==0.8.1 not installed')
    def test_cli_subprocess_mixed_inputs_json_sqlite_and_no_overwrite(self):
        browser=self.folder/'History'
        with closing(sqlite3.connect(browser)) as db:chromium(db)
        link=self.file('a.lnk',shell_link({'relative_path':'APP.EXE'}));pf=self.file('a.pf',pf_fixture());log=self.file('a.evtx',evtx_fixture())
        before={p:p.read_bytes() for p in (browser,link,pf,log)}
        args=[sys.executable,'-m','plaintrace','--input',str(browser),'--lnk',str(link),'--prefetch',str(pf),'--evtx',str(log)]
        result=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);payload=json.loads(result.stdout)
        self.assertEqual(payload['format_version'],15);self.assertEqual(payload['events'][0]['source_id'],4)
        self.assertEqual([s['source_kind'] for s in payload['sources']],['browser','lnk','prefetch','evtx'])
        output=self.folder/'events.sqlite'
        result=subprocess.run(args+['--format','sqlite','--output',str(output)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        with closing(sqlite3.connect(output)) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],15)
            self.assertEqual(json.loads(db.execute('SELECT details FROM events').fetchone()[0])['user'],"한글,O'Brien\n")
        old=output.read_bytes();self.assertEqual(subprocess.run(args+['--output',str(output)],capture_output=True).returncode,2)
        self.assertEqual(output.read_bytes(),old);self.assertTrue(all(p.read_bytes()==data for p,data in before.items()))

    @unittest.skipUnless(HAS_DECODER,'optional python-evtx==0.8.1 not installed')
    def test_multiple_logs_duplicate_ids_and_dirty_strict(self):
        first=self.file('a.evtx',evtx_fixture());second=self.file('b.evtx',evtx_fixture(flags=1))
        stdout,stderr=io.StringIO(),io.StringIO()
        with redirect_stdout(stdout),redirect_stderr(stderr):code=main(['--evtx',str(first),'--evtx',str(second),'--strict'])
        self.assertEqual(code,1);payload=json.loads(stdout.getvalue())
        self.assertEqual([r['source_id'] for r in payload['events']],[1,2]);self.assertIn('evtx_dirty',stderr.getvalue())

    @unittest.skipUnless(HAS_DECODER,'optional python-evtx==0.8.1 not installed')
    def test_empty_evtx_and_corrupt_binxml_fatal_atomicity(self):
        empty=self.file('empty.evtx',evtx_fixture([]));self.assertFalse(analyze(event_logs=[empty]).events)
        good=evtx_fixture();bad=bytearray(good);bad[4608+24+4]=0xff
        malformed=self.file('bad.evtx',rechecksum(bad));output=self.folder/'out.json'
        with redirect_stderr(io.StringIO()):code=main(['--evtx',str(empty),'--evtx',str(malformed),'--output',str(output)])
        self.assertEqual(code,2);self.assertFalse(output.exists());self.assertFalse(list(self.folder.glob('.plaintrace-*')))

    @unittest.skipUnless(HAS_DECODER,'optional python-evtx==0.8.1 not installed')
    def test_review_shared_template_and_unicode_substitutions(self):
        xml=event_xml(data=[('TargetUserName','한글 치환')])
        data=evtx_fixture([xml,xml],substitutions=('한글 치환',),shared=True,ids=[7,7])
        report=Report();rows=evtx.parse(data,1,report)
        self.assertEqual([r['details']['user'] for r in rows],['한글 치환','한글 치환'])
        self.assertNotEqual(rows[0]['record_id'],rows[1]['record_id'])
        self.assertEqual(report.diagnostics[0]['code'],'evtx_duplicate_record_id')

    @unittest.skipUnless(HAS_DECODER,'optional python-evtx==0.8.1 not installed')
    def test_review_multiple_chunks_and_container_32(self):
        data=bytearray(evtx_fixture(minor=2));data+=evtx_fixture()[4096:]
        struct.pack_into('<I',data,42,2);struct.pack_into('<Q',data,16,1)
        report=Report();rows=evtx.parse(rechecksum(data),1,report)
        self.assertEqual([r['chunk_index'] for r in rows],[0,1]);self.assertEqual(rows[1]['record_offset'],70144)
        self.assertEqual([r['details']['user'] for r in rows],["한글,O'Brien\n"]*2)

    def test_review_non_data_nodes_cannot_supply_normalized_identity(self):
        xml=event_xml(data=[]).replace('<EventData />','<EventData><Binary Name="TargetUserName">forged</Binary><Data xmlns="urn:foreign" Name="TargetUserName">foreign</Data></EventData>')
        row,_=self.parse_xml(xml)
        self.assertIsNone(row['details']['user']);self.assertEqual([d['name'] for d in row['event_data']],[None,None])

    def test_review_missing_ids_and_overflow_filetime(self):
        xml=event_xml().replace('<EventRecordID>7</EventRecordID>','').replace('<EventID Qualifiers="0">4624</EventID>','')
        row,report=self.parse_xml(xml,ticks=2**64-1)
        self.assertIsNone(row['event_id']);self.assertIsNone(row['event_record_id']);self.assertIsNone(row['container_time'])
        self.assertEqual(row['container_filetime_raw'],str(2**64-1))
        self.assertEqual({d['code'] for d in report.diagnostics},{'evtx_missing_identity','invalid_filetime'})

    def test_review_worker_and_parent_decoded_size_limits(self):
        records=evtx.envelopes(evtx_fixture(),Report(),1)
        payload=json.dumps(dict(record_offset=4608,xml=event_xml())).encode()+b'\n'
        def run(command,**kwargs):
            Path(command[-2]).write_bytes(payload);return subprocess.CompletedProcess([],0)
        with patch.object(evtx,'version',return_value='0.8.1'),patch.object(evtx.subprocess,'run',side_effect=run),patch.object(evtx,'MAX_DECODED_BYTES',10):
            with self.assertRaisesRegex(AnalysisError,'32 MiB'):evtx.decode_snapshot(evtx_fixture(),records)
        with patch.object(evtx,'version',return_value='0.8.1'),patch.object(evtx.subprocess,'run',side_effect=run),patch.object(evtx,'MAX_XML_BYTES',10):
            with self.assertRaisesRegex(AnalysisError,'1 MiB'):evtx.decode_snapshot(evtx_fixture(),records)
        if HAS_DECODER:
            from plaintrace import evtx_worker
            source=self.file('bounded.evtx',evtx_fixture());output=self.folder/'worker.jsonl';failure=self.folder/'error.txt'
            with patch.object(evtx_worker,'MAX_DECODED_BYTES',10):code=evtx_worker.main([source,output,failure])
            self.assertEqual(code,2);self.assertEqual(output.stat().st_size,0)
            output.unlink()
            with patch.object(evtx_worker,'MAX_XML_BYTES',10):code=evtx_worker.main([source,output,failure])
            self.assertEqual(code,2);self.assertEqual(output.stat().st_size,0)

    def test_review_xml_node_limit_and_integer_lexical_bounds(self):
        xml=event_xml().replace('</Event>','<UserData>'+'<x/>'*10_001+'</UserData></Event>')
        with self.assertRaises(AnalysisError):self.parse_xml(xml)
        for value in ['-1','1.5','9'*100,'18446744073709551616']:
            xml=event_xml().replace('<EventRecordID>7</EventRecordID>','<EventRecordID>'+value+'</EventRecordID>')
            row,report=self.parse_xml(xml);self.assertIsNone(row['event_record_id']);self.assertEqual(report.diagnostics[0]['code'],'evtx_invalid_number')

    def test_review_missing_dependency_cli_publishes_nothing(self):
        path=self.file('missing.evtx',evtx_fixture());output=self.folder/'out.json';out,err=io.StringIO(),io.StringIO()
        with patch.object(evtx,'version',side_effect=PackageNotFoundError('python-evtx')),redirect_stdout(out),redirect_stderr(err):
            code=main(['--evtx',str(path),'--output',str(output)])
        self.assertEqual(code,2);self.assertFalse(output.exists());self.assertFalse(out.getvalue());self.assertIn('pip install',err.getvalue())

    @unittest.skipUnless(HAS_DECODER,'optional python-evtx==0.8.1 not installed')
    def test_review_binxml_invalid_chunk_reference_is_fatal(self):
        data=bytearray(evtx_fixture());struct.pack_into('<I',data,4608+24+4+6,65535)
        path=self.file('offset.evtx',rechecksum(data))
        with self.assertRaisesRegex(AnalysisError,'BinXML'):analyze(event_logs=[path])
