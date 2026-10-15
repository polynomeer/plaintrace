"""Versioned output contract and explicit timestamp interpretation."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import re
from urllib.parse import unquote_plus, urlsplit

from . import __version__

EPOCHS = {
    "chromium_us": (datetime(1601, 1, 1, tzinfo=timezone.utc), 1),
    "unix_us": (datetime(1970, 1, 1, tzinfo=timezone.utc), 1),
    "unix_ms": (datetime(1970, 1, 1, tzinfo=timezone.utc), 1000),
}


@dataclass
class Report:
    sources: list = field(default_factory=list)
    visits: list = field(default_factory=list)
    keywords: list = field(default_factory=list)
    downloads: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)
    links: list = field(default_factory=list)
    prefetch: list = field(default_factory=list)
    events: list = field(default_factory=list)
    recycle_bin: list = field(default_factory=list)

    usb_registry: list = field(default_factory=list)

    recent_doc_keys: list = field(default_factory=list)
    recent_docs: list = field(default_factory=list)

    def warn(self, source_id, code, message, record_id=None):
        self.diagnostics.append(dict(source_id=source_id, severity="warning", code=code,
                                     message=message, record_id=record_id))

    def as_dict(self):
        return dict(format_version=6, tool="plaintrace", tool_version=__version__,
                    **self.__dict__, counts={name: len(getattr(self, name))
                    for name in ("sources", "visits", "keywords", "downloads", "diagnostics", "links", "prefetch", "events", "recycle_bin", "usb_registry", "recent_doc_keys", "recent_docs")})


def raw_text(value):
    return None if value is None else str(value)


def integer(value):
    """Never truncate floats or accept bools as evidence integers."""
    if type(value) is int:
        return value
    if isinstance(value, str) and re.fullmatch(r"-?[0-9]+", value):
        return int(value)
    raise ValueError("not an integer")


def timestamp(value, unit, report, source_id, record_id):
    if value is None:
        return None
    try:
        ticks = integer(value)
        if ticks == 0:
            return None  # Browser zero times are treated as unspecified.
        if ticks < 0:
            raise ValueError("negative browser time")
        epoch, scale = EPOCHS[unit]
        return (epoch + timedelta(microseconds=ticks * scale)).isoformat(timespec="microseconds").replace("+00:00", "Z")
    except (ValueError, OverflowError):
        report.warn(source_id, "invalid_timestamp", f"Invalid {unit} time: {value!r}", record_id)
        return None


def firefox_end_time(value, report, source_id, record_id):
    # Firefox annotation versions can store epoch milliseconds or JSON dates.
    if isinstance(value, str) and not re.fullmatch(r"-?[0-9]+", value):
        try:
            date = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if date.tzinfo is None:
                raise ValueError("missing timezone")
            return date.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"), "iso8601"
        except (ValueError, OverflowError):
            report.warn(source_id, "invalid_timestamp", f"Invalid ISO date: {value!r}", record_id)
            return None, "iso8601"
    return timestamp(value, "unix_ms", report, source_id, record_id), "unix_ms"


def query_keywords(visit, report):
    """Candidate query terms, not a claim that a search was actually performed."""
    url = visit["url"]
    if not isinstance(url, str):
        return
    try:
        query = urlsplit(url).query
        if re.search(r"%(?![0-9a-fA-F]{2})", query):
            report.warn(visit["source_id"], "malformed_url_escape", "Malformed percent escape retained literally", visit["record_id"])
    except (ValueError, UnicodeError) as error:
        report.warn(visit["source_id"], "invalid_query", str(error), visit["record_id"])
        return
    for ordinal, raw_pair in enumerate(query.split("&")):
        raw_parameter, _, raw_term = raw_pair.partition("=")
        try:
            parameter = unquote_plus(raw_parameter, encoding="utf-8", errors="strict")
            if parameter not in ("q", "query", "search_query"):
                continue
            term = unquote_plus(raw_term, encoding="utf-8", errors="strict")
        except UnicodeError as error:
            report.warn(visit["source_id"], "invalid_query", str(error), f'{visit["record_id"]}:query:{ordinal}')
            continue
        if term:
            report.keywords.append(dict(source_id=visit["source_id"], browser=visit["browser"],
                record_id=f'{visit["record_id"]}:query:{ordinal}', source_table=visit["source_table"],
                derivation="url_parameter", visit_record_id=visit["record_id"], parameter=parameter,
                keyword=term, url=url, searched_at=visit["visited_at"],
                time_basis=visit["record_kind"]))
