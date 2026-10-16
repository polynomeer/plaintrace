"""Independent generated Shell Items and BagMRU REGF trees, never real evidence."""
import struct
import uuid
from test_usb_registry_cli import hive_fixture,value,text,FT,UTC

NT=r'Software\Microsoft\Windows\Shell'
UC=r'Local Settings\Software\Microsoft\Windows\Shell'
FAT=bytes.fromhex('21505c64')
FAT_TEXT='2020-01-01T12:34:56'
GUID='20d04fe0-3aea-1069-a2d8-08002b30309d'

def mru(*slots):return value('MRUListEx',3,b''.join(struct.pack('<I',i) for i in slots)+b'\xff'*4)
def node(slot):return value('NodeSlot',4,struct.pack('<I',slot),True)
def shell_value(name,*items,terminal=True):return value(str(name),3,b''.join(items)+(bytes(2) if terminal else b''))
def root_item():return struct.pack('<HBB',20,0x1f,0x50)+uuid.UUID(GUID).bytes_le
def volume(name='C:\\',kind=0x2f):return struct.pack('<HB',25,kind)+name.encode('ascii').ljust(20,b'\0')+bytes(2)
def network(name='\\\\server\\share',kind=0xc3):
    payload=bytes([kind,0,0])+name.encode('ascii')+b'\0';return struct.pack('<H',len(payload)+2)+payload

def file_item(name='Folder',long_name=None,version=9,wide=False,encoding='cp1252',extra=None):
    raw=(name+'\0').encode('utf-16-le' if wide else encoding);header=bytearray(14);header[2]=0x35 if wide else 0x31
    struct.pack_into('<I',header,4,7);header[8:12]=FAT;struct.pack_into('<H',header,12,16)
    raw=bytes(header)+raw
    if len(raw)%2:raw+=bytes(1)
    if long_name is not None:
        start=len(raw);size={3:20,7:38,8:42,9:46}.get(version,20);extension=bytearray(size)
        struct.pack_into('<HHI',extension,0,0,version,0xbeef0004);extension[8:12]=FAT;extension[12:16]=FAT
        if version in (7,8,9):extension[20:28]=bytes.fromhex('8877665544332211')
        extension+=(long_name+'\0').encode('utf-16-le')+struct.pack('<H',start)
        struct.pack_into('<H',extension,0,len(extension));raw+=extension
    elif extra is not None:raw+=extra
    else:raw+=bytes(2)
    raw=bytearray(raw);struct.pack_into('<H',raw,0,len(raw));return bytes(raw)

def paths(base=NT):
    return {base+'\\BagMRU':[shell_value(0,root_item()),mru(0),node(1)],
            base+'\\BagMRU\\0':[shell_value(2,volume()),mru(2),node(2)],
            base+'\\BagMRU\\0\\2':[shell_value(9,file_item('SHORT~1',long_name='한글😀')),shell_value(3,file_item('Older')),mru(9,3),node(3)],
            base+'\\BagMRU\\0\\2\\9':[shell_value(0,file_item('Child')),mru(0),node(3)],
            base+'\\Bags\\1':[],base+'\\Bags\\1\\Shell':[value('Mode',4,struct.pack('<I',4),True)],
            base+'\\Bags\\2':[],base+'\\Bags\\3':[],base+'\\Bags\\3\\Shell\\{view}':[text('FolderType','Documents')]}
