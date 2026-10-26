"""Bounded offline SOFTWARE/SYSTEM observations, not a live machine inventory."""
import json
from datetime import datetime, timedelta, timezone
from .binary import filetime
from .evidence import AnalysisError
from .registry_hive import Hive

OS_PATH = r'Microsoft\Windows NT\CurrentVersion'
MAX_OBSERVATIONS = 8
MAX_VALUES = 4096
MAX_STRING_UNITS = 4096
MAX_OUTPUT_BYTES = 32*1024*1024
OS_STRINGS = ('ProductName','EditionID','CompositionEditionID','InstallationType','CurrentVersion',
              'CurrentBuild','CurrentBuildNumber','CurrentType','BuildLab','BuildLabEx','BuildBranch',
              'DisplayVersion','ReleaseId','CSDVersion','RegisteredOwner','RegisteredOrganization',
              'ProductId','SystemRoot','PathName','SourcePath','SoftwareType')
OS_SPEC = {name.casefold():'string' for name in OS_STRINGS}
OS_SPEC.update({name.casefold():'dword' for name in ('CurrentMajorVersionNumber','CurrentMinorVersionNumber','UBR')})
OS_SPEC.update(installdate='unix_seconds', installtime='filetime_qword')
SYSTEM_SCOPES = (
    (r'Control\ComputerName\ComputerName','computer_name',{'computername':'string'}),
    (r'Control\ComputerName\ActiveComputerName','active_computer_name',{'computername':'string'}),
    (r'Services\Tcpip\Parameters','tcpip_parameters',{n.casefold():'string' for n in ('Hostname','NV Hostname','Domain','NV Domain')}),
    (r'Control\TimeZoneInformation','time_zone',dict(
        **{n.casefold():'string' for n in ('TimeZoneKeyName','StandardName','DaylightName')},
        **{n.casefold():'signed_dword' for n in ('Bias','ActiveTimeBias','StandardBias','DaylightBias')},
        **{n.casefold():'dword' for n in ('DynamicDaylightTimeDisabled','DisableAutoDaylightTimeSet')})),
    (r'Control\Windows','shutdown',{'shutdowntime':'filetime_binary'}),
)


def analyze_hive(data, role, source_id, report):
    if role not in ('software','system'):
        raise AnalysisError('Unsupported system information hive role')
    hive = Hive(data)
    rows = []
    total_values = 0

    def warn(code, message, identity=None):
        report.warn(source_id, 'system_info_'+code, message, identity)

    def decode(value, kind):
        raw = value['raw'];identity = str(value['offset']+4096)
        item = dict(value_offset=value['offset']+4096,name=value['name'],type=value['type'],
                    status='opaque',decoded=None,text_utf16_hex=None,trailing_data_hex=None,
                    time=None,time_raw=None,time_unit=None,value_data_hex=raw.hex())
        if kind is None:
            return item
        valid_type = value['type'] in (1,2) if kind == 'string' else value['type'] == (11 if kind == 'filetime_qword' else 3 if kind == 'filetime_binary' else 4)
        if not valid_type:
            item['status']='wrong_type';warn('wrong_type','Unsupported registry type for '+value['name'],identity)
            return item
        if kind == 'string':
            if len(raw)>2*(MAX_STRING_UNITS+1):
                raise AnalysisError('System information string byte limit exceeded')
            end=next((i for i in range(0,len(raw)-1,2) if raw[i:i+2]==b'\0\0'),None)
            if end is None:
                item['status']='unterminated';warn('unterminated','No aligned UTF-16 terminator for '+value['name'],identity)
                return item
            item['text_utf16_hex']=raw[:end].hex();item['trailing_data_hex']=raw[end+2:].hex()
            try:
                item['decoded']=raw[:end].decode('utf-16-le');item['status']='parsed'
            except UnicodeError:
                item['decoded']=raw[:end].decode('utf-16-le',errors='backslashreplace');item['status']='invalid_text'
                warn('invalid_text','Invalid UTF-16 escaped for '+value['name'],identity)
            if not item['decoded']:
                if item['status']=='parsed':item['status']='empty'
                warn('empty_text','Empty string retained for '+value['name'],identity)
            if item['trailing_data_hex']:
                if item['status']!='invalid_text':item['status']='trailing'
                warn('trailing_data','String trailing bytes retained for '+value['name'],identity)
            return item
        width=8 if kind.startswith('filetime_') else 4
        if len(raw)!=width:
            item['status']='wrong_size';warn('wrong_size','Unexpected value size for '+value['name'],identity)
            return item
        number=int.from_bytes(raw,'little')
        item['decoded']=int.from_bytes(raw,'little',signed=True) if kind=='signed_dword' else number
        item['status']='parsed'
        if kind.startswith('filetime_'):
            item['time_raw']=str(number);item['time_unit']='filetime_100ns'
            item['time']=filetime(number,report,source_id,identity)
        elif kind=='unix_seconds':
            item['time_raw']=str(number);item['time_unit']='unix_seconds'
            if number:
                item['time']=(datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(seconds=number)).isoformat(timespec='microseconds').replace('+00:00','Z')
        return item

    def emit(path, observation, spec, control=None):
        nonlocal total_values
        key=hive.open(path)
        if key is None:
            warn('branch_absent','Registry branch unavailable: '+path)
            return
        if len(rows)>=MAX_OBSERVATIONS:
            raise AnalysisError('System information observation limit exceeded')
        identity=str(key['offset']+4096)
        values=hive.values(key);total_values+=len(values)
        if total_values>MAX_VALUES:
            raise AnalysisError('System information value limit exceeded')
        missing=sorted(set(spec)-{v['name'].casefold() for v in values})
        if missing:
            warn('fields_absent','Selected fields unavailable in '+observation+': '+', '.join(missing),identity)
        rows.append(dict(source_id=source_id,record_id=identity,hive_role=role,observation_kind=observation,
                         key_path=path,control_set=control,key_last_written=filetime(key['ticks'],report,source_id,identity),
                         key_last_write_raw=str(key['ticks']),values=[decode(v,spec.get(v['name'].casefold())) for v in values]))
    if role=='software':
        emit(OS_PATH,'os_version',OS_SPEC)
    else:
        select=hive.open('Select')
        current=next((v for v in hive.values(select) if v['name'].casefold()=='current'),None) if select else None
        if current is None or current['type']!=4 or len(current['raw'])!=4:
            raise AnalysisError('SYSTEM Select\\Current DWORD required; no ControlSet001 fallback')
        number=int.from_bytes(current['raw'],'little')
        if not 1<=number<=999:
            raise AnalysisError('SYSTEM Select\\Current outside 1..999')
        control=f'ControlSet{number:03}'
        if hive.open(control) is None:
            raise AnalysisError('Selected SYSTEM ControlSet is absent')
        emit('Select','control_set_selection',{n.casefold():'dword' for n in ('Current','Default','Failed','LastKnownGood')},control)
        for suffix,kind,spec in SYSTEM_SCOPES:
            emit(control+'\\'+suffix,kind,spec,control)
    if len(json.dumps(rows,ensure_ascii=False).encode('utf-8'))>MAX_OUTPUT_BYTES:
        raise AnalysisError('System information output limit exceeded')
    return rows
