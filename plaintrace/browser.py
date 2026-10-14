"""Schema-aware browser adapters using only explicit, supported tables."""
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .evidence import AnalysisError, snapshot
from .model import Report, firefox_end_time, integer, query_keywords, raw_text, timestamp


def columns(db, table):
    # Names are fixed internal adapter identifiers; input never supplies SQL identifiers.
    entry = db.execute("SELECT type FROM sqlite_master WHERE name=?", (table,)).fetchone()
    if entry and entry["type"] != "table":
        raise AnalysisError(f"Unsupported {table}: expected a table, found {entry['type']}")
    return {row["name"] for row in db.execute(f'PRAGMA table_info("{table}")')}


def require(db, table, fields):
    available = columns(db, table)
    if not set(fields) <= available:
        raise AnalysisError(f"Unsupported {table} schema: missing {sorted(set(fields) - available)}")
    return available


def optional(fields, name, prefix=""):
    return f'{prefix}"{name}"' if name in fields else "NULL"


def visit_row(row, source, table, kind, unit, report):
    identity = f'{table}:{row["id"]}'
    raw = row["time"]
    visit = dict(source_id=source["source_id"], browser=source["browser"], record_id=identity,
                 source_table=table, record_kind=kind, url=row["url"], title=row["title"],
                 visited_at=timestamp(raw, unit, report, source["source_id"], identity),
                 timestamp_raw=raw_text(raw), timestamp_unit=unit, transition=row["transition"])
    report.visits.append(visit)
    query_keywords(visit, report)


def visits(db, source, report, firefox=False):
    base = "moz_places" if firefox else "urls"
    event = "moz_historyvisits" if firefox else "visits"
    foreign = "place_id" if firefox else "url"
    time_name = "visit_date" if firefox else "visit_time"
    last_name = "last_visit_date" if firefox else "last_visit_time"
    unit = "unix_us" if firefox else "chromium_us"
    fields = require(db, base, ("id", "url"))
    title = optional(fields, "title", "u.")
    if columns(db, event):
        event_fields = require(db, event, ("id", foreign, time_name))
        transition = optional(event_fields, "visit_type" if firefox else "transition", "v.")
        # LEFT JOIN retains orphaned events for diagnostic purposes.
        query = f'SELECT v.id, u.url, {title} AS title, v."{time_name}" AS time, {transition} AS transition FROM "{event}" v LEFT JOIN "{base}" u ON u.id=v."{foreign}" ORDER BY v.id'
        for row in db.execute(query):
            if row["url"] is None:
                report.warn(source["source_id"], "orphan_visit", "Visit has no matching URL", f'{event}:{row["id"]}')
            visit_row(row, source, event, "visit", unit, report)
    else:
        require(db, base, (last_name,))
        report.warn(source["source_id"], "url_summary_only", f"{event} absent; emitting URL last-visit summaries, not individual visits")
        query = f'SELECT u.id, u.url, {title} AS title, u."{last_name}" AS time, NULL AS transition FROM "{base}" u ORDER BY u.id'
        for row in db.execute(query):
            visit_row(row, source, base, "url_summary", unit, report)


def chromium_keywords(db, source, report):
    fields = columns(db, "keyword_search_terms")
    if not fields:
        return
    require(db, "keyword_search_terms", ("url_id", "term"))
    url_fields = columns(db, "urls")
    last = optional(url_fields, "last_visit_time", "u.")
    keyword_id = optional(fields, "keyword_id", "k.")
    query = f'SELECT k.url_id, k.term, {keyword_id} AS keyword_id, u.url, {last} AS time FROM keyword_search_terms k LEFT JOIN urls u ON k.url_id=u.id ORDER BY k.url_id, keyword_id, k.term'
    for ordinal, row in enumerate(db.execute(query)):
        identity = f'keyword_search_terms:{row["url_id"]}:{row["keyword_id"]}:{ordinal}'
        if row["url"] is None:
            report.warn(source["source_id"], "orphan_keyword", "Stored term has no matching URL", identity)
        report.keywords.append(dict(source_id=source["source_id"], browser=source["browser"],
            record_id=identity, source_table="keyword_search_terms", derivation="stored_search_term",
            visit_record_id=None, parameter=None, keyword=row["term"], url=row["url"],
            searched_at=timestamp(row["time"], "chromium_us", report, source["source_id"], identity),
            time_basis="url_summary"))


def numeric(value, report, source_id, identity, field):
    if value is None:
        return None
    try:
        result = integer(value)
        if not -(2**63) <= result < 2**63:
            raise ValueError("outside SQLite integer range")
        return result
    except ValueError:
        report.warn(source_id, "invalid_numeric_field", f"Invalid {field}: {value!r}", identity)
        return None


def check_download_times(record, report):
    start, end = record["started_at"], record["ended_at"]
    if start and end and end < start:
        report.warn(record["source_id"], "inconsistent_download_times",
                    "End time precedes start time; raw values retained", record["record_id"])


def chromium_downloads(db, source, report):
    fields = columns(db, "downloads")
    if not fields:
        report.warn(source["source_id"], "downloads_unavailable", "downloads table absent")
        return
    require(db, "downloads", ("id", "start_time"))
    if not {"target_path", "current_path"} & fields:
        raise AnalysisError("Unsupported Chromium downloads schema: target_path/current_path required")
    chains = {}
    if columns(db, "downloads_url_chains"):
        require(db, "downloads_url_chains", ("id", "chain_index", "url"))
        for row in db.execute("SELECT id, url FROM downloads_url_chains ORDER BY id, chain_index"):
            chains.setdefault(row["id"], []).append(row["url"])
    else:
        report.warn(source["source_id"], "download_chain_unavailable", "Download URL chains absent; direct url retained if present")
    names = ("target_path", "current_path", "end_time", "received_bytes", "total_bytes", "referrer", "url", "state")
    query = 'SELECT id,start_time,' + ','.join(f'{optional(fields, name)} AS "{name}"' for name in names) + ' FROM downloads ORDER BY id'
    for row in db.execute(query):
        identity = f'downloads:{row["id"]}'
        chain = chains.get(row["id"], [])
        if not chain and row["url"] is None:
            report.warn(source["source_id"], "download_url_missing", "No URL chain or direct download URL", identity)
        report.downloads.append(dict(source_id=source["source_id"], browser=source["browser"],
            record_id=identity, source_table="downloads", record_kind="download", path=row["target_path"] or row["current_path"],
            destination_uri=None, url=chain[-1] if chain else row["url"], url_chain=chain,
            referrer=row["referrer"], state=numeric(row["state"], report, source["source_id"], identity, "state"),
            started_at=timestamp(row["start_time"], "chromium_us", report, source["source_id"], identity),
            ended_at=timestamp(row["end_time"], "chromium_us", report, source["source_id"], identity),
            start_time_raw=raw_text(row["start_time"]), end_time_raw=raw_text(row["end_time"]),
            start_time_unit="chromium_us", end_time_unit="chromium_us", start_time_basis="download_start",
            received_bytes=numeric(row["received_bytes"], report, source["source_id"], identity, "received_bytes"), total_bytes=numeric(row["total_bytes"], report, source["source_id"], identity, "total_bytes"), metadata_raw=None, annotation_ids={}, start_visit_id=None))
        check_download_times(report.downloads[-1], report)


def destination_path(uri, report, source_id, identity):
    if uri is None:
        return None
    try:
        parts = urlsplit(uri)
        if parts.scheme != "file":
            raise ValueError("Destination is not a file URI")
        path = unquote(parts.path, encoding="utf-8", errors="strict")
        if parts.netloc and parts.netloc != "localhost":
            path = "//" + parts.netloc + path
        elif len(path) >= 3 and path[0] == "/" and path[2] == ":":
            path = path[1:]
        return path
    except (ValueError, UnicodeError, TypeError) as error:
        report.warn(source_id, "invalid_destination", str(error), identity)
        return None


def firefox_downloads(db, source, report):
    if not columns(db, "moz_annos") or not columns(db, "moz_anno_attributes"):
        report.warn(source["source_id"], "downloads_unavailable", "Firefox download annotation tables absent")
        return
    fields = require(db, "moz_annos", ("id", "place_id", "anno_attribute_id", "content"))
    require(db, "moz_anno_attributes", ("id", "name"))
    added, modified = optional(fields, "dateAdded", "a."), optional(fields, "lastModified", "a.")
    query = f'SELECT a.id,a.place_id,a.content,n.name,{added} AS added,{modified} AS modified,p.url FROM moz_annos a JOIN moz_anno_attributes n ON n.id=a.anno_attribute_id LEFT JOIN moz_places p ON p.id=a.place_id WHERE n.name IN (?,?) ORDER BY a.place_id, COALESCE({modified}, {added}, 0),a.id'
    groups = {}
    for row in db.execute(query, ("downloads/destinationFileURI", "downloads/metaData")):
        group = groups.setdefault(row["place_id"], {})
        if row["name"] in group:
            report.warn(source["source_id"], "duplicate_annotation", "Latest annotation selected by modification time then ID", f'moz_annos:{row["id"]}')
        group[row["name"]] = dict(row)
    for place_id, group in groups.items():
        destination = group.get("downloads/destinationFileURI")
        metadata = group.get("downloads/metaData")
        base = destination or metadata
        identity = f'moz_annos:place:{place_id}'
        raw = metadata["content"] if metadata else None
        if base["url"] is None:
            report.warn(source["source_id"], "orphan_download", "Annotations have no matching URL", identity)
        parsed = {}
        if metadata:
            try:
                parsed = json.loads(raw)
                if not isinstance(parsed, dict):
                    raise ValueError("Metadata is not a JSON object")
            except (ValueError, TypeError, RecursionError):
                parsed = {}
                report.warn(source["source_id"], "invalid_download_metadata", "Invalid Firefox metadata retained", identity)
        if not destination or not metadata:
            report.warn(source["source_id"], "incomplete_download", "Destination or metadata annotation missing", identity)
        start = base["added"]
        basis = "annotation_date_added"
        start_visit_id = None
        history = columns(db, "moz_historyvisits")
        if {"place_id", "visit_date", "visit_type", "id"} <= history:
            row = db.execute("SELECT id, visit_date FROM moz_historyvisits WHERE place_id=? AND visit_type=7 ORDER BY visit_date DESC,id DESC LIMIT 1", (place_id,)).fetchone()
            if row:
                start, basis = row["visit_date"], "latest_download_visit"
                start_visit_id = row["id"]
        end = parsed.get("endTime")
        ended_at, end_unit = firefox_end_time(end, report, source["source_id"], identity)
        uri = destination["content"] if destination else None
        report.downloads.append(dict(source_id=source["source_id"], browser=source["browser"],
            record_id=identity, source_table="moz_annos", record_kind="annotation_summary", path=destination_path(uri, report, source["source_id"], identity),
            destination_uri=uri, url=base["url"], url_chain=[], referrer=None, state=numeric(parsed.get("state"), report, source["source_id"], identity, "state"),
            started_at=timestamp(start, "unix_us", report, source["source_id"], identity), ended_at=ended_at,
            start_time_raw=raw_text(start), end_time_raw=raw_text(end), start_time_unit="unix_us", end_time_unit=end_unit,
            start_time_basis=basis, received_bytes=None, total_bytes=numeric(parsed.get("fileSize"), report, source["source_id"], identity, "fileSize"), metadata_raw=raw,
            annotation_ids={name: row["id"] for name, row in group.items()}, start_visit_id=start_visit_id))
        check_download_times(report.downloads[-1], report)


def analyze(paths, browser="auto"):
    report = Report()
    for index, path in enumerate(paths, 1):
        with snapshot(path) as (db, hashes):
            if columns(db, "urls") and columns(db, "moz_places"):
                raise AnalysisError(f"Ambiguous browser schema: {path}")
            if columns(db, "moz_places"):
                family = "firefox"
            elif columns(db, "urls"):
                family = "chromium"
            else:
                raise AnalysisError(f"Unsupported browser schema: {path}")
            if browser != "auto" and ((family == "firefox") != (browser == "firefox")):
                raise AnalysisError(f"Browser label {browser} conflicts with {family} schema: {path}")
            source = dict(source_id=index, path=str(Path(path).expanduser().resolve()),
                          browser=family if browser == "auto" else browser, schema_family=family, source_kind="browser", sha256=hashes["database_sha256"], **hashes)
            report.sources.append(source)
            visits(db, source, report, family == "firefox")
            if family == "firefox":
                firefox_downloads(db, source, report)
            else:
                chromium_keywords(db, source, report)
                chromium_downloads(db, source, report)
    return report
