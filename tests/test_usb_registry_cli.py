"""Independent generated REGF cells and USB oracles; no acquired evidence."""
from contextlib import closing,redirect_stderr,redirect_stdout
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
from plaintrace.registry_hive import Hive
from plaintrace import registry_hive,usb_registry
from plaintrace.model import Report
from plaintrace.execution import analyze
from plaintrace.exports import write_report
from plaintrace.cli import main
from plaintrace.evidence import AnalysisError

FT=132223104001234567
UTC='2020-01-01T00:00:00.123456Z'
DEVICE='Disk&Ven_ACME&Prod_Flash&Rev_1.00'
INSTANCE='SERIAL&0'
BASE='ControlSet002\\Enum\\USBSTOR\\'+DEVICE+'\\'+INSTANCE
GUID=usb_registry.PROPERTY_GUID


def value(name,kind,data,inline=False):return (name,kind,data,inline)
def text(name,data):return value(name,1,(data+'\0').encode('utf-16-le'))


def hive_fixture(paths=None,index_kind=b'li',minor=5):
    paths=paths or {}
    root={'name':'ROOT','children':{},'values':[]}
    for path,values in paths.items():
        node=root
        for name in path.split('\\') if path else []:node=node['children'].setdefault(name,{'name':name,'children':{},'values':[]})
        node['values']=values
    bin_data=bytearray(128*1024);bin_data[:4]=b'hbin';struct.pack_into('<II',bin_data,4,0,len(bin_data));cursor=32
    def cell(payload):
        nonlocal cursor
        size=(len(payload)+4+7)//8*8;offset=cursor;struct.pack_into('<i',bin_data,offset,-size)
        bin_data[offset+4:offset+4+len(payload)]=payload;cursor+=size;return offset
    def name_bytes(name):
        try:return name.encode('latin-1'),True
        except UnicodeError:return name.encode('utf-16-le'),False
    def key(node,parent=0xffffffff):
        raw,compressed=name_bytes(node['name']);payload=bytearray(76)+raw
        payload[:2]=b'nk';struct.pack_into('<H',payload,2,32 if compressed else 0);struct.pack_into('<Q',payload,4,FT)
        struct.pack_into('<I',payload,16,parent);struct.pack_into('<H',payload,72,len(raw))
        offset=cell(payload)
        children=[key(child,offset) for child in node['children'].values()]
        if children:
            leaf=b'li' if index_kind==b'ri' else index_kind
            entries=b''.join(struct.pack('<I',pointer)+(b'\0'*4 if leaf in (b'lf',b'lh') else b'') for pointer in children)
            child_list=cell(leaf+struct.pack('<H',len(children))+entries)
            if index_kind==b'ri':child_list=cell(b'ri'+struct.pack('<HI',1,child_list))
            struct.pack_into('<II',bin_data,offset+4+20,len(children),0);struct.pack_into('<I',bin_data,offset+4+28,child_list)
        pointers=[]
        for name,kind,data,inline in node['values']:
            raw,compressed=name_bytes(name);vk=bytearray(20)+raw;vk[:2]=b'vk';struct.pack_into('<H',vk,2,len(raw))
            struct.pack_into('<I',vk,4,len(data)|(0x80000000 if inline else 0))
            if inline:vk[8:8+len(data)]=data
            else:struct.pack_into('<I',vk,8,cell(data) if data else 0xffffffff)
            struct.pack_into('<I',vk,12,kind);struct.pack_into('<H',vk,16,int(compressed));pointers.append(cell(vk))
        if pointers:
            values=cell(b''.join(struct.pack('<I',pointer) for pointer in pointers))
            struct.pack_into('<II',bin_data,offset+4+36,len(pointers),values)
        return offset
    root_offset=key(root)
    struct.pack_into('<i',bin_data,cursor,len(bin_data)-cursor)
    header=bytearray(4096);header[:4]=b'regf';struct.pack_into('<II',header,4,1,1)
    struct.pack_into('<IIIII',header,20,1,minor,0,1,root_offset);struct.pack_into('<I',header,40,len(bin_data))
    result=header+bin_data;return checksum(result)


def checksum(data):
    data=bytearray(data);result=0
    for number in struct.unpack('<127I',data[:508]):result^=number
    struct.pack_into('<I',data,508,1 if result==0 else 0xfffffffe if result==0xffffffff else result)
    return bytes(data)


def system_paths():
    paths={'Select':[value('Current',4,struct.pack('<I',2),True)],BASE:[text('FriendlyName','한글 USB'),value('HardwareID',7,'USBSTOR\\DiskACME\0USBSTOR\\GenDisk\0\0'.encode('utf-16-le'))],
           'ControlSet001\\Enum\\USBSTOR\\OTHER\\OLD':[],
           'ControlSet002\\Enum\\USB\\VID_1234&PID_ABCD\\INSTANCE':[text('DeviceDesc','USB device')],
           'MountedDevices':[value('\\DosDevices\\E:',3,'\\??\\USBSTOR#Disk&Ven_ACME#SERIAL&0#{GUID}'.encode('utf-16-le'))]}
    for pid in ('0064','0065','0066','0067'):paths[BASE+'\\Properties\\'+GUID+'\\'+pid]=[value('',3,struct.pack('<Q',FT))]
    return paths


class USBRegistryTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def file(self,name,data):path=self.folder/name;path.write_bytes(data);return path
    def parse(self,paths=None,role='system',**kwargs):
        report=Report();rows=usb_registry.analyze_hive(hive_fixture(system_paths() if paths is None else paths,**kwargs),role,1,report);return rows,report

    def test_active_controlset_and_device_identity(self):
        rows,report=self.parse();row=next(r for r in rows if r['observation_kind']=='usbstor')
        self.assertEqual((row['device_id'],row['instance_id'],row['vendor'],row['product'],row['revision']),(DEVICE,INSTANCE,'ACME','Flash','1.00'))
        self.assertEqual(row['friendly_name'],'한글 USB');self.assertEqual(row['control_set'],'ControlSet002')
        self.assertFalse(any('ControlSet001' in r['key_path'] for r in rows));self.assertEqual(row['key_last_written'],UTC)
        self.assertEqual(row['key_last_write_raw'],str(FT));self.assertNotIn('connected_at',row)

    def test_property_filetime_meanings_raw_values_and_offsets(self):
        rows,_=self.parse();row=next(r for r in rows if r['observation_kind']=='usbstor')
        self.assertEqual([t['meaning'] for t in row['device_times']],['install_date','first_install_date','last_arrival_date','last_removal_date'])
        self.assertTrue(all(t['filetime_raw']==str(FT) and t['time']==UTC for t in row['device_times']))
        self.assertTrue(all(t['key_offset']>=4096 and t['values'][0]['data_hex']==struct.pack('<Q',FT).hex() for t in row['device_times']))

    def test_usb_vid_pid_and_instance_not_physical_serial_claim(self):
        rows,_=self.parse();row=next(r for r in rows if r['observation_kind']=='usb')
        self.assertEqual((row['vid'],row['pid'],row['instance_id']),('1234','ABCD','INSTANCE'));self.assertNotIn('serial_number',row)

    def test_mounteddevices_kept_raw_without_drive_inference(self):
        rows,_=self.parse();row=next(r for r in rows if r['observation_kind']=='mounted_devices')
        self.assertEqual(row['values'][0]['name'],'\\DosDevices\\E:');self.assertIsNone(row['values'][0]['decoded'])
        self.assertNotIn('drive_letter',row);self.assertIsNone(row['device_id'])

    def test_software_and_ntuser_context_is_not_automatically_joined(self):
        software={'Microsoft\\Windows Portable Devices\\Devices\\USBSTOR#'+DEVICE+'#'+INSTANCE:[text('FriendlyName','Portable')]}
        rows,_=self.parse(software,'software');self.assertEqual(rows[0]['observation_kind'],'portable_device');self.assertEqual(rows[0]['friendly_name'],'Portable')
        rows,_=self.parse({'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\MountPoints2\\{volume}':[]},'ntuser')
        self.assertEqual(rows[0]['observation_kind'],'mount_point');self.assertIsNone(rows[0]['device_id']);self.assertNotIn('user_sid',rows[0])

    def test_deviceclasses_context_not_usb_proof(self):
        paths=system_paths();paths['ControlSet002\\Control\\DeviceClasses\\{53f56307-b6bf-11d0-94f2-00a0c91efb8b}\\##?#USBSTOR#DEVICE']=[]
        rows,_=self.parse(paths);row=next(r for r in rows if r['observation_kind']=='device_interface')
        self.assertIsNone(row['instance_id']);self.assertNotIn('first_connected',row)

    def test_all_supported_index_layouts_and_regf_versions(self):
        for kind in (b'li',b'lf',b'lh',b'ri'):
            for minor in (3,4,5):
                rows,_=self.parse(index_kind=kind,minor=minor);self.assertEqual(len(rows),3)

    def test_inline_dword_bigendian_qword_multisz_unknown(self):
        paths=system_paths();paths[BASE]+=[value('BE',5,b'\x01\x02\x03\x04',True),value('Q',11,b'\xff'*8),value('Unknown',999,b'raw')]
        rows,_=self.parse(paths);items={v['name']:v for v in rows[0]['values']}
        self.assertEqual(items['BE']['decoded'],str(0x01020304));self.assertEqual(items['Q']['decoded'],str(2**64-1))
        self.assertEqual(items['HardwareID']['decoded'],['USBSTOR\\DiskACME','USBSTOR\\GenDisk']);self.assertIsNone(items['Unknown']['decoded'])

    def test_missing_select_or_bad_current_never_falls_back(self):
        for paths in [{},{'Select':[]},{'Select':[value('Current',3,b'\x01\0\0\0')]},{'Select':[value('Current',4,b'\0'*4,True)]},{'Select':[value('Current',4,b'\x01\0\0\0',True)]}]:
            with self.assertRaises(AnalysisError):self.parse(paths)

    def test_empty_branches_and_absent_properties_diagnosed(self):
        rows,report=self.parse({'Select':[value('Current',4,b'\x02\0\0\0',True)],'ControlSet002':[]})
        self.assertFalse(rows);self.assertIn('usb_no_observations',{d['code'] for d in report.diagnostics})
        paths=system_paths()
        for pid in ('0064','0065','0066','0067'):del paths[BASE+'\\Properties\\'+GUID+'\\'+pid]
        rows,_=self.parse(paths);self.assertFalse(rows[0]['device_times'])

    def test_malformed_property_type_size_and_ambiguity_retained(self):
        for vals in [[value('',4,b'\0'*4)], [value('',3,b'\0'*7)], [value('',3,b'\0'*8),value('00000000',3,b'\0'*8)]]:
            paths=system_paths();paths[BASE+'\\Properties\\'+GUID+'\\0066']=vals
            rows,report=self.parse(paths);entry=rows[0]['device_times'][2]
            self.assertIsNone(entry['time']);self.assertIsNone(entry['filetime_raw']);self.assertEqual(len(entry['values']),len(vals))
            self.assertIn('usb_invalid_property',{d['code'] for d in report.diagnostics})

    def test_zero_overflow_property_and_invalid_text_preserved(self):
        paths=system_paths();paths[BASE+'\\Properties\\'+GUID+'\\0066']=[value('',16,b'\xff'*8)]
        paths[BASE+'\\Properties\\'+GUID+'\\0067']=[value('',3,b'\0'*8)]
        paths[BASE].append(value('Bad',1,b'\0\xd8'))
        rows,report=self.parse(paths);self.assertIsNone(rows[0]['device_times'][2]['time']);self.assertEqual(rows[0]['device_times'][2]['filetime_raw'],str(2**64-1))
        self.assertIn('registry_invalid_text',{d['code'] for d in report.diagnostics})

    def test_dirty_checksum_version_and_extent_fail(self):
        good=hive_fixture(system_paths())
        for offset,data in [(0,b'bad!'),(8,struct.pack('<I',2)),(24,struct.pack('<I',6)),(28,struct.pack('<I',1)),(32,struct.pack('<I',2)),(40,struct.pack('<I',4096)),(4096,b'xxxx')]:
            bad=bytearray(good);bad[offset:offset+len(data)]=data
            with self.assertRaises(AnalysisError):Hive(checksum(bad))
        bad=bytearray(good);bad[508]^=1
        with self.assertRaises(AnalysisError):Hive(bad)
        with self.assertRaises(AnalysisError):Hive(good+b'\0')

    def test_cell_reference_free_interior_bad_size_and_index_cycle(self):
        good=hive_fixture(system_paths(),index_kind=b'ri');h=Hive(good);root=h.key(h.root_offset)
        for reference in [0,root['offset']+1,0xffffffff]:
            with self.assertRaises(AnalysisError):h.cell(reference)
        bad=bytearray(good);struct.pack_into('<i',bad,4096+root['offset'],-7)
        with self.assertRaises(AnalysisError):Hive(bad)
        bad=bytearray(good);struct.pack_into('<I',bad,4096+root['children']+8,root['children'])
        h=Hive(bad)
        with self.assertRaises(AnalysisError):h.children(h.key(h.root_offset))

    def test_duplicate_names_parent_alias_and_wrong_record_rejected(self):
        paths=system_paths();paths['select']=[]
        with self.assertRaises(AnalysisError):self.parse(paths)
        paths=system_paths();paths[BASE]+=[text('friendlyname','duplicate')]
        with self.assertRaises(AnalysisError):self.parse(paths)
        good=hive_fixture(system_paths());h=Hive(good);key=h.open(BASE);bad=bytearray(good)
        struct.pack_into('<I',bad,4096+key['offset']+4+16,0)
        with self.assertRaises(AnalysisError):usb_registry.analyze_hive(bad,'system',1,Report())

    def test_counts_value_size_and_output_limits(self):
        good=hive_fixture(system_paths())
        for owner,name,limit in [(registry_hive,'MAX_CELLS',1),(registry_hive,'MAX_ITEMS',1),(registry_hive,'MAX_TOTAL_VALUE_BYTES',1),(usb_registry,'MAX_ROWS',1),(usb_registry,'MAX_OUTPUT_BYTES',1)]:
            with patch.object(owner,name,limit),self.assertRaises(AnalysisError):usb_registry.analyze_hive(good,'system',1,Report())
        paths=system_paths();paths[BASE].append(value('Big',3,b'x'*16345))
        with self.assertRaises(AnalysisError):self.parse(paths)

    def test_truncations_and_seeded_mutations_are_contract_errors(self):
        good=hive_fixture(system_paths());rng=random.Random(2017)
        for length in (0,3,511,4095,4096,len(good)-1):
            with self.assertRaises(AnalysisError):Hive(good[:length])
        for _ in range(100):
            bad=bytearray(good);offset=rng.randrange(4096+10000);bad[offset]^=rng.randrange(1,256)
            try:usb_registry.analyze_hive(bad,'system',1,Report())
            except AnalysisError:pass

    def test_unicode_keys_case_insensitive_paths_and_value_names(self):
        paths=system_paths();paths[BASE+'한글']=[text('FriendlyName','另一个')]
        rows,_=self.parse(paths);self.assertTrue(any('한글' in row['key_path'] for row in rows))
        h=Hive(hive_fixture(paths));self.assertIsNotNone(h.open(BASE.lower()))

    def test_source_hashes_roles_and_json_sqlite_schema_five(self):
        system=self.file('renamed',hive_fixture(system_paths()));before=system.read_bytes();report=analyze(usb_hives=[('system',system),('system',system)])
        self.assertEqual([s['source_kind'] for s in report.sources],['usb_registry']*2);self.assertEqual(report.sources[0]['sha256'],hashlib.sha256(before).hexdigest())
        self.assertEqual([r['source_id'] for r in report.usb_registry],[1,1,1,2,2,2])
        output=self.folder/'out.sqlite';write_report(report,output,'sqlite')
        with closing(sqlite3.connect(output)) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],5);self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
            self.assertEqual(json.loads(db.execute('SELECT device_times FROM usb_registry LIMIT 1').fetchone()[0])[0]['filetime_raw'],str(FT))
        output=self.folder/'out.json';write_report(report,output)
        self.assertEqual(json.loads(output.read_text())['format_version'],5);self.assertEqual(system.read_bytes(),before)

    def test_cli_subprocess_strict_and_multiple_roles(self):
        system=self.file('SYSTEM',hive_fixture(system_paths()));software=self.file('SOFTWARE',hive_fixture({'Microsoft\\Windows Portable Devices\\Devices\\device':[text('FriendlyName','Portable')]}))
        args=[sys.executable,'-m','plaintrace','--usb-system',str(system),'--usb-software',str(software),'--strict']
        result=subprocess.run(args,capture_output=True,text=True);self.assertEqual(result.returncode,1,result.stderr)
        payload=json.loads(result.stdout);self.assertEqual(payload['format_version'],5);self.assertEqual(payload['usb_registry'][-1]['source_id'],2)
        self.assertEqual(payload['usb_registry'][-1]['hive_role'],'software')

    def test_later_bad_input_atomic_and_existing_output_protected(self):
        system=self.file('SYSTEM',hive_fixture(system_paths()));bad=self.file('BAD',b'corrupt');output=self.folder/'out.json'
        with redirect_stderr(io.StringIO()):code=main(['--usb-system',str(system),'--usb-system',str(bad),'--output',str(output)])
        self.assertEqual(code,2);self.assertFalse(output.exists())
        before=system.read_bytes();report=analyze(usb_hives=[('system',system)])
        with self.assertRaises(AnalysisError):write_report(report,system)
        self.assertEqual(system.read_bytes(),before)

    def test_stable_read_and_no_logs_or_live_registry_access(self):
        system=self.file('SYSTEM',hive_fixture(system_paths()));log=self.file('SYSTEM.LOG1',b'unread')
        opened=[];original=Path.open
        def tracked(path,*args,**kwargs):opened.append(path);return original(path,*args,**kwargs)
        with patch.object(Path,'open',tracked):analyze(usb_hives=[('system',system)])
        self.assertEqual(set(opened),{system.resolve()});self.assertEqual(log.read_bytes(),b'unread')
        with patch('plaintrace.binary.bounded_hash',side_effect=['before','after']),self.assertRaises(AnalysisError):analyze(usb_hives=[('system',system)])

    def test_review_inline_length_key_flags_and_name_corruption(self):
        good=hive_fixture(system_paths());h=Hive(good);key=h.open(BASE);v=h.values(key)[0]
        for offset,raw in [(4096+v['offset']+8,struct.pack('<I',0x80000005)),(4096+key['offset']+6,struct.pack('<H',0x10)),(4096+key['offset']+80,b'\\')]:
            bad=bytearray(good);bad[offset:offset+len(raw)]=raw
            with self.assertRaises(AnalysisError):usb_registry.analyze_hive(bad,'system',1,Report())
        duplicate=bytearray(good);list_offset=4096+key['values']+4
        duplicate[list_offset+4:list_offset+8]=duplicate[list_offset:list_offset+4]
        with self.assertRaises(AnalysisError):usb_registry.analyze_hive(duplicate,'system',1,Report())
        huge=bytearray(good);struct.pack_into('<H',huge,4096+v['offset']+6,65535)
        with self.assertRaises(AnalysisError):usb_registry.analyze_hive(huge,'system',1,Report())
        paths=system_paths();paths[BASE].extend([value('Numeric',4,b'\0'),value('NoNul',1,'literal'.encode('utf-16-le'))])
        rows,report=self.parse(paths);self.assertIn('registry_invalid_integer',{d['code'] for d in report.diagnostics})
        self.assertIn('registry_unterminated_text',{d['code'] for d in report.diagnostics})

    def test_review_header_size_cap_multibin_and_unknown_role(self):
        good=hive_fixture(system_paths())
        with patch.object(registry_hive,'MAX_HIVE_BYTES',1),self.assertRaises(AnalysisError):Hive(good)
        bad=bytearray(good);extra=bytearray(4096);extra[:4]=b'hbin';struct.pack_into('<II',extra,4,len(good)-4096,4096);struct.pack_into('<i',extra,32,4064)
        bad+=extra;struct.pack_into('<I',bad,40,len(bad)-4096)
        self.assertIsNotNone(Hive(checksum(bad)).open(BASE))
        with self.assertRaises(AnalysisError):usb_registry.analyze_hive(good,'unknown',1,Report())

    def test_review_mixed_existing_artifacts_and_usb_source_order(self):
        from test_browser_cli import chromium
        from test_recycle_bin_cli import index_fixture
        browser=self.folder/'History'
        with closing(sqlite3.connect(browser)) as db:chromium(db)
        index=self.file('$IABC',index_fixture());system=self.file('SYSTEM',hive_fixture(system_paths()))
        report=analyze([browser],recycle_bins=[index],usb_hives=[('system',system)])
        self.assertEqual([s['source_kind'] for s in report.sources],['browser','recycle_bin','usb_registry'])
        self.assertEqual(report.usb_registry[0]['source_id'],3);self.assertEqual(report.as_dict()['counts']['usb_registry'],3)
