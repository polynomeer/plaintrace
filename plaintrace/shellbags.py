"""Acquired BagMRU hierarchies and same-hive Bags references, without access claims."""
import codecs
import json
import re
import struct
from .binary import filetime
from .evidence import AnalysisError
from .registry_hive import Hive
from . import shell_items

MAX_KEYS=5000
MAX_ENTRIES=10000
MAX_VIEW_KEYS=5000
MAX_DEPTH=128
MAX_PATH_CHARS=32768
MAX_OUTPUT_BYTES=64*1024*1024
ROOTS={
    'ntuser':tuple(prefix+'\\'+name for prefix in (r'Software\Microsoft\Windows',r'Software\Classes\Local Settings\Software\Microsoft\Windows',r'Software\Classes\Wow6432Node\Local Settings\Software\Microsoft\Windows') for name in ('Shell','ShellNoRoam')),
    'usrclass':tuple(prefix+'\\'+name for prefix in (r'Local Settings\Software\Microsoft\Windows',r'Wow6432Node\Local Settings\Software\Microsoft\Windows') for name in ('Shell','ShellNoRoam')),
}


def canonical(name):return bool(re.fullmatch(r'0|[1-9][0-9]{0,9}',name)) and int(name)<=0xfffffffe


def unc_anchor(name):
    parts=name.split('\\')
    return len(parts)==4 and parts[:2]==['',''] and all(part and part not in ('.','..') and not any(c in part for c in '/:\0<>"|?*') for part in parts[2:])


def compose(prefix,items,valid,report,source_id,identity):
    """Only explicit stored anchors reset an unresolved prefix; never normalize paths."""
    candidate,basis,complete=prefix
    for item in items:
        name=item['path_component'];kind=item['component_kind']
        if name is None: candidate=None;complete=False;continue
        if kind=='volume' and re.fullmatch(r'[A-Za-z]:\\',name):candidate=name;basis='stored_volume_hierarchy';complete=True
        elif kind=='network' and unc_anchor(name):candidate=name;basis='stored_unc_hierarchy';complete=True
        elif kind=='namespace':
            candidate=(candidate.rstrip('\\')+'\\' if complete and candidate else '')+name if complete else None
            basis='shell_namespace_hierarchy'
        elif kind=='name' and name not in ('.','..') and not any(c in name for c in '\\/:\0'):
            candidate=(candidate.rstrip('\\')+'\\' if complete and candidate else '')+name if complete else None
            if basis is None:basis='relative_hierarchy'
        else:
            candidate=None;complete=False
            report.warn(source_id,'shellbag_uncomposed_component','Component is not an unambiguous path segment/anchor',identity)
        if candidate is not None and len(candidate)>MAX_PATH_CHARS:raise AnalysisError('ShellBags path character limit')
    if not valid:candidate=None;complete=False
    return candidate,basis if candidate is not None else None,complete


def analyze_hive(data,role,source_id,report,codepage='cp1252'):
    if role not in ROOTS:raise AnalysisError('Unsupported ShellBags hive role')
    try:
        codecs.lookup(codepage)
        if '\0'.encode(codepage)!=b'\0':raise ValueError('not ANSI-compatible')
    except (LookupError,ValueError) as error:raise AnalysisError('Invalid ShellBags codepage: '+codepage) from error
    hive=Hive(data);keys=[];entries=[];views=[];seen=set();view_seen=set();view_cache={};found=False
    def warn(code,message,identity=None):report.warn(source_id,code,message,identity)
    def raw(value):return dict(value_offset=value['offset']+4096,name=value['name'],type=value['type'],data_hex=value['raw'].hex())
    def view_tree(path,shell_root,slot):
        if path in view_cache:return view_cache[path]
        root=hive.open(path)
        if root is None:view_cache[path]=None;return None
        root_id=str(root['offset']+4096);stack=[(root,path,None,0)]
        while stack:
            key,key_path,parent,depth=stack.pop();identity=str(key['offset']+4096)
            if depth>MAX_DEPTH:raise AnalysisError('ShellBags view depth limit')
            if key['offset'] in view_seen:raise AnalysisError('ShellBags repeated view key')
            view_seen.add(key['offset'])
            if len(views)>=MAX_VIEW_KEYS:raise AnalysisError('ShellBags view key limit')
            views.append(dict(source_id=source_id,record_id=identity,hive_role=role,shell_root=shell_root,key_path=key_path,parent_key_id=parent,
                              slot_name=slot,key_last_written=filetime(key['ticks'],report,source_id,identity),key_last_write_raw=str(key['ticks']),raw_values=[raw(v) for v in hive.values(key)]))
            for child in reversed(hive.children(key)):stack.append((child,key_path+'\\'+child['name'],identity,depth+1))
        view_cache[path]=root_id;return root_id
    for shell_root in ROOTS[role]:
        root_path=shell_root+'\\BagMRU';root=hive.open(root_path)
        if root is None:continue
        found=True;stack=[(root,root_path,None,None,[],(None,None,True))]
        while stack:
            key,path,parent,parent_entry,slots,prefix=stack.pop();identity=str(key['offset']+4096)
            if len(slots)>MAX_DEPTH:raise AnalysisError('ShellBags hierarchy depth limit')
            if key['offset'] in seen:raise AnalysisError('ShellBags repeated hierarchy key')
            seen.add(key['offset'])
            if len(keys)>=MAX_KEYS:raise AnalysisError('ShellBags hierarchy key limit')
            values=hive.values(key);by_name={v['name'].casefold():v for v in values}
            controls=[v for v in values if v['name'].casefold() in ('mrulistex','mrulist')]
            status='missing';order=[]
            if len(controls)>1:status='ambiguous';warn('shellbag_ambiguous_mru','Multiple ordering controls; no ranks assigned',identity)
            elif controls:
                control=controls[0];data_raw=control['raw'];status='invalid'
                if control['name'].casefold()=='mrulistex' and control['type']==3 and len(data_raw)>=4 and len(data_raw)%4==0:
                    numbers=struct.unpack('<'+'I'*(len(data_raw)//4),data_raw)
                    if numbers[-1]==0xffffffff and 0xffffffff not in numbers[:-1] and len(set(numbers[:-1]))==len(numbers)-1:
                        order=[str(n) for n in numbers[:-1]];status='valid'
                if status!='valid':warn('shellbag_invalid_mru','Unsupported/malformed MRU; raw control retained without ranks',identity)
            else:warn('shellbag_missing_mru','MRUListEx missing; no ranks assigned',identity)
            ranks={name:rank for rank,name in enumerate(order)} if status=='valid' else {}
            numeric=[v for v in values if canonical(v['name'])];numbers={v['name'] for v in numeric}
            for name in order:
                if name not in numbers:warn('shellbag_missing_entry','MRU references missing value: '+name,identity)
            node_slot=None;bag_key_id=None;node=by_name.get('nodeslot')
            if node is not None:
                if node['type']==4 and len(node['raw'])==4:
                    node_slot=int.from_bytes(node['raw'],'little');bag_key_id=view_tree(shell_root+'\\Bags\\'+str(node_slot),shell_root,str(node_slot))
                    if bag_key_id is None:warn('shellbag_missing_bag','NodeSlot has no same-root Bags key',identity)
                else:warn('shellbag_invalid_nodeslot','NodeSlot is not an exact REG_DWORD; no Bags reference',identity)
            children=hive.children(key);numeric_children={c['name']:c for c in children if canonical(c['name'])}
            row_by_name={}
            for value in numeric:
                if len(entries)>=MAX_ENTRIES:raise AnalysisError('ShellBags entry limit')
                value_id=str(value['offset']+4096);items=[];terminated=False;trailing=None;valid=False;item_status="wrong_type"
                if value['type']!=3:warn('shellbag_wrong_item_type','Numeric value is not REG_BINARY; raw bytes retained',value_id)
                else:
                    try:
                        items,terminated,trailing,valid=shell_items.parse(value['raw'],codepage,report,source_id,value_id)
                        item_status='parsed' if items else 'empty'
                    except shell_items.InvalidShellItem as error:
                        item_status='malformed';warn('shellbag_malformed_item',str(error),value_id)
                composed=compose(prefix,items,valid,report,source_id,value_id)
                if status=='valid' and value['name'] not in ranks:warn('shellbag_unlisted_entry','Numeric value absent from MRU; no rank assigned',value_id)
                child=numeric_children.get(value['name'])
                row=dict(source_id=source_id,record_id=value_id,key_id=identity,hive_role=role,shell_root=shell_root,key_path=path,value_name=value['name'],value_type=value['type'],
                         mru_rank=ranks.get(value['name']),child_key_id=str(child['offset']+4096) if child else None,item_status=item_status,items=items,item_list_terminated=terminated,item_trailing_hex=trailing,
                         path_candidate=composed[0],path_basis=composed[1],ancestry_complete=composed[2],value_data_hex=value['raw'].hex())
                row_by_name[value['name']]=(row,composed);entries.append(row)
            keys.append(dict(source_id=source_id,record_id=identity,hive_role=role,shell_root=shell_root,key_path=path,parent_key_id=parent,parent_entry_id=parent_entry,
                             depth=len(slots),hierarchy_slots=slots,path_candidate=prefix[0],path_basis=prefix[1],ancestry_complete=prefix[2],
                             key_last_written=filetime(key['ticks'],report,source_id,identity),key_last_write_raw=str(key['ticks']),mru_status=status,mru_order=order,
                             control_values=[raw(v) for v in controls],node_slot=node_slot,bag_key_id=bag_key_id,other_values=[raw(v) for v in values if v not in controls and not canonical(v['name'])]))
            for child in reversed(children):
                if not canonical(child['name']):warn('shellbag_noncanonical_child','Noncanonical BagMRU child not traversed: '+child['name'],str(child['offset']+4096));continue
                row_context=row_by_name.get(child['name']);child_entry=None;child_prefix=(None,None,False)
                if row_context:child_entry=row_context[0]['record_id'];child_prefix=row_context[1]
                else:warn('shellbag_missing_parent_value','Child key lacks a matching numeric value; ancestry unresolved',str(child['offset']+4096))
                stack.append((child,path+'\\'+child['name'],identity,child_entry,slots+[child['name']],child_prefix))
    if not found:warn('shellbags_absent','No supported BagMRU roots in the supplied hive role')
    if len(json.dumps([views,keys,entries],ensure_ascii=False).encode('utf-8'))>MAX_OUTPUT_BYTES:raise AnalysisError('ShellBags output limit')
    return views,keys,entries
