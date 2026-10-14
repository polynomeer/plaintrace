"""Strict EVTX envelopes, isolated optional BinXML decoding and event semantics."""
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zlib

from .binary import Binary, filetime
from .evidence import AnalysisError

MAX_EVTX_BYTES = 64 * 1024 * 1024
MAX_RECORDS = 100_000
MAX_XML_BYTES = 1024 * 1024
MAX_DECODED_BYTES = 32 * 1024 * 1024
DECODE_TIMEOUT = 60
DECODER_VERSION = "0.8.1"
EVENT_NAMESPACE = "http://schemas.microsoft.com/win/2004/08/events/event"


def envelopes(data, report, source_id):
    """Only declared physical chunks and allocated records; never carve slack."""
    if len(data) > MAX_EVTX_BYTES:
        raise AnalysisError("EVTX exceeds 64 MiB limit")
    b = Binary(data, "EVTX")
    if b.take(0, 8) != b"ElfFile\0" or b.number(32, 4) != 128:
        raise AnalysisError("Invalid EVTX file header")
    if (b.number(38, 2), b.number(36, 2)) not in ((3, 1), (3, 2)) or b.number(40, 2) != 4096:
        raise AnalysisError("Unsupported EVTX version/header layout")
    b.take(0, 4096)
    if zlib.crc32(data[:120]) != b.number(124, 4):
        raise AnalysisError("EVTX file header checksum mismatch")
    count = b.number(42, 4)
    if count > (len(data)-4096)//65536 or (len(data)-4096) % 65536:
        raise AnalysisError("EVTX chunk count or file alignment mismatch")
    flags = b.number(120, 4)
    if flags & ~3:
        raise AnalysisError("Unsupported EVTX file flags")
    if flags & 1:
        report.warn(source_id, "evtx_dirty", "Dirty EVTX: header may not describe all records; no recovery attempted")
    if len(data) != 4096 + count*65536:
        report.warn(source_id, "evtx_inactive_chunks", "Physical chunks beyond the declared count are omitted; no carving attempted")
    records = []
    for index in range(count):
        start = 4096 + index*65536
        chunk = b.section(start, 65536)
        if chunk.take(0, 8) != b"ElfChnk\0" or chunk.number(40, 4) != 128:
            raise AnalysisError(f"Invalid EVTX chunk header: {index}")
        end, last = chunk.number(48, 4), chunk.number(44, 4)
        if not 512 <= end <= 65536:
            raise AnalysisError("EVTX free-space offset outside chunk")
        if zlib.crc32(chunk.take(0, 120)+chunk.take(128, 384)) != chunk.number(124, 4):
            raise AnalysisError("EVTX chunk header checksum mismatch")
        if zlib.crc32(chunk.take(512, end-512)) != chunk.number(52, 4):
            raise AnalysisError("EVTX record data checksum mismatch")
        offset, previous = 512, 0
        while offset < end:
            if len(records) >= MAX_RECORDS:
                raise AnalysisError("EVTX record count limit exceeded")
            if chunk.take(offset, 4) != b"**\0\0":
                raise AnalysisError("Invalid EVTX record signature")
            size = chunk.number(offset+4, 4)
            if size < 28 or size > end-offset or size % 8:
                raise AnalysisError("Invalid EVTX record length/alignment")
            if chunk.number(offset+size-4, 4) != size:
                raise AnalysisError("EVTX record trailing length mismatch")
            records.append(dict(chunk_index=index, record_offset=start+offset,
                                container_record_id=str(chunk.number(offset+8, 8)),
                                container_filetime_raw=str(chunk.number(offset+16, 8))))
            previous, offset = offset, offset+size
        if last != previous:
            raise AnalysisError("EVTX last-record offset mismatch")
    return records


def decode_snapshot(data, records):
    """Decode a temporary copy, with timeout and bounded on-disk IPC."""
    try:
        installed = version("python-evtx")
    except PackageNotFoundError as error:
        raise AnalysisError('EVTX requires optional dependency: pip install ".[evtx]" (python-evtx==0.8.1)') from error
    if installed != DECODER_VERSION:
        raise AnalysisError(f"EVTX requires python-evtx=={DECODER_VERSION}; found {installed}")
    with tempfile.TemporaryDirectory(prefix="plaintrace-evtx-") as directory:
        snapshot = Path(directory)/"input.evtx"
        result = Path(directory)/"decoded.jsonl"
        failure = Path(directory)/"failure.txt"
        snapshot.write_bytes(data)
        # Use the same package as the caller even when run outside the checkout.
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent)
        try:
            completed = subprocess.run([sys.executable, "-m", "plaintrace.evtx_worker",
                                        str(snapshot), str(result), str(failure)],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                       timeout=DECODE_TIMEOUT, env=environment)
        except subprocess.TimeoutExpired as error:
            raise AnalysisError("EVTX BinXML decoder exceeded 60 second file timeout") from error
        if completed.returncode != 0:
            message = failure.read_bytes()[:2048].decode("utf-8", errors="replace") if failure.exists() else "worker terminated"
            raise AnalysisError(f"EVTX BinXML decoding failed: {message}")
        if not result.is_file() or result.stat().st_size > MAX_DECODED_BYTES:
            raise AnalysisError("EVTX decoded output missing or exceeds 32 MiB")
        decoded = []
        with result.open("rb") as stream:
            for expected in records:
                line = stream.readline(MAX_XML_BYTES*6+4096)
                try:
                    row = json.loads(line)
                except (ValueError, UnicodeError) as error:
                    raise AnalysisError("Invalid EVTX decoder output") from error
                if not isinstance(row, dict) or row.get("record_offset") != expected["record_offset"] or not isinstance(row.get("xml"), str):
                    raise AnalysisError("EVTX decoder record lineage mismatch")
                if len(row["xml"].encode("utf-8")) > MAX_XML_BYTES:
                    raise AnalysisError("EVTX record XML exceeds 1 MiB")
                decoded.append(row["xml"])
            if stream.read(1):
                raise AnalysisError("EVTX decoder produced extra records")
        return decoded


def event_time(value, report, source_id, record_id):
    if value is None:
        report.warn(source_id, "evtx_missing_time", "TimeCreated/SystemTime absent", record_id)
        return None
    try:
        # Preserve 100 ns text separately; datetime output truncates to microseconds.
        if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,7})?(?:Z|[+-]\d\d:\d\d)", value):
            raise ValueError("unsupported timestamp")
        if not value.endswith("Z"):
            hours, minutes = map(int, value[-5:].split(":"))
            if hours > 23 or minutes > 59:
                raise ValueError("invalid timezone")
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    except (ValueError, OverflowError):
        report.warn(source_id, "evtx_invalid_time", "Invalid XML SystemTime retained verbatim", record_id)
        return None


def parse_event(xml, envelope, report, source_id):
    identity = str(envelope["record_offset"])
    if not isinstance(xml, str) or len(xml.encode("utf-8")) > MAX_XML_BYTES:
        raise AnalysisError("EVTX record XML exceeds 1 MiB or is not text")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", xml, re.I):
        raise AnalysisError("EVTX XML declarations/entities unsupported")
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as error:
        raise AnalysisError("Invalid decoded EVTX XML") from error
    namespace = "{"+EVENT_NAMESPACE+"}" if root.tag == "{"+EVENT_NAMESPACE+"}Event" else ""
    if root.tag != namespace+"Event":
        raise AnalysisError("Unsupported EVTX XML root/namespace")
    stack, nodes = [(root, 1)], 0
    while stack:
        node, depth = stack.pop()
        nodes += 1
        if depth > 64 or nodes > 10_000:
            raise AnalysisError("EVTX XML depth/node limit exceeded")
        stack.extend((child, depth+1) for child in node)
    def one(parent, name):
        matches = parent.findall(namespace+name)
        if len(matches) > 1:
            raise AnalysisError(f"Ambiguous EVTX XML field: {name}")
        return matches[0] if matches else None
    system = one(root, "System")
    if system is None:
        raise AnalysisError("EVTX XML System missing")
    def text(name):
        node = one(system, name)
        return node.text if node is not None else None
    def attr(name, key):
        node = one(system, name)
        return node.get(key) if node is not None else None
    def number(value, field, maximum):
        if value is None:
            return None
        if not re.fullmatch(r"[0-9]{1,20}", value.strip()) or int(value) > maximum:
            report.warn(source_id, "evtx_invalid_number", f"Invalid {field}; rendered XML retained", identity)
            return None
        return int(value)
    event_id = number(text("EventID"), "EventID", 65535)
    event_record = number(text("EventRecordID"), "EventRecordID", 2**64-1)
    if text("EventID") is None or text("EventRecordID") is None:
        report.warn(source_id, "evtx_missing_identity", "XML EventID or EventRecordID absent; no identity inferred", identity)
    xml_time = attr("TimeCreated", "SystemTime")
    created = event_time(xml_time, report, source_id, identity)
    container_time = filetime(int(envelope["container_filetime_raw"]), report, source_id, identity)
    if created and container_time and created != container_time:
        report.warn(source_id, "evtx_time_mismatch", "XML TimeCreated and container FILETIME differ; both retained", identity)
    if event_record is not None and str(event_record) != envelope["container_record_id"]:
        report.warn(source_id, "evtx_record_id_mismatch", "XML and container record IDs differ; both retained", identity)
    event_data = []
    data_node = one(root, "EventData")
    if data_node is not None:
        for child in data_node:
            event_data.append(dict(name=child.get("Name") if child.tag == namespace+"Data" else None, value="".join(child.itertext()),
                                   xml=ET.tostring(child, encoding="unicode")))
    user_data = one(root, "UserData")
    provider, channel = attr("Provider", "Name"), text("Channel")
    category, action, details = "event", None, {}
    if provider == "Microsoft-Windows-Security-Auditing" and channel == "Security" and event_id in (4624, 4634, 4647):
        category = "logon"
        action = {4624: "logon", 4634: "logoff", 4647: "user_initiated_logoff"}[event_id]
        for output, name in (("user", "TargetUserName"), ("domain", "TargetDomainName"),
                             ("sid", "TargetUserSid"), ("logon_id", "TargetLogonId"),
                             ("logon_type", "LogonType"), ("ip_address", "IpAddress"),
                             ("logon_guid", "LogonGuid")):
            values = [item["value"] for item in event_data if item["name"] == name]
            details[output] = values[0] if len(values) == 1 else None
            if len(values) > 1:
                report.warn(source_id, "evtx_duplicate_data", f"Duplicate {name}; normalized value left null", identity)
    elif provider == "Microsoft-Windows-Kernel-General" and channel == "System" and event_id in (12, 13):
        category, action = "power", {12: "os_started", 13: "os_shutdown_started"}[event_id]
    elif provider == "Microsoft-Windows-DriverFrameworks-UserMode":
        category = "driver_frameworks"  # Not a USB connection-state assertion.
    return dict(source_id=source_id, record_id=identity, **envelope,
                event_record_id=None if event_record is None else str(event_record),
                event_id=event_id, provider=provider, provider_guid=attr("Provider", "Guid"),
                channel=channel, computer=text("Computer"), level=number(text("Level"), "Level", 255),
                task=number(text("Task"), "Task", 65535), opcode=number(text("Opcode"), "Opcode", 255),
                version=number(text("Version"), "Version", 255), qualifiers=attr("EventID", "Qualifiers"),
                keywords=text("Keywords"), process_id=number(attr("Execution", "ProcessID"), "ProcessID", 2**32-1),
                thread_id=number(attr("Execution", "ThreadID"), "ThreadID", 2**32-1),
                user_sid=attr("Security", "UserID"), activity_id=attr("Correlation", "ActivityID"),
                related_activity_id=attr("Correlation", "RelatedActivityID"), created_at=created,
                time_created_raw=xml_time, container_time=container_time, category=category, action=action,
                details=details, event_data=event_data,
                user_data_xml=ET.tostring(user_data, encoding="unicode") if user_data is not None else None,
                xml=xml)


def parse(data, source_id, report):
    records = envelopes(data, report, source_id)
    seen = set()
    for record in records:
        identity = record["container_record_id"]
        if identity in seen:
            report.warn(source_id, "evtx_duplicate_record_id", "Repeated container record ID; distinct offsets retained", str(record["record_offset"]))
        seen.add(identity)
    xml_records = decode_snapshot(data, records)
    if len(xml_records) != len(records):
        raise AnalysisError("EVTX decoder record count mismatch")
    return [parse_event(xml, record, report, source_id) for record, xml in zip(records, xml_records)]
