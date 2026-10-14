"""Private subprocess bridge; no evidence execution or Windows API calls."""
import json
from pathlib import Path
import sys

from .evtx import MAX_EVTX_BYTES, MAX_XML_BYTES, MAX_DECODED_BYTES, envelopes
from .model import Report


def main(argv=None):
    input_path, output_path, failure_path = map(Path, argv or sys.argv[1:])
    try:
        from Evtx.Evtx import ChunkHeader, Record
        with input_path.open("rb") as stream:
            data = stream.read(MAX_EVTX_BYTES+1)
        records = envelopes(data, Report(), 1)
        total, cached_index, chunk = 0, None, None
        with output_path.open("xb") as output:
            for item in records:
                index = item["chunk_index"]
                if index != cached_index:
                    start = 4096+index*65536
                    # BinXML references may share the chunk, but cannot read another chunk.
                    buffer = data[start:start+65536]
                    chunk = ChunkHeader(buffer, 0)
                    cached_index = index
                offset = item["record_offset"] - (4096+index*65536)
                xml = Record(buffer, offset, chunk).xml()
                if len(xml.encode("utf-8")) > MAX_XML_BYTES:
                    raise ValueError("record XML exceeds 1 MiB")
                row = json.dumps(dict(record_offset=item["record_offset"], xml=xml), ensure_ascii=False).encode("utf-8")+b"\n"
                total += len(row)
                if total > MAX_DECODED_BYTES:
                    raise ValueError("decoded output exceeds 32 MiB")
                output.write(row)
        return 0
    except Exception as error:
        failure_path.write_text(f"{type(error).__name__}: {str(error)[:1024]}", encoding="utf-8", errors="replace")
        return 2


if __name__ == "__main__":
    sys.exit(main())
