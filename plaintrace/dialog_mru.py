"""Acquired Common Dialog PIDL MRUs; stored references, not proven open/save events."""
import codecs
import json
import struct
from .binary import filetime
from .evidence import AnalysisError
from .model import Report
from .registry_hive import Hive
from . import shell_items
from .shellbags import canonical,compose

BASE=r'Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32'
OPEN_SAVE='OpenSavePidlMRU'
LAST_VISITED='LastVisitedPidlMRU'
MAX_KEYS=1024
MAX_ENTRIES=10000
MAX_APP_UNITS=4096
MAX_PATH_CHARS=32768
MAX_OUTPUT_BYTES=64*1024*1024


def analyze_hive(data,source_id,report,codepage='cp1252'):
    try:
        codecs.lookup(codepage)
        if '\0'.encode(codepage)!=b'\0':raise ValueError('not ANSI-compatible')
    except (LookupError,ValueError) as error:raise AnalysisError('Invalid dialog MRU codepage: '+codepage) from error
    hive=Hive(data);keys=[];entries=[];scopes=[]
    def warn(code,message,identity=None):report.warn(source_id,code,message,identity)
    def raw(value):return dict(value_offset=value['offset']+4096,name=value['name'],type=value['type'],data_hex=value['raw'].hex())
    def forward(local):
        for diagnostic in local.diagnostics:
            diagnostic['code']=diagnostic['code'].replace('shellbag_','dialog_mru_',1)
            report.diagnostics.append(diagnostic)
    for kind in (OPEN_SAVE,LAST_VISITED):
        path=BASE+'\\'+kind;root=hive.open(path)
        if root is None:
            warn('dialog_mru_absent','Common Dialog branch unavailable: '+kind);continue
        scopes.append((root,path,kind,None,None))
        children=hive.children(root)
        if kind==OPEN_SAVE:
            if len(scopes)+len(children)>MAX_KEYS:raise AnalysisError('Dialog MRU key limit')
            for child in children:scopes.append((child,path+'\\'+child['name'],kind,child['name'],str(root['offset']+4096)))
        elif children:warn('dialog_mru_nested_keys','LastVisited subkeys are unsupported and not traversed',str(root['offset']+4096))
    for key,path,kind,category,parent in scopes:
        if len(keys)>=MAX_KEYS:raise AnalysisError('Dialog MRU key limit')
        identity=str(key['offset']+4096);values=hive.values(key)
        if category is not None and hive.children(key):warn('dialog_mru_nested_keys','Deeper OpenSave scopes are unsupported and not traversed',identity)
        controls=[v for v in values if v['name'].casefold() in ('mrulistex','mrulist')]
        numeric=[v for v in values if canonical(v['name'])];status='missing';order=[]
        if kind==OPEN_SAVE and category is None and not controls and not numeric:status='container'
        elif len(controls)>1:status='ambiguous';warn('dialog_mru_ambiguous_mru','Multiple ordering controls; no ranks assigned',identity)
        elif controls:
            control=controls[0];value_bytes=control['raw'];status='invalid'
            if control['name'].casefold()=='mrulistex' and control['type']==3 and len(value_bytes)>=4 and len(value_bytes)%4==0:
                numbers=struct.unpack('<'+'I'*(len(value_bytes)//4),value_bytes)
                if numbers[-1]==0xffffffff and 0xffffffff not in numbers[:-1] and len(set(numbers[:-1]))==len(numbers)-1:
                    order=[str(n) for n in numbers[:-1]];status='valid'
            if status!='valid':warn('dialog_mru_invalid_mru','Unsupported/malformed MRU control retained; no ranks assigned',identity)
        else:warn('dialog_mru_missing_mru','MRUListEx missing; no ranks assigned',identity)
        ranks={name:rank for rank,name in enumerate(order)} if status=='valid' else {}
        names={v['name'] for v in numeric}
        for name in order:
            if name not in names:warn('dialog_mru_missing_entry','MRU references absent value: '+name,identity)
        others=[v for v in values if v not in controls and not canonical(v['name'])]
        for value in others:warn('dialog_mru_unknown_value','Noncanonical/non-entry value retained as metadata',str(value['offset']+4096))
        keys.append(dict(source_id=source_id,record_id=identity,key_path=path,list_kind=kind,category=category,parent_key_id=parent,
                         key_last_written=filetime(key['ticks'],report,source_id,identity),key_last_write_raw=str(key['ticks']),
                         mru_status=status,mru_order=order,control_values=[raw(v) for v in controls],other_values=[raw(v) for v in others]))
        for value in numeric:
            if len(entries)>=MAX_ENTRIES:raise AnalysisError('Dialog MRU entry limit')
            value_id=str(value['offset']+4096);data_raw=value['raw'];application=None;app_hex=None;app_valid=None
            offset=None;pidl=None;pidl_status='wrong_type';items=[];terminated=False;tail=None;candidate=None;basis=None;complete=False
            if value['type']!=3:warn('dialog_mru_wrong_type','Numeric entry is not REG_BINARY; raw bytes retained',value_id)
            else:
                offset=0
                if kind==LAST_VISITED:
                    end=next((i for i in range(0,len(data_raw)-1,2) if data_raw[i:i+2]==b'\0\0'),None)
                    if end is None:
                        offset=None;pidl_status='invalid_prefix';warn('dialog_mru_unterminated_application','No aligned UTF-16 application terminator; PIDL start not guessed',value_id)
                    else:
                        if end//2>MAX_APP_UNITS:raise AnalysisError('Dialog MRU application name limit')
                        app_hex=data_raw[:end].hex();offset=end+2
                        try:application=data_raw[:end].decode('utf-16-le');app_valid=bool(application)
                        except UnicodeError:
                            application=data_raw[:end].decode('utf-16-le',errors='backslashreplace');app_valid=False
                            warn('dialog_mru_invalid_application','Invalid application UTF-16 escaped; no verified attribution',value_id)
                        if application=='':warn('dialog_mru_empty_application','Empty application label retained without attribution',value_id)
                if offset is not None:
                    pidl=data_raw[offset:];local=Report()
                    try:
                        items,terminated,tail,valid=shell_items.parse(pidl,codepage,local,source_id,value_id)
                        pidl_status='parsed' if items else 'empty'
                        if not terminated:
                            pidl_status='unterminated';warn('dialog_mru_unterminated_pidl','PIDL lacks terminal item; decoded components retained without path',value_id)
                        if tail:pidl_status='trailing'
                        candidate,basis,complete=compose((None,None,True),items,valid and terminated,local,source_id,value_id)
                        if candidate is not None and len(candidate)>MAX_PATH_CHARS:raise AnalysisError('Dialog MRU path character limit')
                    except shell_items.InvalidShellItem as error:
                        pidl_status='malformed';warn('dialog_mru_malformed_pidl',str(error),value_id)
                    finally:forward(local)
            rank=ranks.get(value['name'])
            if status=='valid' and rank is None:warn('dialog_mru_unlisted_entry','Entry absent from MRU; no rank assigned',value_id)
            entries.append(dict(source_id=source_id,record_id=value_id,key_id=identity,key_path=path,list_kind=kind,category=category,value_name=value['name'],value_type=value['type'],mru_rank=rank,
                                application_name=application,application_utf16_hex=app_hex,application_name_valid=app_valid,pidl_offset=offset,pidl_hex=pidl.hex() if pidl is not None else None,
                                pidl_status=pidl_status,items=items,item_list_terminated=terminated,item_trailing_hex=tail,path_candidate=candidate,path_basis=basis,
                                ancestry_complete=complete,value_data_hex=data_raw.hex()))
    if len(json.dumps([keys,entries],ensure_ascii=False).encode('utf-8'))>MAX_OUTPUT_BYTES:raise AnalysisError('Dialog MRU output limit')
    return keys,entries
