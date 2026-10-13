"""Bound SQLite inserts and exclusive publication of complete output files."""
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from .evidence import AnalysisError

TABLES = {
    "sources": "source_id INTEGER PRIMARY KEY, path TEXT, browser TEXT, schema_family TEXT, database_sha256 TEXT, wal_sha256 TEXT",
    "visits": "source_id INTEGER, browser TEXT, record_id TEXT, source_table TEXT, record_kind TEXT, url TEXT, title TEXT, visited_at TEXT, timestamp_raw TEXT, timestamp_unit TEXT, transition INTEGER",
    "keywords": "source_id INTEGER, browser TEXT, record_id TEXT, source_table TEXT, derivation TEXT, visit_record_id TEXT, parameter TEXT, keyword TEXT, url TEXT, searched_at TEXT, time_basis TEXT",
    "downloads": "source_id INTEGER, browser TEXT, record_id TEXT, source_table TEXT, record_kind TEXT, path TEXT, destination_uri TEXT, url TEXT, url_chain TEXT, referrer TEXT, state INTEGER, started_at TEXT, ended_at TEXT, start_time_raw TEXT, end_time_raw TEXT, start_time_unit TEXT, end_time_unit TEXT, start_time_basis TEXT, received_bytes INTEGER, total_bytes INTEGER, metadata_raw TEXT",
    "diagnostics": "source_id INTEGER, severity TEXT, code TEXT, message TEXT, record_id TEXT",
}


def sqlite_report(report, path):
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        with connection:
            connection.execute("PRAGMA user_version=1")
            connection.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT)")
            payload = report.as_dict()
            for key in ("format_version", "tool", "tool_version", "counts"):
                connection.execute("INSERT INTO metadata VALUES (?,?)", (key, json.dumps(payload[key], ensure_ascii=False)))
            for table, declaration in TABLES.items():
                fk = "" if table == "sources" else ", FOREIGN KEY(source_id) REFERENCES sources(source_id)"
                connection.execute(f'CREATE TABLE "{table}" ({declaration}{fk})')
                names = [column.split()[0] for column in declaration.split(",")]
                rows = []
                for record in getattr(report, table):
                    row = [record[name] for name in names]
                    if table == "downloads":
                        row[names.index("url_chain")] = json.dumps(record["url_chain"], ensure_ascii=False)
                    rows.append(row)
                placeholders = ",".join("?" for _ in names)
                connection.executemany(f'INSERT INTO "{table}" VALUES ({placeholders})', rows)
    finally:
        connection.close()


def write_report(report, output, format_name="json"):
    destination = Path(output).expanduser().resolve()
    if destination.exists():
        raise AnalysisError(f"Output already exists: {destination}; use a new path")
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
                json.dump(report.as_dict(), stream, ensure_ascii=False, indent=2)
                stream.write("\n")
        # Hard-link publication fails rather than replacing a destination created
        # during analysis. Output filesystems must support hard links.
        os.link(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
