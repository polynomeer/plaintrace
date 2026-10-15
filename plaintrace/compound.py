"""Bounded flat CFB reader for active AutomaticDestinations streams only."""
import struct
from .binary import Binary
from .evidence import AnalysisError

MAGIC=bytes.fromhex('d0cf11e0a1b11ae1')
FREE=0xffffffff
END=0xfffffffe
FAT=0xfffffffd
DIF=0xfffffffc
MAX_BYTES=32*1024*1024
MAX_SECTORS=65536
MAX_DIRECTORY=4096
MAX_STREAMS=1024


class Compound:
    def __init__(self,data):
        self.b=Binary(data,'CFB');b=self.b
        if len(data)>MAX_BYTES or b.take(0,8)!=MAGIC:raise AnalysisError('Invalid/oversized CFB')
        b.take(0,512);version=b.number(26,2);shift=b.number(30,2)
        if version not in (3,4) or shift!={3:9,4:12}[version] or b.number(28,2)!=0xfffe or b.number(32,2)!=6:
            raise AnalysisError('Unsupported CFB version/sector format')
        if b.take(8,16)!=bytes(16) or b.take(34,6)!=bytes(6) or b.number(56,4)!=4096:
            raise AnalysisError('Unsupported CFB header/reserved fields')
        self.width=1<<shift
        if len(data)%self.width or len(data)<self.width*2:raise AnalysisError('CFB sector alignment/truncation')
        if version==4 and any(b.take(512,self.width-512)):raise AnalysisError('CFB header padding is nonzero')
        self.count=len(data)//self.width-1
        if self.count>MAX_SECTORS:raise AnalysisError('CFB sector limit exceeded')
        self.used=set();self.mini_used=set();words=self.width//4
        fat_count=b.number(44,4);dif_count=b.number(72,4)
        if not 0<fat_count<=min(self.count,(MAX_SECTORS+words-1)//words) or dif_count>self.count:raise AnalysisError('Invalid CFB FAT/DIFAT counts')
        fat_ids=list(struct.unpack('<109I',b.take(76,436)));dif_ids=[];pointer=b.number(68,4)
        for _ in range(dif_count):
            self.claim(pointer);dif_ids.append(pointer)
            values=self.words(pointer);fat_ids.extend(values[:-1]);pointer=values[-1]
        if pointer!=END:raise AnalysisError('Invalid CFB DIFAT termination')
        if any(i!=FREE for i in fat_ids[fat_count:]):raise AnalysisError('CFB surplus DIFAT entries')
        fat_ids=fat_ids[:fat_count]
        if len(fat_ids)!=fat_count:raise AnalysisError('CFB FAT list incomplete')
        for sid in fat_ids:self.claim(sid)
        self.fat=[]
        for sid in fat_ids:self.fat.extend(self.words(sid))
        if len(self.fat)<self.count:raise AnalysisError('CFB FAT does not cover file')
        if any(self.fat[sid]!=FAT for sid in fat_ids) or any(self.fat[sid]!=DIF for sid in dif_ids):
            raise AnalysisError('CFB metadata sector marker mismatch')
        directory_ids=self.chain(b.number(48,4),self.fat,self.count)
        if not directory_ids or len(directory_ids)*self.width//128>MAX_DIRECTORY:raise AnalysisError('CFB directory limit/empty chain')
        if (version==3 and b.number(40,4)) or (version==4 and b.number(40,4)!=len(directory_ids)):
            raise AnalysisError('CFB directory sector count mismatch')
        directory=b''.join(self.sector(i) for i in directory_ids);self.directory=[]
        for offset in range(0,len(directory),128):
            d=Binary(directory[offset:offset+128],'CFB directory');kind=d.number(66,1)
            if kind==0:self.directory.append(None);continue
            length=d.number(64,2)
            if length<2 or length>64 or length%2 or d.take(length-2,2)!=b'\0\0':raise AnalysisError('CFB directory name length/termination')
            try:name=d.take(0,length-2).decode('utf-16-le')
            except UnicodeError as error:raise AnalysisError('Invalid CFB directory Unicode') from error
            if not name or any(c in name for c in ('\0','/','\\',':','!')):raise AnalysisError('Unsupported CFB stream name')
            size=d.number(120,8)
            if (version==3 and size>>32) or size>MAX_BYTES:raise AnalysisError('CFB stream size limit')
            self.directory.append(dict(directory_id=offset//128,name=name,kind=kind,left=d.number(68,4),right=d.number(72,4),child=d.number(76,4),start=d.number(116,4),size=size))
        root=self.directory[0]
        if root is None or root['kind']!=5 or root['left']!=FREE or root['right']!=FREE:raise AnalysisError('Invalid CFB root entry')
        self.root=root;self.streams=[];visited=set();stack=[root['child']]
        while stack:
            index=stack.pop()
            if index==FREE:continue
            if index==0 or index>=len(self.directory) or index in visited:raise AnalysisError('CFB directory cycle/invalid reference')
            visited.add(index);entry=self.directory[index]
            if entry is None or entry['kind']!=2 or entry['child']!=FREE:raise AnalysisError('Nested/non-stream CFB directory unsupported')
            self.streams.append(entry);stack.extend([entry['right'],entry['left']])
            if len(self.streams)>MAX_STREAMS:raise AnalysisError('CFB stream limit')
        if any(e is not None and i!=0 and i not in visited for i,e in enumerate(self.directory)):
            raise AnalysisError('CFB unreachable active directory entries unsupported')
        names=[e['name'].casefold() for e in self.streams]
        if len(set(names))!=len(names):raise AnalysisError('CFB duplicate stream names')
        mini_count=b.number(64,4)
        if mini_count>min(self.count,(MAX_BYTES//64+words-1)//words):raise AnalysisError('CFB miniFAT count limit')
        mini_ids=self.chain(b.number(60,4),self.fat,self.count,mini_count)
        self.minifat=[]
        for sid in mini_ids:self.minifat.extend(self.words(sid))
        self.root_chain=self.chain(root['start'],self.fat,self.count,(root['size']+self.width-1)//self.width)
        self.mini_data=b''.join(self.sector(i) for i in self.root_chain)[:root['size']]
        if root['size']%64:raise AnalysisError('CFB root mini stream alignment')
        self.payloads={}
        for entry in self.streams:
            small=entry['size']<4096;unit=64 if small else self.width
            ids=self.chain(entry['start'],self.minifat if small else self.fat,len(self.mini_data)//64 if small else self.count,(entry['size']+unit-1)//unit,small)
            payload=b''.join(self.mini_data[i*64:(i+1)*64] if small else self.sector(i) for i in ids)[:entry['size']]
            # Exact physical byte offsets for each logical stream block.
            offsets=[(self.root_chain[(i*64)//self.width]+1)*self.width+(i*64)%self.width if small else (i+1)*self.width for i in ids]
            entry.update(mini=small,block_offsets=offsets)
            self.payloads[entry['name'].casefold()]=payload

    def claim(self,sid,small=False):
        used=self.mini_used if small else self.used
        if sid<0 or (not small and sid>=self.count) or sid in used:raise AnalysisError('CFB sector out of bounds/cycle/overlap')
        used.add(sid)

    def sector(self,sid):return self.b.take((sid+1)*self.width,self.width)
    def words(self,sid):return list(struct.unpack('<'+str(self.width//4)+'I',self.sector(sid)))

    def chain(self,start,table,limit,expected=None,small=False):
        if expected is not None and expected>limit:raise AnalysisError('CFB chain size exceeds extent')
        result=[];sid=start
        while sid!=END:
            if sid>=limit or sid>=len(table) or (expected is not None and len(result)>=expected):
                raise AnalysisError('CFB chain length/reference mismatch')
            self.claim(sid,small);result.append(sid);sid=table[sid]
            if len(result)>limit:raise AnalysisError('CFB chain limit')
        if expected is not None and len(result)!=expected:raise AnalysisError('CFB truncated chain')
        return result
