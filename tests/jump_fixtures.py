"""Independent synthetic writers for flat CFB and declared Jump List envelopes."""
import math
import struct
CLSID=bytes.fromhex('0114020000000000c000000000000046')

FREE=0xffffffff
END=0xfffffffe
FT=132223104001234567
UTC='2020-01-01T00:00:00.123456Z'

def link(path='relative.txt',extra=b''):
    h=bytearray(76);struct.pack_into('<I',h,0,76);h[4:20]=CLSID
    struct.pack_into('<I',h,20,0x88);struct.pack_into('<Q',h,28,FT)
    raw=path.encode('utf-16-le');return bytes(h)+struct.pack('<H',len(raw)//2)+raw+extra+bytes(4)

def destlist(version=1,records=None,trailing=b'',pinned=None):
    if records is None:records=[dict(number=1,path='C:\\document.txt',pin=-1)]
    header=bytearray(32);struct.pack_into('<III',header,0,version,len(records),sum(r.get('pin',-1)>=0 for r in records) if pinned is None else pinned)
    output=bytes(header)
    for r in records:
        fixed=114 if version==1 else 130;entry=bytearray(fixed);entry[8:72]=bytes(range(64));entry[72:76]=b'HOST'
        struct.pack_into('<I',entry,88,r['number']);struct.pack_into('<Q',entry,100,r.get('ticks',FT));struct.pack_into('<i',entry,108,r.get('pin',-1))
        raw=r.get('raw',r.get('path','').encode('utf-16-le'));struct.pack_into('<H',entry,fixed-2,len(raw)//2)
        output+=entry+raw
        if version!=1:
            extra=r.get('extension',b'');output+=struct.pack('<I',len(extra))+extra
    return output+trailing

def custom(categories=None):
    if categories is None:categories=[dict(kind=0,name='Documents',links=[link()])]
    out=struct.pack('<III',2,len(categories),0)
    for cat in categories:
        kind=cat['kind'];out+=struct.pack('<I',kind)
        if kind==0:
            name=cat.get('name','').encode('utf-16-le');out+=struct.pack('<H',len(name)//2)+name
        if kind==1:out+=struct.pack('<I',cat.get('known',2))
        else:
            entries=cat.get('links',[]);out+=struct.pack('<I',len(entries))+b''.join(entries)
        out+=struct.pack('<I',0xbabffbab)
    return out

def compound(streams,version=3,fragment=False):
    width=512 if version==3 else 4096;words=width//4;sectors=[];chains=[]
    def allocate(payload):
        ids=[]
        for start in range(0,len(payload),width):
            ids.append(len(sectors));sectors.append(payload[start:start+width].ljust(width,b'\0'))
        if fragment and len(ids)>1:
            # Swap physical chunks while logical chain order retains original bytes.
            sectors[ids[0]],sectors[ids[-1]]=sectors[ids[-1]],sectors[ids[0]];ids[0],ids[-1]=ids[-1],ids[0]
        chains.append(ids);return ids
    mini=bytearray();mini_fat=[];descriptors=[]
    for name,payload in streams.items():
        small=len(payload)<4096
        if small:
            ids=list(range(len(mini_fat),len(mini_fat)+math.ceil(len(payload)/64)))
            mini.extend(payload.ljust(len(ids)*64,b'\0'));mini_fat.extend(ids[1:]+[END] if ids else [])
        else:ids=allocate(payload)
        descriptors.append((name,payload,ids,small))
    root_ids=allocate(bytes(mini))
    mini_ids=allocate(struct.pack('<'+'I'*len(mini_fat),*mini_fat).ljust(math.ceil(len(mini_fat)*4/width)*width,b'\xff'))
    def directory(name,kind,start,size,right=FREE,child=FREE):
        entry=bytearray(128);raw=(name+'\0').encode('utf-16-le');entry[:len(raw)]=raw
        struct.pack_into('<HBBIII',entry,64,len(raw),kind,1,FREE,right,child);struct.pack_into('<IQ',entry,116,start,size);return entry
    directory_data=directory('Root Entry',5,root_ids[0] if root_ids else END,len(mini),child=1 if descriptors else FREE)
    for i,(name,payload,ids,small) in enumerate(descriptors):
        directory_data+=directory(name,2,ids[0] if ids else END,len(payload),right=i+2 if i+1<len(descriptors) else FREE)
    dir_ids=allocate(bytes(directory_data).ljust(math.ceil(len(directory_data)/width)*width,b'\0'))
    fat_count=1;dif_count=0
    while True:
        required=math.ceil((len(sectors)+fat_count+dif_count)/words);difs=max(0,math.ceil((required-109)/(words-1)))
        if (required,difs)==(fat_count,dif_count):break
        fat_count,dif_count=required,difs
    fat_ids=list(range(len(sectors),len(sectors)+fat_count));dif_ids=list(range(len(sectors)+fat_count,len(sectors)+fat_count+dif_count))
    fat=[FREE]*(fat_count*words)
    for chain in chains:
        for sid,nxt in zip(chain,chain[1:]+[END]):fat[sid]=nxt
    for sid in fat_ids:fat[sid]=0xfffffffd
    for sid in dif_ids:fat[sid]=0xfffffffc
    fatraw=struct.pack('<'+'I'*len(fat),*fat)
    sectors.extend(fatraw[i:i+width] for i in range(0,len(fatraw),width))
    rest=fat_ids[109:]
    for i,sid in enumerate(dif_ids):
        chunk=rest[i*(words-1):(i+1)*(words-1)];chunk+=[FREE]*(words-1-len(chunk));chunk+=[dif_ids[i+1] if i+1<len(dif_ids) else END]
        sectors.append(struct.pack('<'+'I'*words,*chunk))
    header=bytearray(width);header[:8]=bytes.fromhex('d0cf11e0a1b11ae1')
    struct.pack_into('<HHHHH',header,24,0x3e,version,0xfffe,9 if version==3 else 12,6)
    struct.pack_into('<IIIIIIIII',header,40,len(dir_ids) if version==4 else 0,len(fat_ids),dir_ids[0],0,4096,mini_ids[0] if mini_ids else END,len(mini_ids),dif_ids[0] if dif_ids else END,len(dif_ids))
    header[76:512]=struct.pack('<109I',*(fat_ids[:109]+[FREE]*(109-min(109,len(fat_ids)))))
    return bytes(header)+b''.join(sectors)
