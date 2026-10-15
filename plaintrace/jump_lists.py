"""Active Jump Lists with bounded containers and explicit in-container lineage."""
from collections import Counter
import codecs
import hashlib
import json
import re
import uuid
from . import compound,lnk
from .binary import Binary,filetime
from .evidence import AnalysisError
from .model import Report

MAX_JUMP_BYTES=compound.MAX_BYTES
MAX_ENTRIES=10000
MAX_CATEGORIES=1024
MAX_LINK_BYTES=1024*1024
MAX_PATH_UNITS=32768
MAX_OUTPUT_BYTES=64*1024*1024
FOOTER=0xbabffbab


def link_length(data,start,body_only=False):
    """Walk declared LNK sections, never search for CLSIDs or footer signatures."""
    b=Binary(data,'embedded LNK');header=72 if body_only else 76;b.take(start,header)
    if (not body_only and b.number(start,4)!=76) or b.take(start+(0 if body_only else 4),16)!=lnk.CLSID:
        raise AnalysisError('Unsupported custom shell object/header')
    flags=b.number(start+(16 if body_only else 20),4);cursor=start+header
    if flags&1:cursor+=2+b.number(cursor,2);b.take(cursor,0)
    if flags&2:
        size=b.number(cursor,4)
        if size<28:raise AnalysisError('Embedded LNK LinkInfo size invalid')
        if cursor+size-start>MAX_LINK_BYTES:raise AnalysisError('Embedded LNK size limit')
        b.take(cursor,size);cursor+=size
    for flag in (4,8,16,32,64):
        if flags&flag:
            length=b.number(cursor,2);cursor+=2+length*(2 if flags&128 else 1);b.take(cursor,0)
    while True:
        if cursor-start>MAX_LINK_BYTES:raise AnalysisError('Embedded LNK size limit')
        size=b.number(cursor,4)
        if size==0:cursor+=4;break
        if size<8:raise AnalysisError('Embedded LNK ExtraData size invalid')
        if cursor+size-start>MAX_LINK_BYTES:raise AnalysisError('Embedded LNK size limit')
        b.take(cursor,size);cursor+=size
    if cursor-start>MAX_LINK_BYTES:raise AnalysisError('Embedded LNK size limit')
    return cursor-start


def parse(data,source_id,report,codepage='cp1252'):
    if len(data)>MAX_JUMP_BYTES:raise AnalysisError('Jump List input limit exceeded')
    try:
        codecs.lookup(codepage)
        if "\0".encode(codepage)!=b"\0":raise ValueError('not ANSI-compatible')
    except (LookupError,ValueError) as error:raise AnalysisError('Invalid LNK codepage: '+codepage) from error
    b=Binary(data,'Jump List');rows=[]
    summary=dict(source_id=source_id,record_id='container',container_kind=None,version=None,header_hex=None,container_header_hex=None,
                 app_id_hint=None,declared_entries=None,declared_pinned=None,streams=[],categories=[],trailing_data_hex='')
    def warn(code,message,identity='container'):report.warn(source_id,code,message,identity)
    def base(identity):
        return dict(source_id=source_id,record_id=identity,container_id='container',entry_index=None,
                    stream_name=None,link_stream_name=None,stream_offset=None,file_offset=None,directory_id=None,category_index=None,
                    entry_number=None,association=None,stored_path=None,path_utf16_hex=None,hostname=None,
                    hostname_hex=None,droids={},last_modified_at=None,last_modified_filetime_raw=None,pin_status=None,
                    pinned=None,metadata_hex=None,extension_hex=None,raw_entry_hex=None,link_status='absent',link_representation=None,link=None,lnk_hex=None)
    def text(raw,encoding,identity):
        local=Report();decoded=Binary(raw).text(raw,encoding,local,source_id)
        for diagnostic in local.diagnostics:
            diagnostic['record_id']=identity;report.diagnostics.append(diagnostic)
        return decoded
    def embedded(payload,identity):
        if len(payload)>MAX_LINK_BYTES:raise AnalysisError('Embedded LNK size limit')
        local=Report()
        try:
            record=lnk.parse(payload,source_id,local,codepage)
            record['record_id']=identity
            for d in local.diagnostics:
                d['record_id']=identity;report.diagnostics.append(d)
            return record,'parsed'
        except AnalysisError as error:
            warn('jump_invalid_link',str(error),identity);return None,'invalid'
    if b.take(0,8)==compound.MAGIC:
        c=compound.Compound(data);summary['container_kind']='automatic';summary['container_header_hex']=data[:c.width].hex()
        entries={e['name'].casefold():e for e in c.streams}
        for e in c.streams:
            payload=c.payloads[e['name'].casefold()]
            summary['streams'].append(dict(name=e['name'],directory_id=e['directory_id'],size=e['size'],mini=e['mini'],
                block_offsets=e['block_offsets'],sha256=hashlib.sha256(payload).hexdigest(),
                raw_hex=payload.hex() if e['name'].casefold()!='destlist' and not re.fullmatch('[1-9a-f][0-9a-f]{0,7}',e['name'],re.I|re.ASCII) else None))
        dest=c.payloads.get('destlist');de=entries.get('destlist')
        if dest is None:warn('jump_missing_destlist','No active DestList stream; numbered streams retained without usage claims')
        elif not dest:warn('jump_empty_destlist','Empty DestList stream')
        else:
            d=Binary(dest,'DestList');summary['header_hex']=d.take(0,32).hex();version=d.number(0,4)
            if version not in (1,3,4):raise AnalysisError('Unsupported DestList version')
            summary.update(version=version,declared_entries=d.number(4,4),declared_pinned=d.number(8,4))
            if summary['declared_entries']>MAX_ENTRIES:raise AnalysisError('DestList entry limit')
            cursor=32
            for ordinal in range(summary['declared_entries']):
                start=cursor;fixed=114 if version==1 else 130
                d.take(start,fixed);units=d.number(start+fixed-2,2)
                if units>MAX_PATH_UNITS:raise AnalysisError('DestList path code-unit limit')
                raw=d.take(start+fixed,units*2);cursor+=fixed+units*2
                extension=b''
                if version!=1:
                    size=d.number(cursor,4);extension=d.take(cursor+4,size);cursor+=4+size
                identity='dest:'+str(start);r=base(identity);ticks=d.number(start+100,8);pin=d.number(start+108,4);pin=pin if pin<2**31 else pin-2**32
                if pin < -1:warn('jump_invalid_pin','Unknown negative pin state retained',identity)
                # Logical stream offset is mapped through block offsets, not added to the first sector.
                block=64 if de['mini'] else c.width
                physical=de['block_offsets'][start//block]+start%block
                r.update(entry_index=ordinal,stream_name=de['name'],stream_offset=start,file_offset=physical,directory_id=de['directory_id'],
                         entry_number=str(d.number(start+88,4)),stored_path=text(raw,'utf-16-le',identity),path_utf16_hex=raw.hex(),
                         hostname=text(d.take(start+72,16).split(b'\0',1)[0],'ascii',identity),hostname_hex=d.take(start+72,16).hex(),
                         droids={name:str(uuid.UUID(bytes_le=d.take(start+offset,16))) for name,offset in (('volume',8),('file',24),('birth_volume',40),('birth_file',56))},
                         last_modified_at=filetime(ticks,report,source_id,identity),last_modified_filetime_raw=str(ticks),pin_status=pin,pinned=None if pin < -1 else pin>=0,
                         metadata_hex=d.take(start,fixed-2).hex(),extension_hex=extension.hex(),raw_entry_hex=d.take(start,cursor-start).hex())
                if extension:warn('jump_opaque_extension','DestList extension retained without property-store interpretation',identity)
                if '\0' in r['stored_path']:warn('jump_path_nul','DestList path contains NUL; retained literally',identity)
                rows.append(r)
            summary['trailing_data_hex']=d.take(cursor,len(dest)-cursor).hex()
            if summary['trailing_data_hex']:warn('jump_destlist_trailing','Uncounted DestList bytes retained; not carved')
            if sum(r['pinned'] is True for r in rows)!=summary['declared_pinned']:warn('jump_pinned_count','Declared pinned count differs from interpreted entries')
        counts=Counter(r['entry_number'] for r in rows);referenced=set()
        for r in rows:
            name=format(int(r['entry_number']),'x');e=entries.get(name)
            if counts[r['entry_number']]!=1:
                r['association']='ambiguous';warn('jump_duplicate_entry','Duplicate DestList entry number; no link assigned',r['record_id'])
            elif e is None or not re.fullmatch('[1-9a-f][0-9a-f]{0,7}',name):
                r['association']='missing';warn('jump_missing_link','No canonical numbered stream for entry',r['record_id'])
            else:
                referenced.add(name);payload=c.payloads[name];r.update(link_stream_name=e['name'],association='matched',link_representation='full_lnk',lnk_hex=payload.hex())
                r['link'],r['link_status']=embedded(payload,r['record_id'])
        for name,e in entries.items():
            if name=='destlist' or name in referenced:continue
            if not re.fullmatch('[1-9a-f][0-9a-f]{0,7}',name):
                warn('jump_unknown_stream','Noncanonical stream retained without interpretation: '+e['name']);continue
            r=base('stream:'+str(e['directory_id']));payload=c.payloads[name]
            r.update(stream_name=e['name'],link_stream_name=e['name'],stream_offset=0,file_offset=e['block_offsets'][0] if e['block_offsets'] else None,directory_id=e['directory_id'],association='unassociated',link_representation='full_lnk',lnk_hex=payload.hex())
            r['link'],r['link_status']=embedded(payload,r['record_id']);rows.append(r)
            warn('jump_unassociated_link','Active numbered stream lacks an unambiguous DestList association',r['record_id'])
    else:
        summary['container_kind']='custom';summary['version']=b.number(0,4);count=b.number(4,4);summary['header_hex']=b.take(0,12).hex();summary['container_header_hex']=summary['header_hex']
        if summary['version']!=2 or count>MAX_CATEGORIES:raise AnalysisError('Unsupported custom Jump List version/category count')
        cursor=12
        for index in range(count):
            start=cursor;kind=b.number(cursor,4);cursor+=4;name=None;name_hex=None;known=None;number=0
            if kind==0:
                units=b.number(cursor,2);cursor+=2
                if units>MAX_PATH_UNITS:raise AnalysisError('Custom category name limit')
                raw=b.take(cursor,units*2);name=text(raw,'utf-16-le','category:'+str(start));name_hex=raw.hex();cursor+=len(raw)
            elif kind==1:known=b.number(cursor,4);cursor+=4
            elif kind!=2:raise AnalysisError('Unsupported custom category type')
            if kind!=1:number=b.number(cursor,4);cursor+=4
            if number>MAX_ENTRIES-len(rows):raise AnalysisError('Custom entry limit')
            summary['categories'].append(dict(category_index=index,file_offset=start,kind=kind,name=name,name_utf16_hex=name_hex,known_category=known,declared_entries=number))
            for ordinal in range(number):
                offset=cursor;representation='full_lnk'
                # COM persistence may store CLSID + body rather than HeaderSize + CLSID + body.
                if b.take(cursor,16)==lnk.CLSID:
                    representation='clsid_body'
                    size=link_length(data,cursor,body_only=True)
                    payload=(76).to_bytes(4,'little')+b.take(cursor,size);cursor+=size
                else:
                    size=link_length(data,cursor);payload=b.take(cursor,size);cursor+=size
                identity='custom:'+str(offset);r=base(identity)
                r.update(entry_index=ordinal,file_offset=offset,category_index=index,association='custom',link_representation=representation,
                         raw_entry_hex=b.take(offset,cursor-offset).hex(),lnk_hex=payload.hex())
                r['link'],r['link_status']=embedded(payload,identity);rows.append(r)
            if b.number(cursor,4)!=FOOTER:raise AnalysisError('Custom category footer mismatch')
            cursor+=4
        if cursor!=len(data):raise AnalysisError('Custom trailing bytes/unsupported category envelope')
    if len(rows)>MAX_ENTRIES:raise AnalysisError('Jump List entry limit')
    if len(json.dumps([summary,rows],ensure_ascii=False).encode('utf-8'))>MAX_OUTPUT_BYTES:raise AnalysisError('Jump List output limit')
    return summary,rows
