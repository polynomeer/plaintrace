"""Bounded, deliberately partial Shell Item decoding for BagMRU values."""
from datetime import datetime
import uuid
from .binary import Binary
from .evidence import AnalysisError

MAX_ITEMS=64
MAX_EXTENSIONS=32
MAX_VALUE_BYTES=16344


class InvalidShellItem(AnalysisError):
    """Malformed item framing; the caller can retain the whole raw registry value."""


class ShellItemLimit(AnalysisError):
    """Resource budget exceeded; do not downgrade to a malformed observation."""


def parse(data,codepage,report,source_id,record_id):
    if len(data)>MAX_VALUE_BYTES:raise ShellItemLimit('Shell Item value limit')
    def warn(code,message):report.warn(source_id,code,message,record_id)
    def string(raw,start,end,wide=False):
        width=2 if wide else 1
        stop=next((i for i in range(start,end-width+1,width) if raw[i:i+width]==b'\0'*width),None)
        if stop is None:raise InvalidShellItem('Shell Item unterminated string')
        body=raw[start:stop]
        try:return body.decode('utf-16-le' if wide else codepage),stop+width,True
        except UnicodeError:
            warn('shellbag_invalid_text','Invalid Shell Item text escaped; excluded from path composition')
            return body.decode('utf-16-le' if wide else codepage,errors='backslashreplace'),stop+width,False
    def fat(raw):
        result=dict(raw_hex=raw.hex(),display=None,time_basis='stored_fat_no_timezone')
        if raw==bytes(4):return result
        date=int.from_bytes(raw[:2],'little');time=int.from_bytes(raw[2:],'little')
        try:result['display']=datetime(1980+(date>>9),(date>>5)&15,date&31,time>>11,(time>>5)&63,(time&31)*2).isoformat()
        except ValueError:warn('shellbag_invalid_fat_time','Invalid FAT calendar fields retained')
        return result
    def extensions(raw,start):
        blocks=[];cursor=start;long_names=[]
        while cursor<len(raw):
            if len(blocks)>=MAX_EXTENSIONS:raise ShellItemLimit('Shell Item extension count limit')
            if cursor>len(raw)-8:raise InvalidShellItem('Truncated Shell Item extension header')
            b=Binary(raw[cursor:],'Shell Item extension');size=b.number(0,2)
            if size<8 or size>len(raw)-cursor:raise InvalidShellItem('Shell Item extension size outside item')
            block=raw[cursor:cursor+size];b=Binary(block);version=b.number(2,2);signature=b.number(4,4)
            info=dict(offset=cursor,size=size,version=version,signature=f'{signature:08x}',raw_hex=block.hex(),long_name=None,
                      created_fat=None,accessed_fat=None,file_reference_hex=None)
            if signature==0xbeef0004 and version in (3,7,8,9):
                name_start={3:20,7:38,8:42,9:46}[version]
                if size<name_start+4:raise InvalidShellItem('Truncated BEEF0004 fields/name')
                info['created_fat']=fat(block[8:12]);info['accessed_fat']=fat(block[12:16])
                if version>=7:info['file_reference_hex']=block[20:28].hex()
                name,_,valid=string(block,name_start,size-2,True);info['long_name']=name
                if valid and name:long_names.append(name)
                if int.from_bytes(block[-2:],'little')!=start:
                    raise InvalidShellItem('Shell Item extension backlink mismatch')
            else:warn('shellbag_opaque_extension','Unknown Shell Item extension signature/version retained')
            blocks.append(info);cursor+=size
        if len(long_names)>1:warn('shellbag_ambiguous_long_name','Multiple long names; primary name retained')
        return blocks,long_names[0] if len(long_names)==1 else None
    def item(raw,offset):
        b=Binary(raw,'Shell Item');kind=b.number(2,1)
        result=dict(offset=offset,size=len(raw),class_type=kind,kind='unsupported',status='unsupported',primary_name=None,
                    long_name=None,display_name=None,path_component=None,component_kind=None,folder_id=None,
                    metadata={},extensions=[],raw_hex=raw.hex())
        name=None;valid=False;component_kind=None
        if kind==0x1f:
            b.take(0,20);guid=str(uuid.UUID(bytes_le=raw[4:20]));name='::{'+guid+'}';valid=True;component_kind='namespace'
            result.update(kind='root',folder_id=guid);result['metadata']['sort_index']=raw[3]
            if len(raw)>20:warn('shellbag_opaque_root_tail','Root Shell Item extension remains opaque')
        elif kind in (0x23,0x25,0x29,0x2f):
            b.take(0,25);name,stop,valid=string(raw,3,23);component_kind='volume';result['kind']='volume'
            if any(raw[stop:23]):warn('shellbag_volume_padding','Nonzero volume-name padding retained');valid=False
            if len(raw)>25:warn('shellbag_opaque_volume_tail','Volume Shell Item tail remains opaque')
        elif kind in (0x31,0x32,0x35,0x36) and b.number(3,1)==0:
            b.take(0,16);result['kind']='directory' if kind&1 else 'file';component_kind='name'
            result['metadata']=dict(file_size=b.number(4,4),modified_fat=fat(raw[8:12]),file_attributes=b.number(12,2))
            ext=int.from_bytes(raw[-2:],'little');end=len(raw)
            if ext:
                if ext<14 or ext%2 or ext>len(raw)-8:raise InvalidShellItem('Invalid file-item extension offset')
                end=ext
            name,stop,valid=string(raw,14,end,bool(kind&4));result['primary_name']=name
            if ext:
                if any(raw[stop:ext]):warn('shellbag_primary_padding','Opaque bytes before file extension retained');valid=False
                result['extensions'],long_name=extensions(raw,ext)
                result['long_name']=long_name
                if long_name:name=long_name;valid=True
            elif any(raw[stop:]):warn('shellbag_opaque_file_tail','Opaque file-item bytes after primary name');valid=False
        elif kind in (0x41,0x42,0x43,0x46,0x47,0x4c,0xc3):
            b.take(0,6);name,stop,valid=string(raw,5,len(raw));component_kind='network';result['kind']='network'
            result['metadata']['flags']=raw[4]
            for flag,label in ((128,'description'),(64,'comments')):
                if raw[4]&flag:
                    value,stop,text_valid=string(raw,stop,len(raw));result['metadata'][label]=value;valid=valid and text_valid
            if any(raw[stop:]):warn('shellbag_opaque_network_tail','Network tail remains opaque');valid=False
        else:
            warn('shellbag_unsupported_item','Unsupported Shell Item class/variant retained')
            return result
        result['display_name']=name;result['component_kind']=component_kind
        if not name:warn('shellbag_empty_name','Empty Shell Item name retained');valid=False
        result['path_component']=name if valid else None;result['status']='decoded' if valid else 'partial'
        return result
    items=[];cursor=0;terminated=False
    try:
        b=Binary(data,'BagMRU value')
        while cursor<len(data):
            size=b.number(cursor,2)
            if size==0:cursor+=2;terminated=True;break
            if size<3:raise InvalidShellItem('Invalid Shell Item size')
            if len(items)>=MAX_ITEMS:raise ShellItemLimit('Shell Item count limit')
            raw=b.take(cursor,size);items.append(item(raw,cursor));cursor+=size
        tail=data[cursor:]
        if tail:warn('shellbag_item_trailing','Bytes after item-list terminal retained without interpretation')
        if not items:warn('shellbag_empty_item_list','No Shell Items in numeric value')
        return items,terminated,tail.hex(),bool(items) and not tail
    except (InvalidShellItem,ShellItemLimit):raise
    except AnalysisError as error:
        raise InvalidShellItem(str(error)) from error
