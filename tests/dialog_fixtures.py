"""Synthetic Common Dialog controls and independently framed application/PIDL values."""
from shellbag_fixtures import volume,file_item,root_item,network
from test_usb_registry_cli import hive_fixture,value,text,FT,UTC
import struct
BASE=r'Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32'
OPEN=BASE+'\\OpenSavePidlMRU'
LAST=BASE+'\\LastVisitedPidlMRU'

def mru(*slots):return value('MRUListEx',3,b''.join(struct.pack('<I',s) for s in slots)+b'\xff'*4)
def pidl(*items,terminal=True):return b''.join(items)+(bytes(2) if terminal else b'')
def opened(slot,*items):return value(str(slot),3,pidl(*items))
def visited(slot,application,*items):return value(str(slot),3,(application+'\0').encode('utf-16-le')+pidl(*items))
def paths():
    return {OPEN:[],OPEN+'\\*':[opened(9,root_item(),volume(),file_item('DOCUME~1',long_name='문서😀.doc')),opened(2,volume(),file_item('older.txt')),mru(9,2)],
            OPEN+'\\doc':[opened(3,volume(),file_item('문서😀.doc',wide=True)),mru(3)],
            LAST:[visited(4,'editor.exe',root_item(),volume(),file_item('Documents')),visited(8,'뷰어😀.exe',network(),file_item('Folder')),mru(8,4)]}
