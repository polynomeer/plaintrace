"""Synthetic SAM metadata only; no acquired credentials or cryptographic fixtures."""
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
from plaintrace import sam_accounts as sa
from plaintrace.model import Report
from plaintrace.registry_hive import Hive
from plaintrace.execution import analyze
from plaintrace.exports import write_report
from plaintrace.cli import main
from plaintrace.evidence import AnalysisError
from test_usb_registry_cli import hive_fixture,value,text,checksum,FT,UTC
BASE=sa.BASE
USER=BASE+r'\000003E8'
NAMES=BASE+r'\Names'

# Fixed descriptors are specified independently of the production field table.
def f_record(rid=1000,flags=0x211,ticks=FT):
    raw=bytearray(80)
    for pos in (8,24,40):struct.pack_into('<Q',raw,pos,ticks)
    struct.pack_into('<IIHHHHHH',raw,48,rid,513,flags,0,82,949,3,17)
    return bytes(raw)
def v_record(username='계정😀',full_name='Full name'):
    header=bytearray(204);data=bytearray()
    for offset,s in ((12,username),(24,full_name),(36,'Admin comment'),(48,'User comment'),(72,r'%USERPROFILE%\home'),(84,'H:'),(96,'script.cmd'),(108,r'C:\Users\profile'),(120,'HOST-A,HOST-B')):
        raw=s.encode('utf-16-le');struct.pack_into('<II',header,offset,len(data),len(raw));data.extend(raw)
    return bytes(header+data)
def paths():return {USER:[value('F',3,f_record()),value('V',3,v_record())],NAMES+'\\계정😀':[value('',1000,b'')]}
def fixed(rows):return rows[0]['fixed_fields']
def string(rows,name):return next(s for s in rows[0]['strings'] if s['field']==name)

class SAMAccountTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def file(self,name,data):p=self.folder/name;p.write_bytes(data);return p
    def parse(self,p=None,**kw):
        r=Report();a,m=sa.analyze_hive(hive_fixture(paths() if p is None else p,**kw),1,r);return a,m,r
    def codes(self,r):return {d['code'] for d in r.diagnostics}

    def test_account_unicode_name_mapping_and_rid(self):
        a,m,r=self.parse();self.assertEqual(a[0]['rid_key'],1000);self.assertEqual(string(a,'username')['text'],'계정😀');self.assertEqual(string(a,'full_name')['text'],'Full name');self.assertEqual((m[0]['rid_reference'],m[0]['account_id'],m[0]['status']),(1000,a[0]['record_id'],'linked'));self.assertFalse(r.diagnostics)

    def test_fixed_offsets_unsigned_counts_country_and_flags(self):
        a,_,_=self.parse();f=fixed(a);self.assertEqual((f['rid_raw'],f['primary_group_rid_raw'],f['country_code_raw'],f['codepage_raw'],f['bad_password_count_raw'],f['logon_count_raw']),(1000,513,82,949,3,17));self.assertEqual(f['flags_raw'],0x211);self.assertEqual(f['flag_labels'],['disabled','normal_account','password_never_expires']);self.assertEqual(a[0]['f_record']['data_hex'],f_record().hex())

    def test_exact_filetimes_three_fields_and_separate_key_time(self):
        p=paths();p[USER][0]=value('F',3,f_record(ticks=FT+10));a,_,_=self.parse(p);self.assertEqual([t['offset'] for t in a[0]['times']],[8,24,40]);self.assertTrue(all(t['filetime_raw']==str(FT+10) and t['time']=='2020-01-01T00:00:00.123457Z' for t in a[0]['times']));self.assertEqual(a[0]['key_last_written'],UTC);self.assertNotIn('password_expires',a[0])

    def test_zero_and_sentinel_times_not_calendar_dates(self):
        for tick,state in ((0,'unset'),(0x7fffffffffffffff,'sentinel'),(0xffffffffffffffff,'sentinel')):
            p=paths();p[USER][0]=value('F',3,f_record(ticks=tick));a,_,_=self.parse(p);self.assertTrue(all(t['state']==state and t['time'] is None and t['filetime_raw']==str(tick) for t in a[0]['times']))

    def test_out_of_range_time_warns_without_losing_raw_ticks(self):
        tick=0x7ffffffffffffffe;p=paths();p[USER][0]=value('F',3,f_record(ticks=tick));a,_,r=self.parse(p);self.assertEqual(a[0]['times'][0]['state'],'out_of_range');self.assertEqual(a[0]['times'][0]['filetime_raw'],str(tick));self.assertIn('invalid_filetime',self.codes(r))

    def test_unknown_flags_and_maximum_counters_preserved(self):
        raw=bytearray(f_record(flags=0xffff));struct.pack_into('<HH',raw,64,65535,65535);p=paths();p[USER][0]=value('F',3,bytes(raw));a,_,_=self.parse(p);self.assertEqual(fixed(a)['unknown_flag_bits'],0xffff&~0x615);self.assertEqual(fixed(a)['logon_count_raw'],65535);self.assertNotIn('administrator',fixed(a));self.assertNotIn('effective_lockout',fixed(a))

    def test_f_rid_mismatch_retained_and_not_overwritten(self):
        p=paths();p[USER][0]=value('F',3,f_record(rid=500));a,m,r=self.parse(p);self.assertEqual((a[0]['rid_key'],fixed(a)['rid_raw']),(1000,500));self.assertEqual(m[0]['account_id'],a[0]['record_id']);self.assertIn('sam_accounts_rid_mismatch',self.codes(r))

    def test_f_wrong_type_size_missing_do_not_guess_layout(self):
        for values,status in (([value('F',1,f_record()),value('V',3,v_record())],'wrong_type'),([value('F',3,f_record()[:-1])],'wrong_size'),([value('F',3,f_record()+b'\0')],'wrong_size'),([],'missing')):
            a,_,r=self.parse({USER:values});self.assertEqual(a[0]['f_record']['status'],status);self.assertFalse(a[0]['fixed_fields'] or a[0]['times']);self.assertIsNone(a[0]['f_record']['data_hex']);self.assertIn('sam_accounts_unsupported_record',self.codes(r))

    def test_missing_v_still_retains_f_metadata(self):
        a,_,_=self.parse({USER:[value('F',3,f_record())]});self.assertEqual(a[0]['v_record']['status'],'missing');self.assertEqual(fixed(a)['rid_raw'],1000);self.assertFalse(a[0]['strings'])

    def test_v_wrong_type_and_short_header_retained_as_summary(self):
        for kind,raw,status in ((1,v_record(),'wrong_type'),(3,bytes(203),'wrong_size')):
            a,_,_=self.parse({USER:[value('V',kind,raw)]});self.assertEqual(a[0]['v_record']['status'],status);self.assertEqual(a[0]['v_record']['sha256'],hashlib.sha256(raw).hexdigest());self.assertFalse(a[0]['strings']);self.assertNotIn('data_hex',a[0]['v_record'])

    def test_v_relative_offsets_descriptor_bytes_and_literals(self):
        a,_,_=self.parse();s=string(a,'home_directory');self.assertEqual(s['text'],r'%USERPROFILE%\home');self.assertEqual(s['data_offset'],204+s['relative_offset']);self.assertEqual(s['descriptor_hex'],v_record()[72:80].hex());self.assertEqual(bytes.fromhex(s['utf16_hex']),v_record()[s['data_offset']:s['data_offset']+s['byte_length']]);self.assertNotIn('resolved_path',s)

    def test_v_empty_length_is_not_missing(self):
        p=paths();p[USER][1]=value('V',3,v_record(username=''));a,_,_=self.parse(p);self.assertEqual((string(a,'username')['status'],string(a,'username')['text'],string(a,'username')['utf16_hex']),('empty','',''))

    def test_v_invalid_bounds_keep_descriptors_without_repair(self):
        raw=bytearray(v_record());struct.pack_into('<II',raw,12,0xffffff00,10);p=paths();p[USER][1]=value('V',3,bytes(raw));a,_,r=self.parse(p);s=string(a,'username');self.assertEqual(s['status'],'invalid_bounds');self.assertIsNone(s['text']);self.assertIsNone(s['utf16_hex']);self.assertEqual(s['relative_offset'],0xffffff00);self.assertIn('sam_accounts_invalid_string',self.codes(r))

    def test_v_odd_offset_or_length_not_shifted(self):
        for offset,length in ((1,2),(0,3)):
            raw=bytearray(v_record());struct.pack_into('<II',raw,12,offset,length);p=paths();p[USER][1]=value('V',3,bytes(raw));a,_,_=self.parse(p);self.assertEqual(string(a,'username')['status'],'invalid_alignment');self.assertIsNone(string(a,'username')['text'])

    def test_v_invalid_unicode_and_embedded_nul_preserved(self):
        for content,status,expected in ((b'\0\xd8','invalid_text',r'\x00\xd8'),(b'a\0\0\0','embedded_nul','a\0')):
            raw=bytearray(v_record());struct.pack_into('<II',raw,12,0,len(content));raw[204:204+len(content)]=content;p=paths();p[USER][1]=value('V',3,bytes(raw));a,_,_=self.parse(p);self.assertEqual((string(a,'username')['status'],string(a,'username')['text']),(status,expected));self.assertEqual(string(a,'username')['utf16_hex'],content.hex())

    def test_v_overlapping_ranges_diagnosed_without_silent_repair(self):
        raw=bytearray(v_record());raw[24:32]=raw[12:20];p=paths();p[USER][1]=value('V',3,bytes(raw));a,_,r=self.parse(p);self.assertEqual(string(a,'full_name')['text'],'계정😀');self.assertIn('sam_accounts_overlapping_strings',self.codes(r))

    def test_unselected_v_payload_and_other_values_not_exported(self):
        marker=b'OPAQUE-NONACCOUNT-PAYLOAD';raw=v_record()+marker;p=paths();p[USER][1]=value('V',3,raw);p[USER].append(value('Other',3,marker));a,_,_=self.parse(p);payload=json.dumps(a);self.assertNotIn(marker.hex(),payload);self.assertNotIn(marker.decode(),payload);self.assertEqual(a[0]['v_record']['sha256'],hashlib.sha256(raw).hexdigest());self.assertEqual(a[0]['other_values'][0]['byte_length'],len(marker));self.assertNotIn('nt_hash',payload);self.assertNotIn('lm_hash',payload)

    def test_names_default_type_is_rid_not_data_integer(self):
        a,m,_=self.parse();self.assertEqual(m[0]['values'][0]['type'],1000);self.assertEqual(m[0]['values'][0]['byte_length'],0);self.assertEqual(m[0]['rid_reference'],1000)
        p=paths();p[NAMES+'\\계정😀']=[value('',4,struct.pack('<I',1000))];_,m,r=self.parse(p);self.assertEqual(m[0]['status'],'invalid');self.assertIsNone(m[0]['rid_reference']);self.assertIsNone(m[0]['account_id'])

    def test_orphan_invalid_and_duplicate_name_mappings_retained(self):
        p=paths();p[NAMES+'\\Alias']=[value('',1000,b'')];p[NAMES+'\\Orphan']=[value('',999,b'')];p[NAMES+'\\Invalid']=[];a,m,r=self.parse(p);self.assertEqual(len(m),4);self.assertEqual([x['status'] for x in m],['linked','linked','orphan','invalid']);self.assertIn('sam_accounts_duplicate_mapping',self.codes(r));self.assertIn('sam_accounts_name_mismatch',self.codes(r))

    def test_missing_names_unmapped_rid_no_invented_username(self):
        a,m,r=self.parse({USER:[value('F',3,f_record())]});self.assertFalse(m);self.assertFalse(a[0]['strings']);self.assertIn('sam_accounts_names_absent',self.codes(r));self.assertIn('sam_accounts_unmapped_account',self.codes(r))

    def test_missing_empty_users_and_noncanonical_children(self):
        a,m,r=self.parse({});self.assertFalse(a or m);self.assertIn('sam_accounts_absent',self.codes(r))
        a,m,r=self.parse({BASE:[]});self.assertFalse(a or m);self.assertIn('sam_accounts_no_accounts',self.codes(r))
        a,m,r=self.parse({BASE+'\\1000':[]});self.assertFalse(a);self.assertIn('sam_accounts_unsupported_key',self.codes(r))

    def test_descendants_and_container_values_not_traversed(self):
        p=paths();p[USER+'\\ignored']=[value('V',3,v_record())];p[NAMES+'\\계정😀\\ignored']=[];p[BASE]=[text('container','metadata')];a,m,r=self.parse(p);self.assertEqual(len(a),1);self.assertEqual(len(m),1);self.assertIn('sam_accounts_nested_keys',self.codes(r));self.assertIn('sam_accounts_root_values',self.codes(r))

    def test_physical_cell_offsets_and_key_filetimes(self):
        data=hive_fixture(paths());h=Hive(data);a,m,_=self.parse();self.assertEqual(int(a[0]['record_id']),h.open(USER)['offset']+4096);self.assertEqual(a[0]['key_last_write_raw'],str(FT));self.assertEqual(m[0]['key_last_written'],UTC)
        for meta in (a[0]['f_record'],a[0]['v_record'],m[0]['values'][0]):self.assertEqual(data[meta['value_offset']+4:meta['value_offset']+6],b'vk')

    def test_case_insensitive_paths_and_record_names(self):
        p={k.lower():[(name.lower(),kind,raw,inline) for name,kind,raw,inline in vals] for k,vals in paths().items()};a,m,_=self.parse(p);self.assertEqual(fixed(a)['rid_raw'],1000);self.assertEqual(m[0]['status'],'linked')

    def test_regf_versions_indexes_and_duplicate_values(self):
        for kind in (b'li',b'lf',b'lh',b'ri'):
            for minor in (3,4,5):self.assertEqual(len(self.parse(index_kind=kind,minor=minor)[0]),1)
        p=paths();p[USER].append(value('f',3,f_record()))
        with self.assertRaises(AnalysisError):self.parse(p)

    def test_dirty_and_corrupt_hive_rejected(self):
        raw=bytearray(hive_fixture(paths()));struct.pack_into('<I',raw,4,2)
        for data in (b'bad',b'regf',checksum(raw)):
            with self.assertRaises(AnalysisError):sa.analyze_hive(data,1,Report())

    def test_account_mapping_value_string_and_output_budgets(self):
        for constant in ('MAX_ACCOUNTS','MAX_MAPPINGS','MAX_VALUES','MAX_STRING_UNITS','MAX_OUTPUT_BYTES'):
            with patch.object(sa,constant,0),self.assertRaises(AnalysisError):self.parse()

    def test_json_sqlite_schema_raw_strings_and_foreign_keys(self):
        f=self.file('SAM',hive_fixture(paths()));r=analyze(sam_hives=[f]);j=self.folder/'out.json';s=self.folder/'out.sqlite';write_report(r,j);write_report(r,s,'sqlite');p=json.loads(j.read_text());self.assertEqual(p['format_version'],15);self.assertEqual(p['sam_accounts'],r.sam_accounts)
        with closing(sqlite3.connect(s)) as db:
            self.assertEqual(db.execute('pragma user_version').fetchone()[0],15);self.assertEqual(db.execute('pragma foreign_key_check').fetchall(),[]);self.assertEqual(json.loads(db.execute('select strings from sam_accounts').fetchone()[0]),r.sam_accounts[0]['strings']);db.execute('pragma foreign_keys=on')
            with self.assertRaises(sqlite3.IntegrityError):db.execute("update sam_name_mappings set account_id='missing'")

    def test_repeated_sources_hashes_and_unchanged_input(self):
        data=hive_fixture(paths());f=self.file('renamed',data);r=analyze(sam_hives=[f,f]);self.assertEqual(len(r.sam_accounts),2);self.assertEqual([s['source_id'] for s in r.sources],[1,2]);self.assertTrue(all(s['sha256']==hashlib.sha256(data).hexdigest() and s['schema_family']=='registry_sam' for s in r.sources));self.assertEqual(f.read_bytes(),data)

    def test_cli_json_strict_and_sqlite(self):
        f=self.file('SAM',hive_fixture(paths()));out=self.folder/'out.sqlite';args=[sys.executable,'-m','plaintrace','--sam',str(f)]
        r=subprocess.run(args,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(len(json.loads(r.stdout)['sam_accounts']),1)
        r=subprocess.run(args+['--format','sqlite','--output',str(out)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
        bad=self.file('unmapped',hive_fixture({USER:[]}));r=subprocess.run([sys.executable,'-m','plaintrace','--sam',str(bad),'--strict'],capture_output=True,text=True);self.assertEqual(r.returncode,1);self.assertEqual(len(json.loads(r.stdout)['sam_accounts']),1)

    def test_mixed_sources_do_not_attribute_machine_or_sid(self):
        f=self.file('SAM',hive_fixture(paths()));r=analyze(explorer_hives=[('typed_paths',f)],sam_hives=[f]);self.assertEqual([s['source_kind'] for s in r.sources],['typed_paths','sam_accounts']);self.assertEqual(r.sam_accounts[0]['source_id'],2);self.assertNotIn('sid',r.sam_accounts[0])

    def test_later_failure_no_partial_report(self):
        f=self.file('good',hive_fixture(paths()));bad=self.file('bad',b'bad');out=self.folder/'out.json'
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):self.assertEqual(main(['--sam',str(f),'--sam',str(bad),'--output',str(out)]),2)
        self.assertFalse(out.exists());self.assertFalse(list(self.folder.glob('.plaintrace-*')))

    def test_input_existing_output_and_sidecar_protected(self):
        data=hive_fixture(paths());f=self.file('SAM',data);out=self.file('out',b'keep')
        for dest in (f,out,self.folder/'SAM-wal'):
            with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):self.assertEqual(main(['--sam',str(f),'--output',str(dest)]),2)
        self.assertEqual(f.read_bytes(),data);self.assertEqual(out.read_bytes(),b'keep')

    def test_missing_input_sqlite_destination_and_only_hive_reads(self):
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            self.assertEqual(main(['--sam',str(self.folder/'missing')]),2)
            with self.assertRaises(SystemExit) as error:main(['--sam','missing','--format','sqlite'])
        self.assertEqual(error.exception.code,2)
        f=self.file('SAM',hive_fixture(paths()));real=Path.open;opened=[]
        def track(p,*a,**kw):opened.append(str(p));return real(p,*a,**kw)
        with patch.object(Path,'open',track):analyze(sam_hives=[f])
        self.assertEqual(set(opened),{str(f.resolve())})
        with patch('plaintrace.binary.bounded_hash',side_effect=['before','after']),self.assertRaises(AnalysisError):analyze(sam_hives=[f])

    def test_seeded_f_payload_mutations_keep_controlled_status(self):
        rng=random.Random(52)
        for _ in range(60):
            raw=bytes(rng.randrange(256) for _ in range(rng.randrange(100)));a,_,_=self.parse({USER:[value('F',3,raw)]});self.assertEqual(a[0]['f_record']['sha256'],hashlib.sha256(raw).hexdigest());self.assertEqual(a[0]['f_record']['status'],'parsed' if len(raw)==80 else 'wrong_size')

if __name__=='__main__':unittest.main()
