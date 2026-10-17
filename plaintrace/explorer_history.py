"""Literal Explorer address/search observations, without activity attribution."""
import json
import re
import struct
from .binary import filetime
from .evidence import AnalysisError
from .registry_hive import Hive

BASE = r'Software\Microsoft\Windows\CurrentVersion\Explorer'
SCOPES = {'typed_paths': ('TypedPaths', 1), 'word_wheel_query': ('WordWheelQuery', 3)}
MAX_ENTRIES = 4096
MAX_STRING_UNITS = 4096
MAX_OUTPUT_BYTES = 16*1024*1024


def slot(name, artifact):
    if artifact == 'typed_paths':
        if not name.lower().startswith('url'):
            return None
        name = name[3:]
    if re.fullmatch(r'0|[1-9][0-9]{0,9}', name, re.ASCII) and int(name) <= 0xfffffffe:
        return int(name)
    return None


def analyze_hive(data, artifact, source_id, report):
    if artifact not in SCOPES:
        raise AnalysisError('Unsupported Explorer history artifact')
    hive = Hive(data)
    leaf, required_type = SCOPES[artifact]
    path = BASE+'\\'+leaf
    key = hive.open(path)
    if key is None:
        report.warn(source_id, 'explorer_history_absent', leaf+' key unavailable')
        return [], []
    key_id = str(key['offset']+4096)

    def warn(code, message, identity=key_id):
        report.warn(source_id, 'explorer_history_'+code, message, identity)

    def metadata(value):
        return dict(value_offset=value['offset']+4096, name=value['name'], type=value['type'], data_hex=value['raw'].hex())

    if key['count']:
        warn('nested_keys', 'Only '+leaf+' root is analyzed; descendants not traversed')
    values = hive.values(key)
    controls = [v for v in values if v['name'].casefold() in ('mrulist', 'mrulistex')]
    order, status = [], 'not_applicable' if artifact == 'typed_paths' else 'missing'
    if artifact == 'typed_paths':
        if controls:
            warn('unexpected_control', 'TypedPaths controls retained without ordering interpretation')
    elif len(controls) == 2:
        status = 'ambiguous'
        warn('ambiguous_mru', 'Both controls exist; no ranks assigned')
    elif controls:
        control = controls[0]
        status = 'invalid' if control['name'].casefold() == 'mrulistex' else 'unsupported'
        raw = control['raw']
        if status == 'invalid' and control['type'] == 3 and len(raw) >= 4 and len(raw)%4 == 0:
            numbers = list(struct.unpack('<'+'I'*(len(raw)//4), raw))
            if numbers[-1] == 0xffffffff and 0xffffffff not in numbers[:-1] and len(set(numbers[:-1])) == len(numbers)-1:
                order, status = numbers[:-1], 'valid'
        if status != 'valid':
            warn('invalid_mru', 'Unsupported or malformed MRUListEx; no ranks assigned')
    else:
        warn('missing_mru', 'WordWheelQuery MRUListEx unavailable; no ranks assigned')
    candidates = [v for v in values if slot(v['name'], artifact) is not None]
    if len(candidates) > MAX_ENTRIES:
        raise AnalysisError('Explorer history entry limit exceeded')
    others = [v for v in values if v not in candidates and v not in controls]
    for value in others:
        warn('unknown_value', 'Noncanonical slot retained as raw key metadata', str(value['offset']+4096))
    names = {slot(v['name'], artifact) for v in candidates}
    for number in order:
        if number not in names:
            warn('missing_entry', 'MRUListEx references absent slot: '+str(number))
    ranks = {number:rank for rank,number in enumerate(order)}
    entries = []
    for value in candidates:
        identity, raw = str(value['offset']+4096), value['raw']
        number = slot(value['name'], artifact)
        rank = ranks.get(number)
        if status == 'valid' and rank is None:
            warn('unlisted_entry', 'Entry absent from valid MRUListEx; rank unavailable', identity)
        text, text_hex, tail, entry_status = None, None, None, 'wrong_type'
        if value['type'] != required_type:
            warn('wrong_type', 'Wrong registry type for '+leaf+'; raw data retained', identity)
        else:
            if len(raw) > 2*(MAX_STRING_UNITS+1):
                raise AnalysisError('Explorer history string byte limit exceeded')
            end = next((i for i in range(0,len(raw)-1,2) if raw[i:i+2] == b'\0\0'), None)
            entry_status = 'unterminated'
            if end is None:
                warn('unterminated', 'No aligned UTF-16 NUL; raw data retained', identity)
            else:
                text_hex, tail = raw[:end].hex(), raw[end+2:].hex()
                try:
                    text = raw[:end].decode('utf-16-le')
                    entry_status = 'parsed' if text else 'empty'
                except UnicodeError:
                    text = raw[:end].decode('utf-16-le', errors='backslashreplace')
                    entry_status = 'invalid_text'
                    warn('invalid_text', 'Invalid UTF-16 escaped; bytes authoritative', identity)
                if not text:
                    warn('empty_text', 'Empty text retained', identity)
                if tail:
                    if entry_status != 'invalid_text':
                        entry_status = 'trailing'
                    warn('trailing_data', 'Bytes after first terminator retained opaque', identity)
        entries.append(dict(source_id=source_id, record_id=identity, key_id=key_id, key_path=path, artifact=artifact,
                            value_name=value['name'], value_type=value['type'], slot_number=number, mru_rank=rank,
                            status=entry_status, stored_text=text, text_utf16_hex=text_hex,
                            trailing_data_hex=tail, value_data_hex=raw.hex()))
    keys = [dict(source_id=source_id, record_id=key_id, key_path=path, artifact=artifact,
                 key_last_written=filetime(key['ticks'], report, source_id, key_id), key_last_write_raw=str(key['ticks']),
                 mru_status=status, mru_order=order, control_values=[metadata(v) for v in controls],
                 other_values=[metadata(v) for v in others])]
    if len(json.dumps([keys, entries], ensure_ascii=False).encode('utf-8')) > MAX_OUTPUT_BYTES:
        raise AnalysisError('Explorer history output limit exceeded')
    return keys, entries
