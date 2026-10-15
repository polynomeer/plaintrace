"""RecentDocs names and explicit MRU state; no per-document timestamp inference."""
import json
import re
import struct
from .binary import filetime
from .evidence import AnalysisError
from .registry_hive import Hive

KEY_PATH = r'Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs'
MAX_KEYS = 1024
MAX_DOCUMENTS = 10000
MAX_OUTPUT_BYTES = 32*1024*1024


def analyze_hive(data, source_id, report):
    hive=Hive(data)
    root=hive.open(KEY_PATH)
    if root is None:
        report.warn(source_id,'recent_docs_absent','Explorer RecentDocs key is unavailable')
        return [],[]
    keys,documents=[],[]
    scopes=[(root,KEY_PATH,None)]+[(key,KEY_PATH+'\\'+key['name'],key['name']) for key in hive.children(root)]
    if len(scopes)>MAX_KEYS:raise AnalysisError('RecentDocs key limit exceeded')
    def raw_value(value):
        return dict(value_offset=value['offset']+4096,name=value['name'],type=value['type'],data_hex=value['raw'].hex())
    for key,path,category in scopes:
        key_id=str(key['offset']+4096)
        def warn(code,message,identity=key_id):report.warn(source_id,code,message,identity)
        if category is not None and key['count']:
            warn('recent_docs_nested_keys','Deeper RecentDocs subkeys are not traversed')
        values=hive.values(key)
        controls=[v for v in values if v['name'].casefold() in ('mrulistex','mrulist')]
        by_name={v['name'].casefold():v for v in controls}
        format_name=None;status='missing';order=[]
        if len(controls)==2:
            status='ambiguous'
            warn('recent_docs_ambiguous_mru','Both MRUListEx and MRUList exist; no ordering selected')
        elif controls:
            control=controls[0];raw=control['raw'];format_name='MRUListEx' if 'mrulistex' in by_name else 'MRUList'
            status='invalid'
            if format_name=='MRUListEx' and control['type']==3 and len(raw)>=4 and len(raw)%4==0:
                items=list(struct.unpack('<'+'I'*(len(raw)//4),raw))
                if items[-1]==0xffffffff and 0xffffffff not in items[:-1] and len(set(items[:-1]))==len(items)-1:
                    order=[str(item) for item in items[:-1]];status='valid'
            elif format_name=='MRUList' and control['type']==1:
                try:
                    text=raw.decode('utf-16-le')
                    if text.endswith('\0') and re.fullmatch('[a-z]*',text[:-1],re.I|re.ASCII) and len(set(text[:-1].casefold()))==len(text)-1:
                        order=list(text[:-1]);status='valid'
                except UnicodeError:pass
            if status!='valid':warn('recent_docs_invalid_mru','Wrong type, malformed/unterminated/duplicate MRU; no ranks assigned')
        else:warn('recent_docs_missing_mru','MRU control value absent; no ranks assigned')
        entries=[];others=[]
        for value in values:
            name=value['name'];numeric=bool(re.fullmatch(r'0|[1-9][0-9]{0,9}',name)) and int(name)<=0xfffffffe
            alpha=bool(re.fullmatch('[a-z]',name,re.I|re.ASCII))
            expected=numeric if format_name=='MRUListEx' else alpha if format_name=='MRUList' else numeric or alpha
            if value in controls:continue
            if expected:entries.append(value)
            else:
                others.append(raw_value(value))
                warn('recent_docs_unknown_value','Non-entry value preserved as key metadata',str(value['offset']+4096))
        entry_names={v['name'].casefold() for v in entries}
        if status=='valid':
            for name in order:
                if name.casefold() not in entry_names:warn('recent_docs_missing_entry','MRU references absent value: '+name)
        ranks={name.casefold():rank for rank,name in enumerate(order)} if status=='valid' else {}
        entries.sort(key=lambda v:(ranks.get(v['name'].casefold(),len(ranks)),v['offset']))
        for value in entries:
            if len(documents)>=MAX_DOCUMENTS:raise AnalysisError('RecentDocs document limit exceeded')
            identity=str(value['offset']+4096);raw=value['raw'];name=None;name_raw=None;tail=None
            allowed=(3,1) if format_name=='MRUList' else (3,)
            if value['type'] not in allowed:
                warn('recent_docs_wrong_entry_type','Unsupported entry type; raw value retained',identity)
            else:
                end=next((i for i in range(0,len(raw)-1,2) if raw[i:i+2]==b'\0\0'),None)
                if end is None:warn('recent_docs_unterminated_name','No aligned UTF-16 NUL; raw value retained',identity)
                else:
                    name_raw=raw[:end].hex();tail=raw[end+2:].hex()
                    try:name=raw[:end].decode('utf-16-le')
                    except UnicodeError:
                        warn('recent_docs_invalid_name','Undecodable UTF-16 name escaped; raw bytes retained',identity)
                        name=raw[:end].decode('utf-16-le',errors='backslashreplace')
                    if not name:warn('recent_docs_empty_name','Empty document name retained',identity)
                    if tail:warn('recent_docs_opaque_tail','Trailing Shell Item/other bytes remain opaque; no path inferred',identity)
            rank=ranks.get(value['name'].casefold())
            if status=='valid' and rank is None:warn('recent_docs_unlisted_entry','Entry absent from MRU; no rank assigned',identity)
            documents.append(dict(source_id=source_id,record_id=identity,key_id=key_id,key_path=path,category=category,
                                  value_name=value['name'],value_type=value['type'],mru_rank=rank,document_name=name,
                                  name_utf16_hex=name_raw,trailing_data_hex=tail,value_data_hex=raw.hex()))
        keys.append(dict(source_id=source_id,record_id=key_id,key_path=path,category=category,
                         key_last_written=filetime(key['ticks'],report,source_id,key_id),key_last_write_raw=str(key['ticks']),
                         mru_format=format_name,mru_status=status,mru_order=order,mru_values=[raw_value(v) for v in controls],other_values=others))
    if len(json.dumps([keys,documents],ensure_ascii=False).encode('utf-8'))>MAX_OUTPUT_BYTES:
        raise AnalysisError('RecentDocs output limit exceeded')
    return keys,documents
