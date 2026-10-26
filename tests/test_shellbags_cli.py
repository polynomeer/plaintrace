"""Synthetic ShellBags hierarchy, partial decoding and cross-reference oracles."""
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
from plaintrace import shellbags,shell_items
from plaintrace.cli import main
from plaintrace.evidence import AnalysisError
from plaintrace.execution import analyze
from plaintrace.exports import write_report
from plaintrace.model import Report
from shellbag_fixtures import NT,UC,FAT,FAT_TEXT,GUID,paths,mru,node,shell_value,root_item,volume,network,file_item
from test_usb_registry_cli import hive_fixture,value,text,FT,UTC

class ShellBagsTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def file(self,name,data):p=self.folder/name;p.write_bytes(data);return p
    def parse(self,source=None,role='ntuser',codepage='cp1252',**kw):
        report=Report();views,keys,rows=shellbags.analyze_hive(hive_fixture(paths() if source is None else source,**kw),role,1,report,codepage)
        return views,keys,rows,report
    def single(self,raw):return self.parse({NT+'\\BagMRU':[value('0',3,raw),mru(0)]})

    def test_hierarchy_guid_volume_long_names_and_same_hive_views(self):
        views,keys,rows,report=self.parse();self.assertFalse(report.diagnostics);self.assertEqual(len(keys),4);self.assertEqual(len(rows),5)
        self.assertEqual(rows[0]['path_candidate'],'::{'+GUID+'}');self.assertEqual(rows[1]['path_candidate'],'C:\\')
        self.assertEqual(rows[2]['path_candidate'],'C:\\한글😀');self.assertEqual(rows[-1]['path_candidate'],'C:\\한글😀\\Child')
        self.assertEqual(keys[-1]['parent_entry_id'],rows[2]['record_id']);self.assertEqual(keys[2]['bag_key_id'],keys[3]['bag_key_id'])
        self.assertEqual(len({v['record_id'] for v in views}),len(views));self.assertTrue(any(v['key_path'].endswith('{view}') for v in views))

    def test_ntuser_and_usrclass_root_layouts_are_role_explicit(self):
        for role,bases in shellbags.ROOTS.items():
            source={base+'\\BagMRU':[mru()] for base in bases};_,keys,rows,report=self.parse(source,role)
            self.assertEqual(len(keys),len(bases));self.assertFalse(rows);self.assertFalse(report.diagnostics)
            self.assertEqual({k['hive_role'] for k in keys},{role})
        self.assertFalse(self.parse(paths(UC),role='ntuser')[1]);self.assertEqual(len(self.parse(paths(UC),role='usrclass')[1]),4)

    def test_mru_sparse_order_is_rank_not_timestamp(self):
        _,keys,rows,_=self.parse({NT+'\\BagMRU':[shell_value(1,file_item('A')),shell_value(9,file_item('B')),mru(9,7,1)]})
        self.assertEqual(keys[0]['mru_order'],['9','7','1']);self.assertEqual([r['mru_rank'] for r in rows],[2,0])
        self.assertTrue(all('opened_at' not in r for r in rows));self.assertEqual(keys[0]['key_last_write_raw'],str(FT));self.assertEqual(keys[0]['key_last_written'],UTC)

    def test_invalid_ambiguous_and_missing_mru_keep_raw_no_ranks(self):
        for controls in ([],[mru(0,0)],[mru(0),text('MRUList','a')],[value('MRUListEx',3,b'\0'*3)],[text('MRUListEx','wrong')]):
            _,keys,rows,report=self.parse({NT+'\\BagMRU':[shell_value(0,file_item()),*controls]})
            self.assertIsNone(rows[0]['mru_rank']);self.assertNotEqual(keys[0]['mru_status'],'valid');self.assertEqual(len(keys[0]['control_values']),len(controls));self.assertTrue(report.diagnostics)

    def test_unlisted_and_noncanonical_values_are_not_dropped(self):
        source={NT+'\\BagMRU':[shell_value(1,file_item()),mru(),shell_value('01',file_item()),shell_value('4294967295',file_item()),value('NodeSlots',3,b'raw')]}
        _,keys,rows,report=self.parse(source);self.assertEqual(len(rows),1);self.assertEqual(len(keys[0]['other_values']),3)
        self.assertIn('shellbag_unlisted_entry',{d['code'] for d in report.diagnostics})

    def test_valid_empty_mru_and_absent_roots(self):
        _,keys,rows,report=self.parse({NT+'\\BagMRU':[mru()]});self.assertFalse(rows);self.assertEqual(keys[0]['mru_status'],'valid');self.assertFalse(report.diagnostics)
        views,keys,rows,report=self.parse({'Unrelated':[]});self.assertFalse(views or keys or rows);self.assertEqual(report.diagnostics[0]['code'],'shellbags_absent')

    def test_node_slot_type_missing_bag_and_raw_controls(self):
        for entry,code in ((text('NodeSlot','3'),'shellbag_invalid_nodeslot'),(node(999),'shellbag_missing_bag')):
            _,keys,_,report=self.parse({NT+'\\BagMRU':[mru(),entry]});self.assertIsNone(keys[0]['bag_key_id'])
            self.assertIn(code,{d['code'] for d in report.diagnostics});self.assertEqual(keys[0]['other_values'][0]['data_hex'],entry[2].hex())

    def test_node_slot_belongs_to_key_not_child_value(self):
        views,keys,rows,_=self.parse();self.assertEqual(keys[0]['node_slot'],1)
        self.assertNotIn('node_slot',rows[0]);self.assertIsNone(keys[0]['parent_entry_id']);self.assertIsNone(keys[0]['path_candidate'])
        self.assertEqual(keys[1]['path_candidate'],rows[0]['path_candidate'])

    def test_missing_parent_value_propagates_unresolved_ancestry(self):
        source={NT+'\\BagMRU':[mru()],NT+'\\BagMRU\\9':[shell_value(1,file_item('Child')),mru(1)]}
        _,keys,rows,report=self.parse(source);self.assertIsNone(keys[1]['parent_entry_id']);self.assertIsNone(rows[0]['path_candidate']);self.assertFalse(rows[0]['ancestry_complete'])
        self.assertIn('shellbag_missing_parent_value',{d['code'] for d in report.diagnostics})

    def test_unknown_ancestor_is_not_guessed_and_explicit_volume_can_anchor(self):
        unknown=struct.pack('<HB',3,0x61)
        source={NT+'\\BagMRU':[shell_value(0,unknown),mru(0)],NT+'\\BagMRU\\0':[shell_value(1,file_item('NoRoot')),shell_value(2,volume('D:\\')),mru(1,2)]}
        _,_,rows,_=self.parse(source);self.assertIsNone(rows[0]['path_candidate']);self.assertIsNone(rows[1]['path_candidate']);self.assertEqual(rows[2]['path_candidate'],'D:\\')

    def test_noncanonical_child_is_diagnosed_and_not_traversed(self):
        _,keys,rows,report=self.parse({NT+'\\BagMRU':[mru()],NT+'\\BagMRU\\01':[shell_value(0,file_item()),mru(0)]})
        self.assertEqual(len(keys),1);self.assertFalse(rows);self.assertIn('shellbag_noncanonical_child',{d['code'] for d in report.diagnostics})

    def test_duplicate_paths_and_separate_roots_are_preserved(self):
        source={base+'\\BagMRU':[shell_value(0,file_item('same')),shell_value(7,file_item('same')),mru(0,7)] for base in shellbags.ROOTS['ntuser'][:2]}
        _,keys,rows,_=self.parse(source);self.assertEqual(len(rows),4);self.assertEqual(len(keys),2);self.assertEqual(len({r['record_id'] for r in rows}),4)

    def test_file_entry_extension_versions_and_exact_fat_bytes(self):
        for version in (3,7,8,9):
            _,_,rows,_=self.single(shell_value(0,file_item('SHORT',long_name='Long😀',version=version))[2]);item=rows[0]['items'][0];extension=item['extensions'][0]
            self.assertEqual(item['display_name'],'Long😀');self.assertEqual(item['primary_name'],'SHORT');self.assertEqual(extension['created_fat']['raw_hex'],FAT.hex());self.assertEqual(extension['created_fat']['display'],FAT_TEXT)
            self.assertEqual(item['metadata']['modified_fat']['display'],FAT_TEXT);self.assertNotIn('Z',FAT_TEXT)

        original=file_item('SHORT',long_name='Long');ext=int.from_bytes(original[-2:],'little')
        double=bytearray(original+original[ext:]);struct.pack_into('<H',double,0,len(double))
        _,_,rows,report=self.single(bytes(double)+bytes(2))
        self.assertEqual(rows[0]['items'][0]['display_name'],'SHORT')
        self.assertIn('shellbag_ambiguous_long_name',{d['code'] for d in report.diagnostics})

    def test_unknown_extension_version_retains_primary_without_guess(self):
        _,_,rows,report=self.single(shell_value(0,file_item('SHORT',long_name='not selected',version=10))[2])
        self.assertEqual(rows[0]['items'][0]['display_name'],'SHORT');self.assertIsNone(rows[0]['items'][0]['long_name']);self.assertTrue(report.diagnostics)

    def test_malformed_extension_offsets_sizes_and_backlinks_keep_whole_raw(self):
        original=file_item('SHORT',long_name='Long');ext=int.from_bytes(original[-2:],'little')
        for offset,n in ((len(original)-2,65535),(ext,65535),(ext+16,0)):
            data=bytearray(original);struct.pack_into('<H',data,offset,n)
            # Offset 16 is opaque; other pointer/size corruptions must be malformed.
            _,_,rows,_=self.single(bytes(data)+bytes(2));self.assertEqual(rows[0]['value_data_hex'],(bytes(data)+bytes(2)).hex())
            if offset!=ext+16:self.assertEqual(rows[0]['item_status'],'malformed');self.assertIsNone(rows[0]['path_candidate'])

        double=bytearray(original+original[ext:]);struct.pack_into('<H',double,0,len(double))
        first_backlink=ext+int.from_bytes(original[ext:ext+2],'little')-2
        struct.pack_into('<H',double,first_backlink,ext+2)
        _,_,rows,_=self.single(bytes(double)+bytes(2));self.assertEqual(rows[0]['item_status'],'malformed')

    def test_ansi_codepage_and_unicode_names(self):
        for wide,encoding in ((False,'cp949'),(True,'cp1252')):
            source={NT+'\\BagMRU':[shell_value(0,file_item('경로',wide=wide,encoding=encoding)),mru(0)]}
            _,_,rows,_=self.parse(source,codepage=encoding);self.assertEqual(rows[0]['path_candidate'],'경로')

    def test_invalid_unicode_does_not_become_path(self):
        data=bytearray(file_item('A',wide=True));data[14:16]=b'\0\xd8'
        _,_,rows,report=self.single(bytes(data)+bytes(2));self.assertIsNone(rows[0]['path_candidate']);self.assertIn('shellbag_invalid_text',{d['code'] for d in report.diagnostics})

    def test_network_unc_and_folder_hierarchy_literal(self):
        source={NT+'\\BagMRU':[shell_value(0,network()),mru(0)],NT+'\\BagMRU\\0':[shell_value(1,file_item('Folder')),mru(1)]}
        _,_,rows,_=self.parse(source);self.assertEqual(rows[-1]['path_candidate'],'\\\\server\\share\\Folder');self.assertEqual(rows[-1]['path_basis'],'stored_unc_hierarchy')

    def test_unsupported_volume_network_and_namespace_variants_stay_opaque(self):
        for item in (struct.pack('<HB',3,0x2e),struct.pack('<HB',3,0x71),struct.pack('<HB',3,0xb1)):
            _,_,rows,_=self.single(item+bytes(2));self.assertEqual(rows[0]['items'][0]['status'],'unsupported');self.assertIsNone(rows[0]['path_candidate'])

    def test_root_guid_not_mapped_and_opaque_tail_retained(self):
        item=bytearray(root_item()+b'raw');struct.pack_into('<H',item,0,len(item));_,_,rows,report=self.single(bytes(item)+bytes(2))
        self.assertEqual(rows[0]['items'][0]['folder_id'],GUID);self.assertEqual(rows[0]['path_candidate'],'::{'+GUID+'}');self.assertIn('shellbag_opaque_root_tail',{d['code'] for d in report.diagnostics})

    def test_dot_and_separator_names_not_composed_or_normalized(self):
        for name in ('.','..','a\\b','C:relative','a/b'):
            _,_,rows,_=self.single(shell_value(0,file_item(name,wide=True))[2]);self.assertIsNone(rows[0]['path_candidate']);self.assertEqual(rows[0]['items'][0]['display_name'],name)

    def test_item_list_multiple_components_and_optional_terminal(self):
        for terminal in (True,False):
            _,_,rows,_=self.single(shell_value(0,volume(),file_item('Folder'),terminal=terminal)[2])
            self.assertEqual(rows[0]['path_candidate'],'C:\\Folder');self.assertEqual(rows[0]['item_list_terminated'],terminal)

    def test_trailing_bytes_empty_and_wrong_type_keep_raw(self):
        _,_,rows,report=self.single(shell_value(0,volume())[2]+b'extra');self.assertIsNone(rows[0]['path_candidate']);self.assertEqual(rows[0]['item_trailing_hex'],b'extra'.hex())
        _,_,rows,_=self.single(bytes(2));self.assertEqual(rows[0]['item_status'],'empty')
        _,_,rows,_=self.parse({NT+'\\BagMRU':[text('0','wrong'),mru(0)]});self.assertEqual(rows[0]['item_status'],'wrong_type');self.assertIsNone(rows[0]['path_candidate'])

    def test_malformed_list_bounds_and_strings_are_observations(self):
        for raw in (b'\x01\0x',b'\xff\xffx',b'x',struct.pack('<HB',3,0x1f)):
            _,_,rows,_=self.single(raw);self.assertEqual(rows[0]['item_status'],'malformed');self.assertEqual(rows[0]['value_data_hex'],raw.hex())

    def test_zero_invalid_fat_times_keep_raw_no_epoch_guess(self):
        for raw in (bytes(4),b'\xff'*4):
            data=bytearray(file_item('Folder'));data[8:12]=raw;_,_,rows,_=self.single(bytes(data)+bytes(2))
            fat=rows[0]['items'][0]['metadata']['modified_fat'];self.assertIsNone(fat['display']);self.assertEqual(fat['raw_hex'],raw.hex());self.assertEqual(fat['time_basis'],'stored_fat_no_timezone')

    def test_item_and_extension_budgets_are_fatal_not_malformed_rows(self):
        with patch.object(shell_items,'MAX_ITEMS',1),self.assertRaises(AnalysisError):self.single(shell_value(0,root_item(),volume())[2])
        with patch.object(shell_items,'MAX_EXTENSIONS',0),self.assertRaises(AnalysisError):self.single(shell_value(0,file_item(long_name='long'))[2])
        with patch.object(shell_items,'MAX_VALUE_BYTES',1),self.assertRaises(AnalysisError):self.single(shell_value(0,volume())[2])

    def test_key_view_entry_output_and_path_budgets(self):
        for name in ('MAX_KEYS','MAX_VIEW_KEYS','MAX_ENTRIES','MAX_OUTPUT_BYTES','MAX_PATH_CHARS'):
            with patch.object(shellbags,name,1),self.assertRaises(AnalysisError):self.parse()

    def test_hierarchy_and_view_depth_are_bounded(self):
        with patch.object(shellbags,'MAX_DEPTH',1),self.assertRaises(AnalysisError):self.parse()
        source={NT+'\\BagMRU':[node(1),mru()],NT+'\\Bags\\1\\Shell\\Deep':[]}
        with patch.object(shellbags,'MAX_DEPTH',1),self.assertRaises(AnalysisError):self.parse(source)

    def test_regf_versions_indexes_case_paths_and_dirty_hives(self):
        for minor in (3,4,5):
            for index in (b'li',b'lf',b'lh',b'ri'):self.assertEqual(len(self.parse(minor=minor,index_kind=index)[2]),5)
        self.assertEqual(len(self.parse({path.upper():values for path,values in paths().items()})[2]),5)
        data=bytearray(hive_fixture(paths()));data[8]^=1
        with self.assertRaises(AnalysisError):shellbags.analyze_hive(bytes(data),'ntuser',1,Report())

    def test_role_and_encoding_validation_are_fatal(self):
        for role,encoding in (('system','cp1252'),('ntuser','missing-codepage'),('ntuser','utf-16-le')):
            with self.assertRaises(AnalysisError):self.parse(role=role,codepage=encoding)

    def test_cli_repeated_roles_hashes_and_schema(self):
        a=self.file('renamed-a',hive_fixture(paths()));b=self.file('renamed-b',hive_fixture(paths(UC)));before=a.read_bytes()
        result=subprocess.run([sys.executable,'-m','plaintrace','--shellbags-ntuser',str(a),'--shellbags-usrclass',str(b)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);payload=json.loads(result.stdout);self.assertEqual(payload['format_version'],13);self.assertEqual(payload['counts']['shellbag_entries'],10)
        self.assertEqual([s['schema_family'] for s in payload['sources']],['registry_ntuser','registry_usrclass']);self.assertEqual(payload['sources'][0]['sha256'],hashlib.sha256(before).hexdigest());self.assertEqual(a.read_bytes(),before)

    def test_json_sqlite_raw_roundtrip_and_composite_relationships(self):
        p=self.file('hive',hive_fixture(paths()));report=analyze(shellbag_hives=[('ntuser',p)]);js=self.folder/'out.json';db=self.folder/'out.sqlite'
        write_report(report,js);write_report(report,db,'sqlite');self.assertEqual(json.loads(js.read_text())['format_version'],13)
        with closing(sqlite3.connect(db)) as c:
            self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],13);self.assertFalse(c.execute('PRAGMA foreign_key_check').fetchall())
            self.assertEqual(c.execute('SELECT path_candidate FROM shellbag_entries ORDER BY rowid').fetchall(),[(r['path_candidate'],) for r in report.shellbag_entries])
            self.assertEqual(json.loads(c.execute('SELECT items FROM shellbag_entries LIMIT 1').fetchone()[0])[0]['folder_id'],GUID)
            c.execute('PRAGMA foreign_keys=ON')
            with self.assertRaises(sqlite3.IntegrityError):c.execute("UPDATE shellbag_entries SET key_id='missing'")
            c.rollback()
            with self.assertRaises(sqlite3.IntegrityError):c.execute("UPDATE shellbag_keys SET bag_key_id='missing'")
            c.rollback();c.execute("UPDATE shellbag_keys SET parent_entry_id='missing'")
            with self.assertRaises(sqlite3.IntegrityError):c.commit()

    def test_deferred_orphan_parent_fails_without_publishing_output(self):
        p=self.file('hive',hive_fixture(paths()));report=analyze(shellbag_hives=[('ntuser',p)]);report.shellbag_keys[-1]['parent_entry_id']='missing';db=self.folder/'out.sqlite'
        with self.assertRaises(sqlite3.IntegrityError):write_report(report,db,'sqlite')
        self.assertFalse(db.exists())

    def test_mixed_adapters_do_not_join_users_or_duplicate_sources(self):
        from test_application_mru_cli import paths as apps
        source=paths();source.update(apps());p=self.file('hive',hive_fixture(source))
        report=analyze(application_hives=[p],shellbag_hives=[('ntuser',p),('ntuser',p)])
        self.assertEqual([s['source_kind'] for s in report.sources],['application_mru','shellbags','shellbags']);self.assertEqual({r['source_id'] for r in report.shellbag_entries},{2,3})

    def test_cli_strict_fatal_atomic_and_evidence_protection(self):
        p=self.file('hive',hive_fixture({NT+'\\BagMRU':[]}));bad=self.file('bad',b'bad');output=self.folder/'strict.json';absent=self.folder/'absent.json'
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            self.assertEqual(main(['--shellbags-ntuser',str(p),'--strict','--output',str(output)]),1)
            self.assertEqual(main(['--shellbags-ntuser',str(p),'--output',str(p)]),2)
            self.assertEqual(main(['--shellbags-ntuser',str(p),'--shellbags-ntuser',str(bad),'--output',str(absent)]),2)
        self.assertTrue(output.exists());self.assertFalse(absent.exists())

    def test_only_supplied_hive_opened_and_changing_read_rejected(self):
        p=self.file('hive',hive_fixture(paths()));opened=[];real=Path.open
        def watch(path,*args,**kw):opened.append(path);return real(path,*args,**kw)
        with patch.object(Path,'open',watch):analyze(shellbag_hives=[('ntuser',p)])
        self.assertEqual(set(opened),{p.resolve()})
        with patch('plaintrace.binary.bounded_hash',side_effect=['a','b']),self.assertRaises(AnalysisError):analyze(shellbag_hives=[('ntuser',p)])

    def test_deterministic_mutations_raise_only_controlled_errors(self):
        original=hive_fixture(paths());rng=random.Random(909)
        for _ in range(60):
            data=bytearray(original);offset=rng.randrange(len(data));data[offset]^=rng.randrange(1,256)
            try:views,keys,rows=shellbags.analyze_hive(bytes(data),'ntuser',1,Report());json.dumps([views,keys,rows],allow_nan=False)
            except AnalysisError:pass

    def test_view_metadata_offsets_raw_values_and_slot_reuse(self):
        views,keys,rows,_=self.parse();self.assertTrue(all(int(v['record_id'])>=4096 for v in views))
        view=next(v for v in views if v['raw_values']);self.assertEqual(view['raw_values'][0]['name'],'Mode')
        self.assertEqual(view['raw_values'][0]['data_hex'],'04000000');self.assertEqual(view['key_last_write_raw'],str(FT))
        self.assertEqual(keys[-1]['bag_key_id'],keys[-2]['bag_key_id']);self.assertEqual(len(views),6)

    def test_mru_sentinel_missing_embedded_and_trailing_are_invalid(self):
        for raw in (b'',bytes(4),b'\xff'*4+bytes(4),bytes(4)+b'\xff'*8):
            _,keys,rows,_=self.parse({NT+'\\BagMRU':[shell_value(0,file_item()),value('MRUListEx',3,raw)]})
            self.assertEqual(keys[0]['mru_status'],'invalid');self.assertIsNone(rows[0]['mru_rank'])

    def test_invalid_long_name_falls_back_to_explicit_primary(self):
        raw=bytearray(file_item('SHORT',long_name='Long'));start=int.from_bytes(raw[-2:],'little');raw[start+46:start+48]=b'\0\xd8'
        _,_,rows,report=self.single(bytes(raw)+bytes(2));self.assertEqual(rows[0]['items'][0]['display_name'],'SHORT')
        self.assertEqual(rows[0]['path_candidate'],'SHORT');self.assertIn('shellbag_invalid_text',{d['code'] for d in report.diagnostics})

    def test_cli_shellbag_codepage_option_and_sqlite(self):
        p=self.file('hive',hive_fixture({NT+'\\BagMRU':[shell_value(0,file_item('경로',encoding='cp949')),mru(0)]}));out=self.folder/'korean.sqlite'
        result=subprocess.run([sys.executable,'-m','plaintrace','--shellbags-ntuser',str(p),'--shellbags-codepage','cp949','--format','sqlite','--output',str(out)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        with closing(sqlite3.connect(out)) as c:self.assertEqual(c.execute('SELECT path_candidate FROM shellbag_entries').fetchone()[0],'경로')

    def test_network_description_comments_and_non_unc_remain_literal(self):
        raw=bytearray(network());raw[4]=192;raw+=b'description\0comments\0';struct.pack_into('<H',raw,0,len(raw))
        _,_,rows,_=self.single(bytes(raw)+bytes(2));item=rows[0]['items'][0]
        self.assertEqual(item['metadata']['description'],'description');self.assertEqual(item['metadata']['comments'],'comments')
        _,_,rows,_=self.single(network('WORKGROUP',kind=0x41)+bytes(2));self.assertIsNone(rows[0]['path_candidate']);self.assertEqual(rows[0]['items'][0]['display_name'],'WORKGROUP')

        for name in ('\\\\.\\C$','\\\\?\\Volume{opaque}','\\\\server\\..'):
            _,_,rows,_=self.single(network(name)+bytes(2));self.assertIsNone(rows[0]['path_candidate'])
