"""MS-SHLLINK parsing without target resolution or execution."""
import codecs
import ntpath
import uuid

from .binary import Binary, filetime
from .evidence import AnalysisError

CLSID = uuid.UUID("00021401-0000-0000-c000-000000000046").bytes_le


def combine(base, suffix):
    if not base:
        return suffix or None
    if not suffix:
        return base
    suffix = suffix.lstrip("\\")
    if base.casefold() == suffix.casefold() or base.casefold().endswith("\\" + suffix.casefold()):
        return base
    return base.rstrip("\\") + "\\" + suffix.lstrip("\\")


def parse(data, source_id, report, codepage="cp1252"):
    try:
        codecs.lookup(codepage)
        if "\x00".encode(codepage) != b"\x00":
            raise ValueError("not an ANSI-compatible encoding")
    except (LookupError, ValueError) as error:
        raise AnalysisError(f"Invalid LNK codepage: {codepage}") from error
    root = Binary(data, "LNK")
    if root.number(0,4) != 0x4c or root.take(4,16) != CLSID:
        raise AnalysisError("Not a Shell Link header")
    root.take(0,76)
    flags = root.number(20,4)
    record = dict(source_id=source_id, record_id="lnk:0", link_flags=flags,
        file_attributes=root.number(24,4), target_size=root.number(52,4),
        created_at=None, accessed_at=None, written_at=None, filetimes_raw={},
        local_base_path=None, common_path_suffix=None, network_share=None, volume={},
        name=None, relative_path=None, working_directory=None, arguments=None, icon_location=None,
        target_candidates=[], tracker={}, environment_target=None, id_list_hex=None, extra_blocks=[])
    for name, offset in (("created",28),("accessed",36),("written",44)):
        ticks = root.number(offset,8)
        record["filetimes_raw"][name] = str(ticks)
        record[name+"_at"] = filetime(ticks,report,source_id,"lnk:0")
    cursor = 76
    if flags & 1:
        size = root.number(cursor,2)
        items = root.section(cursor+2,size)
        item_cursor = 0
        while True:
            length = items.number(item_cursor,2)
            if length == 0:
                if item_cursor + 2 != size:
                    raise AnalysisError("LNK ID list has bytes after its terminal item")
                break
            if length < 2:
                raise AnalysisError("Invalid LNK ItemID size")
            items.take(item_cursor,length)
            item_cursor += length
        record["id_list_hex"] = items.data.hex()
        report.warn(source_id,"opaque_id_list","PIDL retained as hex; target shell items not decoded","lnk:0")
        cursor += size+2
    if flags & 2:
        info = root.section(cursor,root.number(cursor,4))
        header = info.number(4,4)
        if header != 28 and header < 36:
            raise AnalysisError("Invalid LNK LinkInfo header size")
        info.take(0,header)
        location_flags = info.number(8,4)
        suffix = info.ztext(info.number(24,4),header,False,codepage,report,source_id)
        if header >= 36 and info.number(32,4):
            suffix = info.ztext(info.number(32,4),header,True,"utf-16-le",report,source_id)
        record["common_path_suffix"] = suffix
        if location_flags & 1:
            volume_offset = info.number(12,4)
            if volume_offset < header:
                raise AnalysisError("Invalid VolumeID offset")
            volume = info.section(volume_offset,info.number(volume_offset,4))
            volume.take(0,16)
            label_offset = volume.number(12,4)
            wide = label_offset == 20
            if wide:
                label_offset = volume.number(16,4)
            label = volume.ztext(label_offset,20 if wide else 16,wide,"utf-16-le" if wide else codepage,report,source_id)
            record["volume"] = dict(drive_type=volume.number(4,4),serial=f'{volume.number(8,4):08X}',label=label)
            base = info.ztext(info.number(16,4),header,False,codepage,report,source_id)
            if header >= 36 and info.number(28,4):
                base = info.ztext(info.number(28,4),header,True,"utf-16-le",report,source_id)
            record["local_base_path"] = base
            record["target_candidates"].append(dict(basis="link_info_local",path=combine(base,suffix)))
        if location_flags & 2:
            network_offset = info.number(20,4)
            if network_offset < header:
                raise AnalysisError("Invalid network offset")
            network = info.section(network_offset,info.number(network_offset,4))
            network.take(0,20)
            name_offset = network.number(8,4)
            wide = name_offset > 20
            if wide:
                network.take(0,28)
                name_offset = network.number(20,4)
            share = network.ztext(name_offset,28 if wide else 20,wide,"utf-16-le" if wide else codepage,report,source_id)
            record["network_share"] = share
            record["target_candidates"].append(dict(basis="link_info_network",path=combine(share,suffix)))
        cursor += len(info.data)
    for mask, name in ((4,"name"),(8,"relative_path"),(16,"working_directory"),(32,"arguments"),(64,"icon_location")):
        if flags & mask:
            count = root.number(cursor,2)
            size = count * (2 if flags & 128 else 1)
            record[name] = root.text(root.take(cursor+2,size),"utf-16-le" if flags & 128 else codepage,report,source_id)
            cursor += 2+size
    if record["relative_path"]:
        path = ntpath.join(record["working_directory"],record["relative_path"]) if record["working_directory"] else record["relative_path"]
        record["target_candidates"].append(dict(basis="relative_string",path=path))
    while True:
        size = root.number(cursor,4)
        if size < 4:
            cursor += 4
            break
        if size < 8:
            raise AnalysisError("Invalid LNK ExtraData block size")
        block = root.section(cursor,size)
        signature = block.number(4,4)
        record["extra_blocks"].append(dict(offset=cursor,size=size,signature=f'{signature:08X}'))
        if signature == 0xa0000003:
            if size != 96 or block.number(8,4) != 88 or block.number(12,4) != 0:
                raise AnalysisError("Invalid LNK tracker block")
            machine = block.section(16,16).ztext(0,0,False,codepage,report,source_id)
            tracker = dict(machine_id=machine)
            for name,offset in (("droid_volume",32),("droid_file",48),("birth_volume",64),("birth_file",80)):
                tracker[name] = str(uuid.UUID(bytes_le=block.take(offset,16)))
            record["tracker"] = tracker
        elif signature == 0xa0000001:
            if size != 788:
                raise AnalysisError("Invalid LNK environment block")
            ansi = block.section(8,260).ztext(0,0,False,codepage,report,source_id)
            unicode = block.section(268,520).ztext(0,0,True,"utf-16-le",report,source_id)
            record["environment_target"] = unicode or ansi
            record["target_candidates"].append(dict(basis="environment_string",path=unicode or ansi))
        else:
            report.warn(source_id,"opaque_extra_block",f"ExtraData {signature:08X} not interpreted","lnk:0")
        cursor += size
    if cursor != len(data):
        report.warn(source_id,"lnk_trailing_bytes","Bytes after TerminalBlock are not interpreted","lnk:0")
    record["target_candidates"] = [candidate for candidate in record["target_candidates"] if candidate["path"]]
    if not record["target_candidates"]:
        report.warn(source_id,"lnk_target_unresolved","No supported textual target; not resolved against a filesystem","lnk:0")
    return record
