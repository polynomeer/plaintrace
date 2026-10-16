"""Bounded UserAssist observations; no target resolution or execution attribution."""
import codecs
import json
import re
from .binary import filetime
from .evidence import AnalysisError
from .registry_hive import Hive

KEY_PATH = r'Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist'
MAX_KEYS = 1024
MAX_ENTRIES = 10000
MAX_OUTPUT_BYTES = 32*1024*1024
GUID = re.compile(r'\{[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\}', re.I | re.ASCII)


def analyze_hive(data, source_id, report):
    hive = Hive(data)
    root = hive.open(KEY_PATH)
    if root is None:
        report.warn(source_id, 'userassist_absent', 'Explorer UserAssist key unavailable')
        return [], []
    keys, entries = [], []

    def warn(code, message, identity):
        report.warn(source_id, 'userassist_'+code, message, identity)

    def metadata(value):
        return dict(value_offset=value['offset']+4096, name=value['name'], type=value['type'], data_hex=value['raw'].hex())

    def add_key(key, path, role, parent=None, group=None, version=None):
        if len(keys) >= MAX_KEYS:
            raise AnalysisError('UserAssist key limit exceeded')
        identity = str(key['offset']+4096)
        keys.append(dict(source_id=source_id, record_id=identity, key_path=path, key_role=role,
                         parent_key_id=parent, group_guid=group, format_version=version,
                         key_last_written=filetime(key['ticks'], report, source_id, identity),
                         key_last_write_raw=str(key['ticks']), raw_values=[metadata(v) for v in hive.values(key)]))
        return identity

    root_id = add_key(root, KEY_PATH, 'root')
    children = hive.children(root)
    settings = next((k for k in children if k['name'].casefold() == 'settings'), None)
    name_encoding = 'rot13'
    if settings is not None:
        identity = add_key(settings, KEY_PATH+'\\'+settings['name'], 'settings', root_id)
        if settings['count']:
            warn('nested_keys', 'Settings subkeys are not traversed', identity)
        controls = [v for v in hive.values(settings) if v['name'].casefold() == 'noencrypt']
        if controls:
            control = controls[0]
            if control['type'] == 4 and len(control['raw']) == 4 and int.from_bytes(control['raw'], 'little') in (0, 1):
                name_encoding = 'plain' if int.from_bytes(control['raw'], 'little') else 'rot13'
            else:
                name_encoding = 'unknown'
                warn('invalid_noencrypt', 'Invalid NoEncrypt; names retained without decoded candidates', identity)
    groups = [key for key in children if key is not settings]
    if len(groups)*2+len(keys) > MAX_KEYS:
        raise AnalysisError('UserAssist scope limit exceeded')
    for group in groups:
        path = KEY_PATH+'\\'+group['name']
        if not GUID.fullmatch(group['name']):
            warn('unsupported_scope', 'Non-GUID child not traversed: '+group['name'], root_id)
            continue
        versions = [v for v in hive.values(group) if v['name'].casefold() == 'version']
        version = None
        if versions and versions[0]['type'] == 4 and len(versions[0]['raw']) == 4:
            version = int.from_bytes(versions[0]['raw'], 'little')
        group_id = add_key(group, path, 'group', root_id, group['name'], version)
        if version not in (3, 5):
            warn('unsupported_version', 'Missing, invalid or unsupported Version; no size-based guessing', group_id)
        count = None
        for child in hive.children(group):
            if child['name'].casefold() == 'count':
                count = child
            else:
                warn('unsupported_scope', 'Only direct Count subkey is supported: '+child['name'], group_id)
        if count is None:
            warn('missing_count', 'GUID has no Count subkey', group_id)
            continue
        path += '\\'+count['name']
        key_id = add_key(count, path, 'count', group_id, group['name'], version)
        if count['count']:
            warn('nested_keys', 'Count descendants are not traversed', key_id)
        for value in hive.values(count):
            if len(entries) >= MAX_ENTRIES:
                raise AnalysisError('UserAssist entry limit exceeded')
            identity = str(value['offset']+4096)
            name = codecs.decode(value['name'], 'rot13') if name_encoding == 'rot13' else value['name'] if name_encoding == 'plain' else None
            raw = value['raw']
            row = dict(source_id=source_id, record_id=identity, key_id=key_id, key_path=path,
                       group_guid=group['name'], format_version=version, value_name=value['name'],
                       name_encoding=name_encoding, decoded_name=name, value_type=value['type'],
                       status=None, first_dword_raw=None, run_count_raw=None, focus_count_raw=None,
                       focus_time_raw=None, last_run_at=None, last_run_filetime_raw=None,
                       opaque_data_hex=None, value_data_hex=raw.hex())
            if name is not None and name.casefold() == 'ueme_ctlsession':
                row['status'] = 'session_control'
                warn('session_control', 'Session control retained opaque; not an execution entry', identity)
            elif version not in (3, 5):
                row['status'] = 'unsupported_version'
            elif value['type'] != 3:
                row['status'] = 'wrong_type'
                warn('wrong_type', 'Count value is not REG_BINARY; raw data retained', identity)
            elif len(raw) != (16 if version == 3 else 72):
                row['status'] = 'wrong_size'
                warn('wrong_size', 'Value size does not match declared Version; no prefix recovery', identity)
            elif name is None:
                row['status'] = 'unknown_name_encoding'
                warn('unknown_name_encoding', 'Cannot distinguish control from entry; data retained opaque', identity)
            else:
                row['status'] = 'parsed'
                row['first_dword_raw'] = int.from_bytes(raw[:4], 'little')
                row['run_count_raw'] = int.from_bytes(raw[4:8], 'little')
                offset = 8 if version == 3 else 60
                ticks = int.from_bytes(raw[offset:offset+8], 'little')
                row['last_run_filetime_raw'] = str(ticks)
                row['last_run_at'] = filetime(ticks, report, source_id, identity)
                if version == 5:
                    row['focus_count_raw'] = int.from_bytes(raw[8:12], 'little')
                    row['focus_time_raw'] = int.from_bytes(raw[12:16], 'little')
                    row['opaque_data_hex'] = (raw[16:60]+raw[68:72]).hex()
                else:
                    row['opaque_data_hex'] = ''
            if row['status'] != 'parsed':
                row['opaque_data_hex'] = raw.hex()
            entries.append(row)
    if len(json.dumps([keys, entries], ensure_ascii=False).encode('utf-8')) > MAX_OUTPUT_BYTES:
        raise AnalysisError('UserAssist output limit exceeded')
    return keys, entries
