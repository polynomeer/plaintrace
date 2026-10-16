"""Bound SQLite inserts and exclusive publication of complete output files."""
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from .evidence import AnalysisError

TABLES = {
    "sources": "source_id INTEGER PRIMARY KEY, path TEXT, browser TEXT, schema_family TEXT, database_sha256 TEXT, wal_sha256 TEXT, source_kind TEXT, sha256 TEXT",
    "visits": "source_id INTEGER, browser TEXT, record_id TEXT, source_table TEXT, record_kind TEXT, url TEXT, title TEXT, visited_at TEXT, timestamp_raw TEXT, timestamp_unit TEXT, transition INTEGER",
    "keywords": "source_id INTEGER, browser TEXT, record_id TEXT, source_table TEXT, derivation TEXT, visit_record_id TEXT, parameter TEXT, keyword TEXT, url TEXT, searched_at TEXT, time_basis TEXT",
    "downloads": "source_id INTEGER, browser TEXT, record_id TEXT, source_table TEXT, record_kind TEXT, path TEXT, destination_uri TEXT, url TEXT, url_chain TEXT, referrer TEXT, state INTEGER, started_at TEXT, ended_at TEXT, start_time_raw TEXT, end_time_raw TEXT, start_time_unit TEXT, end_time_unit TEXT, start_time_basis TEXT, received_bytes INTEGER, total_bytes INTEGER, metadata_raw TEXT, annotation_ids TEXT, start_visit_id INTEGER",
    "links": "source_id INTEGER, record_id TEXT, link_flags INTEGER, file_attributes INTEGER, target_size INTEGER, created_at TEXT, accessed_at TEXT, written_at TEXT, filetimes_raw TEXT, local_base_path TEXT, common_path_suffix TEXT, network_share TEXT, volume TEXT, name TEXT, relative_path TEXT, working_directory TEXT, arguments TEXT, icon_location TEXT, target_candidates TEXT, tracker TEXT, environment_target TEXT, id_list_hex TEXT, extra_blocks TEXT",
    "prefetch": "source_id INTEGER, record_id TEXT, version INTEGER, compressed INTEGER, layout INTEGER, executable TEXT, prefetch_hash TEXT, file_size INTEGER, run_count INTEGER, last_run_times TEXT, last_run_times_raw TEXT, referenced_files TEXT, executable_path_candidates TEXT, volumes TEXT, metrics_count INTEGER, trace_count INTEGER, unparsed_sections TEXT",
    "diagnostics": "source_id INTEGER, severity TEXT, code TEXT, message TEXT, record_id TEXT",
    "recycle_bin": "source_id INTEGER, record_id TEXT, version INTEGER, original_size TEXT, deleted_at TEXT, deletion_filetime_raw TEXT, original_path TEXT, path_length_units INTEGER, path_utf16_hex TEXT, trailing_data_hex TEXT",
    "usb_registry": "source_id INTEGER, record_id TEXT, hive_role TEXT, observation_kind TEXT, key_path TEXT, key_last_written TEXT, key_last_write_raw TEXT, control_set TEXT, device_id TEXT, instance_id TEXT, vendor TEXT, product TEXT, revision TEXT, vid TEXT, pid TEXT, friendly_name TEXT, device_times TEXT, values_json TEXT",
    "recent_doc_keys": "source_id INTEGER, record_id TEXT, key_path TEXT, category TEXT, key_last_written TEXT, key_last_write_raw TEXT, mru_format TEXT, mru_status TEXT, mru_order TEXT, mru_values TEXT, other_values TEXT",
    "recent_docs": "source_id INTEGER, record_id TEXT, key_id TEXT, key_path TEXT, category TEXT, value_name TEXT, value_type INTEGER, mru_rank INTEGER, document_name TEXT, name_utf16_hex TEXT, trailing_data_hex TEXT, value_data_hex TEXT",
    "application_mru_keys": "source_id INTEGER, record_id TEXT, key_path TEXT, family TEXT, application TEXT, application_version TEXT, scope TEXT, list_kind TEXT, key_role TEXT, key_last_written TEXT, key_last_write_raw TEXT, metadata_values TEXT",
    "application_mru": "source_id INTEGER, record_id TEXT, key_id TEXT, key_path TEXT, family TEXT, application TEXT, application_version TEXT, scope TEXT, list_kind TEXT, slot_name TEXT, slot_number INTEGER, value_name TEXT, value_type INTEGER, raw_text TEXT, stored_path TEXT, path_basis TEXT, metadata_tokens TEXT, embedded_filetime_raw TEXT, embedded_at TEXT, value_data_hex TEXT",
    "jump_lists": "source_id INTEGER, record_id TEXT, container_kind TEXT, version INTEGER, app_id_hint TEXT, header_hex TEXT, container_header_hex TEXT, declared_entries INTEGER, declared_pinned INTEGER, streams TEXT, categories TEXT, trailing_data_hex TEXT",
    "jump_list_entries": "source_id INTEGER, record_id TEXT, container_id TEXT, entry_index INTEGER, stream_name TEXT, link_stream_name TEXT, stream_offset INTEGER, file_offset INTEGER, directory_id INTEGER, category_index INTEGER, entry_number TEXT, association TEXT, stored_path TEXT, path_utf16_hex TEXT, hostname TEXT, hostname_hex TEXT, droids TEXT, last_modified_at TEXT, last_modified_filetime_raw TEXT, pin_status INTEGER, pinned INTEGER, metadata_hex TEXT, extension_hex TEXT, raw_entry_hex TEXT, link_status TEXT, link_representation TEXT, link TEXT, lnk_hex TEXT",
    "shellbag_views": "source_id INTEGER, record_id TEXT, hive_role TEXT, shell_root TEXT, key_path TEXT, parent_key_id TEXT, slot_name TEXT, key_last_written TEXT, key_last_write_raw TEXT, raw_values TEXT",
    "shellbag_keys": "source_id INTEGER, record_id TEXT, hive_role TEXT, shell_root TEXT, key_path TEXT, parent_key_id TEXT, parent_entry_id TEXT, depth INTEGER, hierarchy_slots TEXT, path_candidate TEXT, path_basis TEXT, ancestry_complete INTEGER, key_last_written TEXT, key_last_write_raw TEXT, mru_status TEXT, mru_order TEXT, control_values TEXT, node_slot INTEGER, bag_key_id TEXT, other_values TEXT",
    "shellbag_entries": "source_id INTEGER, record_id TEXT, key_id TEXT, hive_role TEXT, shell_root TEXT, key_path TEXT, value_name TEXT, value_type INTEGER, mru_rank INTEGER, child_key_id TEXT, item_status TEXT, items TEXT, item_list_terminated INTEGER, item_trailing_hex TEXT, path_candidate TEXT, path_basis TEXT, ancestry_complete INTEGER, value_data_hex TEXT",
    "dialog_mru_keys": "source_id INTEGER, record_id TEXT, key_path TEXT, list_kind TEXT, category TEXT, parent_key_id TEXT, key_last_written TEXT, key_last_write_raw TEXT, mru_status TEXT, mru_order TEXT, control_values TEXT, other_values TEXT",
    "dialog_mru_entries": "source_id INTEGER, record_id TEXT, key_id TEXT, key_path TEXT, list_kind TEXT, category TEXT, value_name TEXT, value_type INTEGER, mru_rank INTEGER, application_name TEXT, application_utf16_hex TEXT, application_name_valid INTEGER, pidl_offset INTEGER, pidl_hex TEXT, pidl_status TEXT, items TEXT, item_list_terminated INTEGER, item_trailing_hex TEXT, path_candidate TEXT, path_basis TEXT, ancestry_complete INTEGER, value_data_hex TEXT",
    "userassist_keys": "source_id INTEGER, record_id TEXT, key_path TEXT, key_role TEXT, parent_key_id TEXT, group_guid TEXT, format_version INTEGER, key_last_written TEXT, key_last_write_raw TEXT, raw_values TEXT",
    "userassist_entries": "source_id INTEGER, record_id TEXT, key_id TEXT, key_path TEXT, group_guid TEXT, format_version INTEGER, value_name TEXT, name_encoding TEXT, decoded_name TEXT, value_type INTEGER, status TEXT, first_dword_raw INTEGER, run_count_raw INTEGER, focus_count_raw INTEGER, focus_time_raw INTEGER, last_run_at TEXT, last_run_filetime_raw TEXT, opaque_data_hex TEXT, value_data_hex TEXT",
    "events": "source_id INTEGER, record_id TEXT, chunk_index INTEGER, record_offset INTEGER, container_record_id TEXT, container_filetime_raw TEXT, event_record_id TEXT, event_id INTEGER, provider TEXT, provider_guid TEXT, channel TEXT, computer TEXT, level INTEGER, task INTEGER, opcode INTEGER, version INTEGER, qualifiers TEXT, keywords TEXT, process_id INTEGER, thread_id INTEGER, user_sid TEXT, activity_id TEXT, related_activity_id TEXT, created_at TEXT, time_created_raw TEXT, container_time TEXT, category TEXT, action TEXT, details TEXT, event_data TEXT, user_data_xml TEXT, xml TEXT",
}


def sqlite_report(report, path):
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        with connection:
            connection.execute("PRAGMA user_version=11")
            connection.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT)")
            payload = report.as_dict()
            for key in ("format_version", "tool", "tool_version", "counts"):
                connection.execute("INSERT INTO metadata VALUES (?,?)", (key, json.dumps(payload[key], ensure_ascii=False)))
            for table, declaration in TABLES.items():
                fk = "" if table == "sources" else ", FOREIGN KEY(source_id) REFERENCES sources(source_id)"
                if table in ('recent_doc_keys','application_mru_keys','jump_lists'):
                    fk += ', UNIQUE(source_id, record_id)'
                elif table == 'recent_docs':
                    fk += ', FOREIGN KEY(source_id, key_id) REFERENCES recent_doc_keys(source_id, record_id)'
                elif table == 'application_mru':
                    fk += ', FOREIGN KEY(source_id, key_id) REFERENCES application_mru_keys(source_id, record_id)'
                elif table == 'jump_list_entries':
                    fk += ', FOREIGN KEY(source_id, container_id) REFERENCES jump_lists(source_id, record_id)'
                elif table == 'userassist_keys':
                    fk += ', UNIQUE(source_id, record_id), FOREIGN KEY(source_id, parent_key_id) REFERENCES userassist_keys(source_id, record_id)'
                elif table == 'userassist_entries':
                    fk += ', FOREIGN KEY(source_id, key_id) REFERENCES userassist_keys(source_id, record_id)'
                elif table == 'dialog_mru_keys':
                    fk += ', UNIQUE(source_id, record_id), FOREIGN KEY(source_id, parent_key_id) REFERENCES dialog_mru_keys(source_id, record_id)'
                elif table == 'dialog_mru_entries':
                    fk += ', FOREIGN KEY(source_id, key_id) REFERENCES dialog_mru_keys(source_id, record_id)'
                elif table in ('shellbag_views','shellbag_keys','shellbag_entries'):
                    fk += ', UNIQUE(source_id, record_id)'
                    if table in ('shellbag_views','shellbag_keys'):
                        fk += f', FOREIGN KEY(source_id, parent_key_id) REFERENCES {table}(source_id, record_id)'
                    if table == 'shellbag_keys':
                        fk += ', FOREIGN KEY(source_id, bag_key_id) REFERENCES shellbag_views(source_id, record_id)'
                        fk += ', FOREIGN KEY(source_id, parent_entry_id) REFERENCES shellbag_entries(source_id, record_id) DEFERRABLE INITIALLY DEFERRED'
                    elif table == 'shellbag_entries':
                        fk += ', FOREIGN KEY(source_id, key_id) REFERENCES shellbag_keys(source_id, record_id)'
                        fk += ', FOREIGN KEY(source_id, child_key_id) REFERENCES shellbag_keys(source_id, record_id)'
                connection.execute(f'CREATE TABLE "{table}" ({declaration}{fk})')
            # Deferred ShellBags references require every target table to exist before inserts.
            for table, declaration in TABLES.items():
                names = [column.split()[0] for column in declaration.split(",")]
                rows = []
                for record in getattr(report, table):
                    row = [record["values" if name=="values_json" else name] for name in names]
                    for i,value in enumerate(row):
                        if isinstance(value,(list,dict)):
                            row[i] = json.dumps(value,ensure_ascii=False,allow_nan=False)
                    rows.append(row)
                placeholders = ",".join("?" for _ in names)
                connection.executemany(f'INSERT INTO "{table}" VALUES ({placeholders})', rows)
    finally:
        connection.close()


def ensure_new_output(destination, format_name):
    if destination.exists() or destination.is_symlink():
        raise AnalysisError(f"Output already exists: {destination}; use a new path")
    if format_name == "sqlite":
        for suffix in ("-wal", "-shm", "-journal"):
            sidecar = Path(str(destination) + suffix)
            if sidecar.exists() or sidecar.is_symlink():
                raise AnalysisError(f"Output SQLite sidecar already exists: {sidecar}; use a new base path")


def write_report(report, output, format_name="json"):
    if format_name not in ("json", "sqlite"):
        raise AnalysisError(f"Unsupported output format: {format_name}")
    requested = Path(output).expanduser()
    # Resolve parent links, but never follow an existing final symlink (even a dangling one).
    destination = requested.parent.resolve() / requested.name
    ensure_new_output(destination, format_name)
    # Even absent WAL/SHM names are reserved against collision with evidence paths.
    protected = {Path(source["path"] + suffix).resolve()
                 for source in report.sources for suffix in ("", "-wal", "-shm", "-journal")}
    if destination in protected:
        raise AnalysisError("Output would collide with input evidence or its SQLite sidecars")
    descriptor, temporary = tempfile.mkstemp(prefix=".plaintrace-", dir=destination.parent)
    os.close(descriptor)
    temporary = Path(temporary)
    try:
        if format_name == "sqlite":
            sqlite_report(report, temporary)
        else:
            with temporary.open("w", encoding="utf-8", newline="\n") as stream:
                json.dump(report.as_dict(), stream, ensure_ascii=False, indent=2, allow_nan=False)
                stream.write("\n")
        # Hard-link publication fails rather than replacing a destination created
        # during analysis. Output filesystems must support hard links.
        ensure_new_output(destination, format_name)
        os.link(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
