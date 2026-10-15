"""USB registry observations with explicit timestamp basis, never session inference."""
import json
from .binary import filetime
from .evidence import AnalysisError
from .registry_hive import Hive

PROPERTY_GUID='{83da6326-97a6-4088-9453-a1923f573b29}'
PROPERTY_NAMES={'0064':'install_date','0065':'first_install_date','0066':'last_arrival_date','0067':'last_removal_date'}
MAX_ROWS=10000
MAX_OUTPUT_BYTES=32*1024*1024


def analyze_hive(data,role,source_id,report):
    hive=Hive(data);rows=[];seen=set()
    def warn(code,message,identity=None):report.warn(source_id,code,message,identity)
    def values(key):
        output=[]
        for value in hive.values(key):
            raw=value['raw'];kind=value['type'];decoded=None
            if kind in (1,2,7):
                try:
                    text=raw.decode('utf-16-le')
                    if not text.endswith('\0'):warn('registry_unterminated_text','Registry string lacks NUL terminator',str(value['offset']+4096))
                    decoded=text.rstrip('\0').split('\0') if kind==7 else text.rstrip('\0')
                except UnicodeError:warn('registry_invalid_text','Undecodable UTF-16 retained as raw hex',str(value['offset']+4096))
            elif kind in (4,5,11):
                if len(raw)==(8 if kind==11 else 4):decoded=str(int.from_bytes(raw,'big' if kind==5 else 'little'))
                else:warn('registry_invalid_integer','Wrong numeric value length; raw retained')
            output.append(dict(value_offset=value['offset']+4096,name=value['name'],type=kind,data_hex=raw.hex(),decoded=decoded))
        return output
    def emit(key,path,kind,control_set=None,device=None,instance=None):
        if key['offset'] in seen:raise AnalysisError('USB registry repeated key reference')
        seen.add(key['offset'])
        if len(rows)>=MAX_ROWS:raise AnalysisError('USB registry observation limit exceeded')
        if kind not in ('usbstor','usb'):device=None
        record_id=str(key['offset']+4096)
        items=values(key)
        friendly=next((item['decoded'] for item in items if item['name'].casefold()=='friendlyname' and item['type']==1),None)
        tokens={}
        for token in (device or '').split('&'):
            for prefix in ('Ven_','Prod_','Rev_','VID_','PID_'):
                if token.lower().startswith(prefix.lower()):tokens[prefix]=token[len(prefix):]
        times=[]
        if kind in ('usbstor','usb'):
            for pid,meaning in PROPERTY_NAMES.items():
                property_path=path+'\\Properties\\'+PROPERTY_GUID+'\\'+pid
                prop=hive.open(property_path)
                if prop is None:continue
                prop_values=values(prop)
                candidates=[item for item in prop_values if item['name'] in ('','00000000')]
                tick=None
                if len(candidates)==1 and candidates[0]['type'] in (3,16) and len(bytes.fromhex(candidates[0]['data_hex']))==8:
                    tick=int.from_bytes(bytes.fromhex(candidates[0]['data_hex']),'little')
                else:warn('usb_invalid_property','Missing/ambiguous/wrong-size FILETIME property; raw values retained',record_id)
                times.append(dict(property_id=pid,meaning=meaning,key_path=property_path,key_offset=prop['offset']+4096,
                                  filetime_raw=None if tick is None else str(tick),
                                  time=None if tick is None else filetime(tick,report,source_id,record_id),values=prop_values))
        if kind in ('usbstor','usb') and len(times)<4:
            warn('usb_time_properties_absent','Some device time properties are unavailable; no connection times inferred',record_id)
        rows.append(dict(source_id=source_id,record_id=record_id,hive_role=role,observation_kind=kind,
                         key_path=path,key_last_written=filetime(key['ticks'],report,source_id,record_id),
                         key_last_write_raw=str(key['ticks']),control_set=control_set,device_id=device,instance_id=instance,
                         vendor=tokens.get('Ven_'),product=tokens.get('Prod_'),revision=tokens.get('Rev_'),
                         vid=tokens.get('VID_'),pid=tokens.get('PID_'),friendly_name=friendly,device_times=times,values=items))
    def branch(path,kind,depth,control=None):
        root=hive.open(path)
        if root is None:
            warn('usb_branch_absent',f'Registry branch unavailable: {path}')
            return
        stack=[(root,path,0,None)]
        visited=set()
        while stack:
            key,current,level,device=stack.pop()
            if key['offset'] in visited or len(visited)>=100000:raise AnalysisError('USB registry traversal cycle/limit')
            visited.add(key['offset'])
            if level==depth:
                emit(key,current,kind,control,device,key['name'] if kind in ('usbstor','usb') else None)
            else:
                for child in reversed(hive.children(key)):
                    stack.append((child,current+'\\'+child['name'],level+1,child['name'] if level==0 else device))
    if role=='system':
        select=hive.open('Select')
        current=next((v for v in hive.values(select) if v['name'].casefold()=='current'),None) if select else None
        if current is None or current['type']!=4 or len(current['raw'])!=4:
            raise AnalysisError('SYSTEM Select\\Current DWORD required; no ControlSet001 fallback')
        number=int.from_bytes(current['raw'],'little')
        if not 1<=number<=999:raise AnalysisError('SYSTEM Select\\Current outside 1..999')
        control=f'ControlSet{number:03}'
        if hive.open(control) is None:raise AnalysisError('Selected SYSTEM ControlSet is absent')
        branch(control+'\\Enum\\USBSTOR','usbstor',2,control)
        branch(control+'\\Enum\\USB','usb',2,control)
        for guid in ('{53f56307-b6bf-11d0-94f2-00a0c91efb8b}','{53f5630d-b6bf-11d0-94f2-00a0c91efb8b}'):
            branch(control+'\\Control\\DeviceClasses\\'+guid,'device_interface',1,control)
        mounted=hive.open('MountedDevices')
        if mounted:emit(mounted,'MountedDevices','mounted_devices')
        else:warn('usb_branch_absent','Registry branch unavailable: MountedDevices')
    elif role=='software':branch('Microsoft\\Windows Portable Devices\\Devices','portable_device',1)
    elif role=='ntuser':branch('Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\MountPoints2','mount_point',1)
    else:raise AnalysisError('Unsupported USB registry hive role')
    if not rows:warn('usb_no_observations','No supported USB registry observations found')
    if len(json.dumps(rows,ensure_ascii=False).encode('utf-8'))>MAX_OUTPUT_BYTES:raise AnalysisError('USB registry output limit exceeded')
    return rows
