"""Version-checked SCCA metadata and bounded MAM04 XPRESS Huffman decoding."""
import ntpath

from .binary import Binary, MAX_ARTIFACT_BYTES, filetime
from .evidence import AnalysisError
from .xpress import decompress

LAYOUTS = {17: (152,36,60,1,20,40),23: (240,44,68,1,32,104),
           26: (304,44,124,8,32,104),31: (296,44,116,8,32,96)}


def parse(data, source_id, report):
    compressed = data[:3] == b"MAM"
    if compressed:
        mam = Binary(data,"MAM Prefetch")
        if mam.take(0,4) != b"MAM\x04":
            raise AnalysisError("Unsupported MAM flags/checksum variant")
        expected = mam.number(4,4)
        if expected < 84 or expected > MAX_ARTIFACT_BYTES:
            raise AnalysisError("MAM advertised output size outside limits")
        data = decompress(data[8:],expected)
    pf = Binary(data,"Prefetch")
    pf.take(0,84)
    version = pf.number(0,4)
    if pf.take(4,4) != b"SCCA":
        raise AnalysisError("Not an SCCA Prefetch")
    if pf.number(12,4) != len(data):
        raise AnalysisError("Prefetch declared file size differs from payload")
    metrics_offset = pf.number(84,4)
    if version == 30:
        if metrics_offset not in (304,296):
            raise AnalysisError("Unsupported Prefetch v30 layout")
        layout = (metrics_offset,44,124 if metrics_offset==304 else 116,8,32,96)
    else:
        layout = LAYOUTS.get(version)
    if layout is None or metrics_offset != layout[0]:
        raise AnalysisError(f"Unsupported Prefetch version/layout: {version}/{metrics_offset}")
    header_end,time_offset,count_offset,slots,metric_size,volume_size = layout
    pf.take(0,header_end)
    exe = pf.section(16,60).ztext(0,0,True,"utf-16-le",report,source_id)
    metrics_count = pf.number(88,4)
    pf.take(metrics_offset,metrics_count*metric_size)
    trace_offset,trace_count = pf.number(92,4),pf.number(96,4)
    strings_offset,strings_size = pf.number(100,4),pf.number(104,4)
    volume_offset,volume_count,volume_bytes = pf.number(108,4),pf.number(112,4),pf.number(116,4)
    for offset,size,name in ((trace_offset,trace_count*(8 if version>=30 else 12),"traces"),
                             (strings_offset,strings_size,"strings"),(volume_offset,volume_bytes,"volumes")):
        if size and offset < header_end:
            raise AnalysisError(f"Prefetch {name} overlaps header")
        pf.take(offset,size)
    ranges = [(metrics_offset, metrics_count*metric_size),
              (trace_offset,trace_count*(8 if version>=30 else 12)),
              (strings_offset,strings_size),(volume_offset,volume_bytes)]
    occupied = sorted((start,start+size) for start,size in ranges if size)
    if any(right[0] < left[1] for left,right in zip(occupied,occupied[1:])):
        raise AnalysisError("Prefetch known sections overlap")
    if strings_size % 2:
        raise AnalysisError("Odd Prefetch UTF-16 string section size")
    strings = pf.take(strings_offset,strings_size)
    if strings and not strings.endswith(b"\x00\x00"):
        raise AnalysisError("Unterminated Prefetch filename strings")
    references = [s for s in pf.text(strings,"utf-16-le",report,source_id).split("\x00") if s]
    raw_times = [pf.number(84+time_offset+8*i,8) for i in range(slots)]
    times = [filetime(ticks,report,source_id,f'prefetch:time:{i}') for i,ticks in enumerate(raw_times)]
    volumes = []
    volume_data = pf.section(volume_offset,volume_bytes)
    volume_data.take(0,volume_count*volume_size)
    for index in range(volume_count):
        entry = volume_data.section(index*volume_size,volume_size)
        path_offset,length = entry.number(0,4),entry.number(4,4)
        if length and path_offset < volume_count*volume_size:
            raise AnalysisError("Prefetch volume path overlaps entries")
        path = volume_data.text(volume_data.take(path_offset,length*2),"utf-16-le",report,source_id).rstrip("\x00")
        ticks = entry.number(8,8)
        volumes.append(dict(device_path=path,created_at=filetime(ticks,report,source_id,f'prefetch:volume:{index}'),
                            creation_time_raw=str(ticks),serial=f'{entry.number(16,4):08X}'))
    return dict(source_id=source_id,record_id="prefetch:0",version=version,compressed=compressed,
        layout=header_end,executable=exe,prefetch_hash=f'{pf.number(76,4):08X}',file_size=len(data),
        run_count=pf.number(84+count_offset,4),last_run_times=times,last_run_times_raw=[str(t) for t in raw_times],
        referenced_files=references,executable_path_candidates=[p for p in references if ntpath.basename(p).casefold()==exe.casefold()],
        volumes=volumes,metrics_count=metrics_count,trace_count=trace_count,
        unparsed_sections=["file_metrics","trace_chains","volume_file_references","directory_strings","hash_string"])
