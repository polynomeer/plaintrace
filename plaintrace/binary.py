"""Bounded binary access, stable acquired-file reads and FILETIME conversion."""
import hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone

from .evidence import AnalysisError

MAX_ARTIFACT_BYTES = 8 * 1024 * 1024


class Binary:
    def __init__(self, data, label="artifact"):
        self.data, self.label = data, label

    def take(self, offset, size):
        if offset < 0 or size < 0 or offset > len(self.data) - size:
            raise AnalysisError(f"{self.label}: invalid/truncated range {offset}+{size}")
        return self.data[offset:offset+size]

    def number(self, offset, size):
        return int.from_bytes(self.take(offset, size), "little")

    def section(self, offset, size):
        return Binary(self.take(offset, size), self.label)

    def text(self, data, encoding, report, source_id):
        try:
            return data.decode(encoding)
        except UnicodeError:
            report.warn(source_id, "invalid_artifact_text", f"Invalid {encoding}; undecodable bytes escaped")
            return data.decode(encoding, errors="backslashreplace")

    def ztext(self, offset, minimum, wide, encoding, report, source_id):
        width = 2 if wide else 1
        if offset < minimum or offset >= len(self.data):
            raise AnalysisError(f"{self.label}: invalid string offset {offset}")
        for end in range(offset, len(self.data)-width+1, width):
            if self.data[end:end+width] == b"\x00" * width:
                return self.text(self.take(offset, end-offset), encoding, report, source_id)
        raise AnalysisError(f"{self.label}: unterminated string")


def bounded_hash(path, limit=MAX_ARTIFACT_BYTES):
    if type(limit) is not int or limit <= 0:
        raise AnalysisError("Invalid artifact hash limit")
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(min(1024*1024,limit+1-total))
            if not chunk:
                break
            total += len(chunk)
            if total > limit:
                raise AnalysisError("Artifact exceeds bounded read size")
            digest.update(chunk)
    return digest.hexdigest()


def read_artifact(path, limit=MAX_ARTIFACT_BYTES):
    if type(limit) is not int or limit <= 0:
        raise AnalysisError("Invalid artifact read limit")
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise AnalysisError(f"Input is not a file: {path}")
    if path.stat().st_size > limit:
        raise AnalysisError(f"Artifact exceeds {limit} bytes: {path}")
    before = bounded_hash(path, limit)
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    digest = hashlib.sha256(data).hexdigest()
    after = bounded_hash(path, limit)
    if len(data) > limit or before != digest or after != digest:
        raise AnalysisError(f"Artifact changed while reading or exceeds size limit: {path}")
    return path, data, digest


def filetime(ticks, report, source_id, identity):
    if ticks == 0:
        return None
    try:
        return (datetime(1601,1,1,tzinfo=timezone.utc) + timedelta(microseconds=ticks // 10)).isoformat(timespec="microseconds").replace("+00:00", "Z")
    except OverflowError:
        report.warn(source_id, "invalid_filetime", "FILETIME outside datetime range; raw ticks retained", identity)
        return None
