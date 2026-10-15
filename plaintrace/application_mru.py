"""Application registry MRUs with raw lineage, not inferred document usage."""
import json
import re
from .binary import filetime
from .evidence import AnalysisError
from .registry_hive import Hive

MAX_KEYS=1024
MAX_ENTRIES=10000
MAX_OUTPUT_BYTES=32*1024*1024
VERSION=re.compile(r'[0-9]{1,2}\.[0-9]{1,2}')


def analyze_hive(data,source_id,report):
    hive=Hive(data);keys=[];entries=[];seen=set()
    def warn(code,message,identity=None):report.warn(source_id,code,message,identity)
    def raw_value(value):
        return dict(value_offset=value['offset']+4096,name=value['name'],type=value['type'],data_hex=value['raw'].hex())
    def children(key):
        result=hive.children(key)
        if len(result)>4096:raise AnalysisError('Application MRU discovery breadth exceeded')
        return result
    def decode(value,family):
        identity=str(value['offset']+4096);raw=value['raw']
        if value['type'] not in ((1,2,3) if family=='hwp' else (1,2)):
            warn('app_mru_wrong_type','Unsupported path value type; raw retained',identity)
            return None,False
        if family=='hwp' and value['type']==3:
            if raw.startswith(b'\xfe\xff'):
                warn('app_mru_wrong_encoding','Big-endian HWP binary path unsupported; raw retained',identity)
                return None,False
            if raw.startswith(b'\xff\xfe'):raw=raw[2:]
        try:text=raw.decode('utf-16-le')
        except UnicodeError:
            warn('app_mru_invalid_text','Invalid UTF-16 path escaped without interpretation',identity)
            return raw.decode('utf-16-le',errors='backslashreplace'),False
        if not text.endswith('\0'):warn('app_mru_unterminated_text','Registry string lacks NUL; decoded text retained',identity)
        text=text.rstrip('\0')
        if '\0' in text:
            warn('app_mru_embedded_nul','Embedded NUL in path text; no path selected',identity)
            return text,False
        return text,True
    def office(text,identity):
        tokens=[];ticks=None;time=None
        if not text.startswith('['):return text,'plain_value',tokens,ticks,time
        match=re.match(r'((?:\[[A-Za-z][^\]\r\n]*\])+)\*',text)
        if not match:
            warn('app_mru_invalid_office_prefix','Unrecognized Office metadata prefix; raw text retained',identity)
            return None,'unparsed_office_metadata',tokens,ticks,time
        for tag,body in re.findall(r'\[([A-Za-z])([^\]]*)\]',match[1]):tokens.append(dict(tag=tag,raw=body))
        times=[item['raw'] for item in tokens if item['tag'].upper()=='T']
        if len(times)==1 and re.fullmatch('[0-9A-Fa-f]{16}',times[0]):
            ticks=str(int(times[0],16));time=filetime(int(ticks),report,source_id,identity)
        elif times:warn('app_mru_invalid_office_time','Ambiguous/invalid Office T token; no time selected',identity)
        return text[match.end():],'office_metadata',tokens,ticks,time
    def emit(key,path,family,app,version,scope,kind,role='list'):
        if key['offset'] in seen:raise AnalysisError('Application MRU repeated key reference')
        seen.add(key['offset'])
        if len(keys)>=MAX_KEYS:raise AnalysisError('Application MRU key limit exceeded')
        key_id=str(key['offset']+4096);metadata=[]
        if not (family=='adobe' and role=='list') and children(key):
            warn('app_mru_nested_keys','Nested list/slot keys are unsupported and not traversed',key_id)
        values=hive.values(key)
        for value in values:
            name=value['name'];match=None
            if family=='office':match=re.fullmatch(r'Item ([1-9][0-9]{0,8})',name,re.I|re.ASCII)
            elif family=='hwp':match=re.fullmatch(r'file(0|[1-9][0-9]{0,8})',name,re.I|re.ASCII)
            elif role=='slot' and name.casefold()=='tditext':match=True
            if not match:
                metadata.append(raw_value(value));continue
            if len(entries)>=MAX_ENTRIES:raise AnalysisError('Application MRU entry limit exceeded')
            identity=str(value['offset']+4096)
            slot_number=int(match[1]) if family!='adobe' else int(key['name'][1:])
            text,valid=decode(value,family);candidate=None;basis='unavailable';tokens=[];ticks=None;time=None
            if valid:
                if family=='office':candidate,basis,tokens,ticks,time=office(text,identity)
                else:candidate,basis=text,'adobe_device_independent' if family=='adobe' else 'plain_value'
            if candidate=='':warn('app_mru_empty_path','Empty stored path retained',identity)
            entries.append(dict(source_id=source_id,record_id=identity,key_id=key_id,key_path=path,family=family,
                                application=app,application_version=version,scope=scope,list_kind=kind,
                                slot_name=key['name'] if family=='adobe' else name,slot_number=slot_number,
                                value_name=name,value_type=value['type'],raw_text=text,stored_path=candidate,path_basis=basis,
                                metadata_tokens=tokens,embedded_filetime_raw=ticks,embedded_at=time,value_data_hex=value['raw'].hex()))
        keys.append(dict(source_id=source_id,record_id=key_id,key_path=path,family=family,application=app,
                         application_version=version,scope=scope,list_kind=kind,key_role=role,
                         key_last_written=filetime(key['ticks'],report,source_id,key_id),key_last_write_raw=str(key['ticks']),
                         metadata_values=metadata))
        if role=='slot' and not any(v['name'].casefold()=='tditext' for v in values):
            warn('app_mru_missing_path','Adobe slot lacks tDIText; key metadata retained',key_id)
    def take(path,*context):
        key=hive.open(path)
        if key is not None:emit(key,path,*context)
    office_root=r'Software\Microsoft\Office'
    root=hive.open(office_root)
    if root:
        for version in children(root):
            if not VERSION.fullmatch(version['name']):continue
            for app in ('Word','Excel','PowerPoint'):
                base=office_root+'\\'+version['name']+'\\'+app
                for kind in ('File MRU','Place MRU'):
                    take(base+'\\'+kind,'office',app,version['name'],None,kind)
                users=hive.open(base+'\\User MRU')
                if users:
                    for user in children(users):
                        for kind in ('File MRU','Place MRU'):
                            take(base+'\\User MRU\\'+user['name']+'\\'+kind,'office',app,version['name'],user['name'],kind)
    else:warn('app_mru_family_absent','Office registry branch unavailable')
    hwp_found=False
    for product,frames in (('Hwp',('HwpFrame_KOR','HwpFrame')),('Common',('CommonFrame',))):
        base='Software\\Hnc\\'+product;root=hive.open(base)
        if root:
            hwp_found=True
            for version in children(root):
                if VERSION.fullmatch(version['name']):
                    for frame in frames:take(base+'\\'+version['name']+'\\'+frame+'\\RecentFile','hwp','HWP',version['name'],frame,'RecentFile')
    if not hwp_found:warn('app_mru_family_absent','HWP registry branches unavailable')
    adobe_found=False
    for product in ('Acrobat Reader','Adobe Acrobat'):
        base='Software\\Adobe\\'+product;root=hive.open(base)
        if root:
            adobe_found=True
            for version in children(root):
                path=base+'\\'+version['name']+'\\AVGeneral\\cRecentFiles';recent=hive.open(path)
                if recent:
                    emit(recent,path,'adobe',product,version['name'],None,'cRecentFiles')
                    for slot in children(recent):
                        if re.fullmatch(r'c[1-9][0-9]{0,8}',slot['name'],re.I|re.ASCII):
                            emit(slot,path+'\\'+slot['name'],'adobe',product,version['name'],None,'cRecentFiles','slot')
                        else:warn('app_mru_unknown_adobe_slot','Noncanonical Adobe slot key not interpreted',str(slot['offset']+4096))
    if not adobe_found:warn('app_mru_family_absent','Adobe registry branches unavailable')
    if not keys:warn('app_mru_no_lists','No supported application MRU lists found')
    if len(json.dumps([keys,entries],ensure_ascii=False).encode('utf-8'))>MAX_OUTPUT_BYTES:raise AnalysisError('Application MRU output limit exceeded')
    return keys,entries
