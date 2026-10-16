"""Literal RunMRU strings and explicit ordering, never command execution."""
import json
import re
from .binary import filetime
from .evidence import AnalysisError
from .registry_hive import Hive

KEY_PATH = r'Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU'
MAX_ENTRIES = 26
MAX_STRING_UNITS = 4096
MAX_OUTPUT_BYTES = 8*1024*1024
LETTER = re.compile('[a-z]', re.I | re.ASCII)


def analyze_hive(data, source_id, report):
    hive = Hive(data)
    key = hive.open(KEY_PATH)
    if key is None:
        report.warn(source_id, 'run_mru_absent', 'Explorer RunMRU key unavailable')
        return [], []
    key_id = str(key['offset']+4096)

    def warn(code, message, identity=key_id):
        report.warn(source_id, 'run_mru_'+code, message, identity)

    def metadata(value):
        return dict(value_offset=value['offset']+4096, name=value['name'], type=value['type'], data_hex=value['raw'].hex())

    if key['count']:
        warn('nested_keys', 'RunMRU subkeys are not traversed')
    values = hive.values(key)
    controls = [v for v in values if v['name'].casefold() in ('mrulist', 'mrulistex')]
    order, status = [], 'missing'
    if len(controls) == 2:
        status = 'ambiguous'
        warn('ambiguous_mru', 'Both ordering controls exist; no ranks assigned')
    elif controls:
        control = controls[0]
        status = 'invalid' if control['name'].casefold() == 'mrulist' else 'unsupported'
        if status == 'invalid' and control['type'] == 1:
            try:
                text = control['raw'].decode('utf-16-le')
                if text.endswith('\0') and re.fullmatch('[a-z]*', text[:-1], re.I | re.ASCII) and len(set(text[:-1].casefold())) == len(text)-1:
                    order, status = list(text[:-1]), 'valid'
            except UnicodeError:
                pass
        if status != 'valid':
            warn('invalid_mru', 'Unsupported, malformed, duplicate or wrong-type control; no ranks assigned')
    else:
        warn('missing_mru', 'MRUList unavailable; no ranks assigned')
    candidates = [v for v in values if LETTER.fullmatch(v['name'])]
    if len(candidates) > MAX_ENTRIES:
        raise AnalysisError('RunMRU entry limit exceeded')
    others = [v for v in values if v not in controls and v not in candidates]
    for value in others:
        warn('unknown_value', 'Non-letter value retained as key metadata', str(value['offset']+4096))
    names = {v['name'].casefold() for v in candidates}
    for name in order:
        if name.casefold() not in names:
            warn('missing_entry', 'MRUList references absent value: '+name)
    ranks = {name.casefold():rank for rank,name in enumerate(order)}
    entries = []
    for value in candidates:
        identity, raw = str(value['offset']+4096), value['raw']
        rank = ranks.get(value['name'].casefold())
        if status == 'valid' and rank is None:
            warn('unlisted_entry', 'Entry absent from valid MRUList; no rank assigned', identity)
        text, text_hex, tail, entry_status = None, None, None, 'wrong_type'
        if value['type'] != 1:
            warn('wrong_type', 'Only REG_SZ command values are decoded', identity)
        else:
            if len(raw) > 2*(MAX_STRING_UNITS+1):
                raise AnalysisError('RunMRU string byte limit exceeded')
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
                    warn('invalid_text', 'Invalid UTF-16 escaped; raw data retained', identity)
                if not text:
                    warn('empty_command', 'Empty stored command retained', identity)
                if tail:
                    if entry_status != 'invalid_text':
                        entry_status = 'trailing'
                    warn('trailing_data', 'Data after first string terminator retained opaque', identity)
        entries.append(dict(source_id=source_id, record_id=identity, key_id=key_id, key_path=KEY_PATH,
                            value_name=value['name'], value_type=value['type'], mru_rank=rank,
                            status=entry_status, stored_command=text, command_utf16_hex=text_hex,
                            trailing_data_hex=tail, value_data_hex=raw.hex()))
    keys = [dict(source_id=source_id, record_id=key_id, key_path=KEY_PATH,
                 key_last_written=filetime(key['ticks'], report, source_id, key_id), key_last_write_raw=str(key['ticks']),
                 mru_status=status, mru_order=order, control_values=[metadata(v) for v in controls],
                 other_values=[metadata(v) for v in others])]
    if len(json.dumps([keys, entries], ensure_ascii=False).encode('utf-8')) > MAX_OUTPUT_BYTES:
        raise AnalysisError('RunMRU output limit exceeded')
    return keys, entries
