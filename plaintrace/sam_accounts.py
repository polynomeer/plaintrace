"""Offline SAM account metadata; no credentials, boot keys or hash decryption."""
from collections import Counter
import hashlib
import json
import re
from .binary import filetime
from .evidence import AnalysisError
from .registry_hive import Hive

BASE = r'SAM\Domains\Account\Users'
MAX_ACCOUNTS = 4096
MAX_MAPPINGS = 4096
MAX_VALUES = 16384
MAX_STRING_UNITS = 4096
MAX_OUTPUT_BYTES = 32*1024*1024
STRINGS = (('username',12),('full_name',24),('admin_comment',36),('user_comment',48),
           ('home_directory',72),('home_drive',84),('logon_script',96),('profile_path',108),('workstations',120))
FLAGS = {1:'disabled',4:'password_not_required',16:'normal_account',512:'password_never_expires',1024:'auto_locked'}


def analyze_hive(data, source_id, report):
    hive=Hive(data);root=hive.open(BASE)
    if root is None:
        report.warn(source_id,'sam_accounts_absent','SAM account Users root unavailable')
        return [],[]
    accounts,mappings=[],[]
    total_values=0

    def warn(code,message,identity=None):
        report.warn(source_id,'sam_accounts_'+code,message,identity)

    def values(key):
        nonlocal total_values
        result=hive.values(key);total_values+=len(result)
        if total_values>MAX_VALUES:raise AnalysisError('SAM observed value limit exceeded')
        return result

    def summary(value):
        return dict(value_offset=value['offset']+4096,name=value['name'],type=value['type'],
                    byte_length=len(value['raw']),sha256=hashlib.sha256(value['raw']).hexdigest())

    def record(value,which):
        if value is None:return dict(status='missing',value_offset=None,type=None,byte_length=None,sha256=None,**({'data_hex':None} if which=='F' else {}))
        result=summary(value);result.pop('name');result['status']='wrong_type' if value['type']!=3 else 'wrong_size' if (len(value['raw'])!=80 if which=='F' else len(value['raw'])<204) else 'parsed' if which=='F' else 'partial_strings'
        if which=='F':result['data_hex']=value['raw'].hex() if result['status']=='parsed' else None
        return result

    children=hive.children(root)
    names=next((k for k in children if k['name'].casefold()=='names'),None)
    candidates=[k for k in children if re.fullmatch('[0-9a-fA-F]{8}',k['name'],re.ASCII)]
    if len(candidates)>MAX_ACCOUNTS:raise AnalysisError('SAM account limit exceeded')
    candidate_offsets={key['offset'] for key in candidates}
    for key in children:
        if key is not names and key['offset'] not in candidate_offsets:warn('unsupported_key','Unsupported Users child: '+key['name'],str(key['offset']+4096))
    if root['value_count']:warn('root_values','Users container values are outside the account adapter',str(root['offset']+4096))
    for key in candidates:
        identity=str(key['offset']+4096);rid=int(key['name'],16);path=BASE+'\\'+key['name']
        if key['count']:warn('nested_keys','Account descendants not traversed',identity)
        vals=values(key);f=next((v for v in vals if v['name'].casefold()=='f'),None);v=next((v for v in vals if v['name'].casefold()=='v'),None)
        fr,vr=record(f,'F'),record(v,'V');fixed={};times=[];strings=[]
        for label,meta in (('F',fr),('V',vr)):
            if meta['status'] not in ('parsed','partial_strings'):warn('unsupported_record',label+' record '+meta['status']+'; no layout guessing',identity)
        if fr['status']=='parsed':
            raw=f['raw'];u=lambda offset,width:int.from_bytes(raw[offset:offset+width],'little')
            flags=u(56,2)
            fixed=dict(rid_raw=u(48,4),primary_group_rid_raw=u(52,4),flags_raw=flags,
                       flag_labels=[label for bit,label in FLAGS.items() if flags&bit],unknown_flag_bits=flags&~sum(FLAGS),
                       country_code_raw=u(60,2),codepage_raw=u(62,2),bad_password_count_raw=u(64,2),logon_count_raw=u(66,2))
            if fixed['rid_raw']!=rid:warn('rid_mismatch','F RID differs from RID key; both retained',identity)
            for name,offset in (('last_logon',8),('password_last_set',24),('last_bad_password',40)):
                ticks=u(offset,8)
                state='unset' if ticks==0 else 'sentinel' if ticks in (0x7fffffffffffffff,0xffffffffffffffff) else 'value'
                stamp=filetime(ticks,report,source_id,identity) if state=='value' else None
                if state=='value' and stamp is None:state='out_of_range'
                times.append(dict(field=name,offset=offset,filetime_raw=str(ticks),time=stamp,state=state))
        if vr['status']=='partial_strings':
            raw=v['raw'];spans=[]
            for name,descriptor in STRINGS:
                relative=int.from_bytes(raw[descriptor:descriptor+4],'little');length=int.from_bytes(raw[descriptor+4:descriptor+8],'little');offset=204+relative
                item=dict(field=name,descriptor_offset=descriptor,relative_offset=relative,byte_length=length,data_offset=offset,
                          descriptor_hex=raw[descriptor:descriptor+8].hex(),status=None,text=None,utf16_hex=None)
                if length>2*MAX_STRING_UNITS:raise AnalysisError('SAM string limit exceeded')
                if offset>len(raw) or length>len(raw)-offset:
                    item['status']='invalid_bounds';warn('invalid_string','V string outside value: '+name,identity)
                elif offset%2 or length%2:
                    item['status']='invalid_alignment';warn('invalid_string','Unaligned V UTF-16 field: '+name,identity)
                else:
                    item['utf16_hex']=raw[offset:offset+length].hex()
                    try:
                        item['text']=raw[offset:offset+length].decode('utf-16-le');item['status']='parsed' if length else 'empty'
                    except UnicodeError:
                        item['text']=raw[offset:offset+length].decode('utf-16-le',errors='backslashreplace');item['status']='invalid_text'
                        warn('invalid_text','V string Unicode escaped: '+name,identity)
                    if item['text'] and '\0' in item['text']:
                        if item['status']!='invalid_text':item['status']='embedded_nul'
                        warn('embedded_nul','Length-framed string includes NUL: '+name,identity)
                    if length:
                        if any(offset<end and start<offset+length for start,end in spans):warn('overlapping_strings','V string ranges overlap: '+name,identity)
                        spans.append((offset,offset+length))
                strings.append(item)
        others=[summary(x) for x in vals if x is not f and x is not v]
        if others:warn('other_values','Other account values summarized without content decoding',identity)
        accounts.append(dict(source_id=source_id,record_id=identity,key_path=path,rid_key=rid,
                             key_last_written=filetime(key['ticks'],report,source_id,identity),key_last_write_raw=str(key['ticks']),
                             f_record=fr,v_record=vr,fixed_fields=fixed,times=times,strings=strings,other_values=others))
    by_rid={a['rid_key']:a for a in accounts}
    if names is None:warn('names_absent','Names mapping root unavailable')
    else:
        if names['value_count']:warn('root_values','Names container values not decoded',str(names['offset']+4096))
        namekeys=hive.children(names)
        if len(namekeys)>MAX_MAPPINGS:raise AnalysisError('SAM name mapping limit exceeded')
        for key in namekeys:
            identity=str(key['offset']+4096);vals=values(key);default=next((v for v in vals if v['name']==''),None)
            valid=default is not None and not default['raw'];rid=default['type'] if valid else None
            account=by_rid.get(rid);status='linked' if account else 'orphan' if valid else 'invalid'
            if key['count']:warn('nested_keys','Name mapping descendants not traversed',identity)
            if status!='linked':warn('mapping_'+status,'Name mapping '+status+'; no invented account',identity)
            if account:
                username=next((s for s in account['strings'] if s['field']=='username' and s['status']=='parsed'),None)
                if username and username['text'].casefold()!=key['name'].casefold():warn('name_mismatch','Names label differs from V username; no label selected',identity)
            mappings.append(dict(source_id=source_id,record_id=identity,key_path=BASE+'\\'+names['name']+'\\'+key['name'],
                                 account_name=key['name'],rid_reference=rid,account_id=account['record_id'] if account else None,status=status,
                                 key_last_written=filetime(key['ticks'],report,source_id,identity),key_last_write_raw=str(key['ticks']),values=[summary(x) for x in vals]))
        linked=[m['rid_reference'] for m in mappings if m['status']=='linked']
        for rid,count in Counter(linked).items():
            if count>1:warn('duplicate_mapping','Several Names labels reference RID '+str(rid),by_rid[rid]['record_id'])
    referenced={m['account_id'] for m in mappings if m['account_id'] is not None}
    for a in accounts:
        if a['record_id'] not in referenced:warn('unmapped_account','RID key has no valid Names reference',a['record_id'])
    if not accounts:warn('no_accounts','No supported RID keys found')
    if len(json.dumps([accounts,mappings],ensure_ascii=False).encode('utf-8'))>MAX_OUTPUT_BYTES:raise AnalysisError('SAM output limit exceeded')
    return accounts,mappings
