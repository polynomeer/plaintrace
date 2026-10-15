"""Bounded $Recycle.Bin $I metadata parsing; no $R or filesystem inference."""
from .binary import Binary, filetime
from .evidence import AnalysisError

MAX_RECYCLE_BYTES = 128 * 1024
MAX_PATH_UNITS = 32768


def parse(data, source_id, report):
    if len(data) > MAX_RECYCLE_BYTES:
        raise AnalysisError("Recycle Bin $I exceeds 128 KiB input limit")
    binary = Binary(data, "Recycle Bin $I")
    version = binary.number(0, 8)
    if version not in (1, 2):
        raise AnalysisError(f"Unsupported Recycle Bin $I version: {version}")
    original_size = binary.number(8, 8)
    ticks = binary.number(16, 8)
    if version == 1:
        path_units, offset, length = None, 24, 520
    else:
        path_units = binary.number(24, 4)
        if not 1 <= path_units <= MAX_PATH_UNITS:
            raise AnalysisError("Recycle Bin $I path length outside 1..32768 UTF-16 units")
        offset, length = 28, path_units*2
    raw_path = binary.take(offset, length)
    terminator = next((position for position in range(0, length, 2)
                       if raw_path[position:position+2] == b"\0\0"), None)
    if terminator is None:
        raise AnalysisError("Recycle Bin $I path has no aligned UTF-16 terminator")
    if version == 2 and terminator != length-2:
        report.warn(source_id, "recycle_path_length_mismatch", "Path terminates before declared UTF-16 length; raw field retained", "0")
    if any(raw_path[terminator+2:]):
        report.warn(source_id, "recycle_path_padding", "Nonzero bytes after path terminator; not interpreted as part of path", "0")
    original_path = binary.text(raw_path[:terminator], "utf-16-le", report, source_id)
    if not original_path:
        report.warn(source_id, "recycle_empty_path", "Empty original path; deletion metadata retained", "0")
    extra = data[offset+length:]
    if extra:
        report.warn(source_id, "recycle_trailing_data", "Bytes beyond supported $I layout retained without interpretation", "0")
    if ticks == 0:
        report.warn(source_id, "recycle_missing_deletion_time", "Zero deletion FILETIME is unspecified", "0")
    return dict(source_id=source_id, record_id="0", version=version,
                original_size=str(original_size), deleted_at=filetime(ticks, report, source_id, "0"),
                deletion_filetime_raw=str(ticks), original_path=original_path,
                path_length_units=path_units, path_utf16_hex=raw_path.hex(),
                trailing_data_hex=extra.hex())
