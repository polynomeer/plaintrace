"""Bounded allocated REGF cells; no recovery, log replay or Windows API access."""
import struct
from .binary import Binary
from .evidence import AnalysisError

MAX_HIVE_BYTES = 64*1024*1024
MAX_CELLS = 250_000
MAX_ITEMS = 100_000
MAX_VALUE_BYTES = 16344  # Segmented db data is deliberately unsupported.
MAX_TOTAL_VALUE_BYTES = 16*1024*1024


class Hive:
    def __init__(self, data):
        self.data = data
        self.cells, self.keys, self.child_cache, self.value_cache = {}, {}, {}, {}
        self.child_names = {}
        self.total_values = self.total_bytes = 0
        b = Binary(data, 'REGF')
        if len(data)>MAX_HIVE_BYTES or b.take(0,4)!=b'regf':
            raise AnalysisError('Invalid/oversized REGF hive')
        b.take(0,4096)
        if b.number(4,4)!=b.number(8,4):
            raise AnalysisError('Dirty REGF sequences; transaction-log replay unsupported')
        if b.number(20,4)!=1 or b.number(24,4) not in (3,4,5) or b.number(28,4)!=0 or b.number(32,4)!=1:
            raise AnalysisError('Unsupported REGF version/type/format')
        checksum=0
        for value in struct.unpack('<127I',data[:508]):checksum^=value
        checksum = 1 if checksum==0 else 0xfffffffe if checksum==0xffffffff else checksum
        if checksum!=b.number(508,4):raise AnalysisError('REGF header checksum mismatch')
        size=b.number(40,4)
        if not size or size%4096 or len(data)!=4096+size:
            raise AnalysisError('REGF bin size/alignment mismatch; trailing data unsupported')
        position=0
        scanned=0
        while position<size:
            start=4096+position
            if b.take(start,4)!=b'hbin' or b.number(start+4,4)!=position:
                raise AnalysisError('Invalid REGF hbin header')
            bin_size=b.number(start+8,4)
            if bin_size<4096 or bin_size%4096 or bin_size>size-position:
                raise AnalysisError('REGF hbin outside declared extent')
            cursor=start+32
            while cursor<start+bin_size:
                scanned+=1
                if scanned>MAX_CELLS:raise AnalysisError('REGF cell limit exceeded')
                signed=int.from_bytes(b.take(cursor,4),'little',signed=True)
                length=abs(signed)
                if length<8 or length%8 or length>start+bin_size-cursor:
                    raise AnalysisError('Invalid REGF cell length')
                if signed<0:self.cells[cursor-4096]=(cursor+4,length-4)
                cursor+=length
            position+=bin_size
        self.root_offset=b.number(36,4)
        self.key(self.root_offset)

    def cell(self,offset):
        if offset not in self.cells:raise AnalysisError('REGF reference is not an allocated cell boundary')
        start,length=self.cells[offset]
        return Binary(memoryview(self.data)[start:start+length],'REGF cell')

    @staticmethod
    def name(raw, compressed, key=False):
        try:text=bytes(raw).decode('latin-1' if compressed else 'utf-16-le')
        except UnicodeError as error:raise AnalysisError('Invalid REGF key/value name encoding') from error
        if '\0' in text or (key and ('\\' in text or not text)):
            raise AnalysisError('Invalid REGF name/path separator')
        return text

    def key(self,offset):
        if offset in self.keys:return self.keys[offset]
        if len(self.keys)>=MAX_ITEMS:raise AnalysisError('REGF key limit exceeded')
        b=self.cell(offset)
        if b.take(0,2)!=b'nk':raise AnalysisError('REGF key reference is not nk')
        b.take(0,76)
        flags=b.number(2,2)
        if flags&0x10:raise AnalysisError('REGF symbolic-link key unsupported')
        if b.number(24,4):raise AnalysisError('REGF volatile subkeys unsupported')
        raw=b.take(76,b.number(72,2))
        if len(raw)>(255 if flags&32 else 510):raise AnalysisError('REGF key name limit exceeded')
        result=dict(offset=offset,name=self.name(raw,bool(flags&32),True),ticks=b.number(4,8),
                    parent=b.number(16,4),count=b.number(20,4),children=b.number(28,4),
                    value_count=b.number(36,4),values=b.number(40,4))
        self.keys[offset]=result
        return result

    def children(self,key):
        offset=key['offset']
        if offset in self.child_cache:return self.child_cache[offset]
        if key['count']>MAX_ITEMS:raise AnalysisError('REGF child count limit exceeded')
        stack=[key['children']] if key['count'] else []
        visited=set();children=[]
        while stack:
            pointer=stack.pop()
            if pointer in visited or len(visited)>=MAX_ITEMS:raise AnalysisError('REGF index cycle/limit')
            visited.add(pointer);b=self.cell(pointer);kind=b.take(0,2);count=b.number(2,2)
            width=8 if kind in (b'lf',b'lh') else 4
            if kind not in (b'li',b'lf',b'lh',b'ri'):raise AnalysisError('Unsupported REGF child index')
            b.take(4,count*width)
            entries=[b.number(4+i*width,4) for i in range(count)]
            if kind==b'ri':stack.extend(reversed(entries))
            else:children.extend(entries)
            if len(stack)+len(children)>MAX_ITEMS:raise AnalysisError('REGF index item limit exceeded')
        if len(children)!=key['count'] or len(set(children))!=len(children):
            raise AnalysisError('REGF child count/duplicate mismatch')
        result=[self.key(pointer) for pointer in children]
        names=[child['name'].casefold() for child in result]
        if len(set(names))!=len(names) or any(child['parent']!=offset for child in result):
            raise AnalysisError('REGF ambiguous children or parent mismatch')
        self.child_names[offset]={child["name"].casefold():child for child in result}
        self.child_cache[offset]=result
        return result

    def open(self,path):
        key=self.key(self.root_offset)
        for name in path.split('\\') if path else []:
            self.children(key)
            key=self.child_names[key['offset']].get(name.casefold())
            if key is None:return None
        return key

    def values(self,key):
        offset=key['offset']
        if offset in self.value_cache:return self.value_cache[offset]
        count=key['value_count']
        self.total_values+=count
        if count>4096 or self.total_values>MAX_ITEMS:raise AnalysisError('REGF value count limit exceeded')
        pointers=self.cell(key['values']) if count else None
        if count:pointers.take(0,count*4)
        values=[];names=set()
        references=[pointers.number(index*4,4) for index in range(count)]
        if len(set(references))!=count:raise AnalysisError('REGF duplicate value references')
        for pointer in references:
            b=self.cell(pointer)
            if b.take(0,2)!=b'vk':raise AnalysisError('REGF value reference is not vk')
            b.take(0,20);length=b.number(4,4);inline=bool(length&0x80000000);length&=0x7fffffff
            if length>MAX_VALUE_BYTES or (inline and length>4):raise AnalysisError('REGF big/oversized value unsupported')
            raw=b.take(8,length) if inline else self.cell(b.number(8,4)).take(0,length) if length else b''
            name_length=b.number(2,2)
            if name_length>(16383 if b.number(16,2)&1 else 32766):raise AnalysisError('REGF value name limit exceeded')
            self.total_bytes+=length+name_length
            if self.total_bytes>MAX_TOTAL_VALUE_BYTES:raise AnalysisError('REGF aggregate value-byte limit exceeded')
            name=self.name(b.take(20,name_length),bool(b.number(16,2)&1))
            if name.casefold() in names:raise AnalysisError('REGF duplicate value names')
            names.add(name.casefold())
            values.append(dict(offset=pointer,name=name,type=b.number(12,4),raw=bytes(raw)))
        self.value_cache[offset]=values
        return values
