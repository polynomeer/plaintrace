"""Combine acquired artifact reports while preserving source IDs and parser boundaries."""
import re
from .binary import read_artifact
from .browser import analyze as analyze_browsers
from .model import Report
from . import lnk, prefetch, evtx, recycle_bin, usb_registry, registry_hive, recent_docs, application_mru, jump_lists


def analyze(inputs=(), links=(), prefetches=(), browser="auto", codepage="cp1252", event_logs=(), recycle_bins=(), usb_hives=(), recent_hives=(), application_hives=(), jump_files=()):
    report = analyze_browsers(inputs,browser) if inputs else Report()
    for kind,paths,parser in (("lnk",links,lnk.parse),("prefetch",prefetches,prefetch.parse)):
        for path in paths:
            resolved,data,digest = read_artifact(path)
            source_id = len(report.sources)+1
            source = dict(source_id=source_id,path=str(resolved),browser=None,schema_family=kind,
                          database_sha256=None,wal_sha256=None,source_kind=kind,sha256=digest)
            report.sources.append(source)
            record = parser(data,source_id,report,codepage) if kind=="lnk" else parser(data,source_id,report)
            getattr(report,"links" if kind=="lnk" else "prefetch").append(record)
    for path in event_logs:
        resolved, data, digest = read_artifact(path, evtx.MAX_EVTX_BYTES)
        source_id = len(report.sources)+1
        report.sources.append(dict(source_id=source_id,path=str(resolved),browser=None,schema_family="evtx",
                                   database_sha256=None,wal_sha256=None,source_kind="evtx",sha256=digest))
        report.events.extend(evtx.parse(data, source_id, report))
    for path in recycle_bins:
        resolved, data, digest = read_artifact(path, recycle_bin.MAX_RECYCLE_BYTES)
        source_id = len(report.sources)+1
        report.sources.append(dict(source_id=source_id,path=str(resolved),browser=None,schema_family="recycle_bin",
                                   database_sha256=None,wal_sha256=None,source_kind="recycle_bin",sha256=digest))
        report.recycle_bin.append(recycle_bin.parse(data, source_id, report))
    for role,path in usb_hives:
        resolved,data,digest = read_artifact(path,registry_hive.MAX_HIVE_BYTES)
        source_id=len(report.sources)+1
        report.sources.append(dict(source_id=source_id,path=str(resolved),browser=None,schema_family='registry_'+role,
                                   database_sha256=None,wal_sha256=None,source_kind='usb_registry',sha256=digest))
        report.usb_registry.extend(usb_registry.analyze_hive(data,role,source_id,report))
    for path in recent_hives:
        resolved,data,digest=read_artifact(path,registry_hive.MAX_HIVE_BYTES)
        source_id=len(report.sources)+1
        report.sources.append(dict(source_id=source_id,path=str(resolved),browser=None,schema_family='registry_ntuser',
                                   database_sha256=None,wal_sha256=None,source_kind='recent_docs',sha256=digest))
        keys,documents=recent_docs.analyze_hive(data,source_id,report)
        report.recent_doc_keys.extend(keys)
        report.recent_docs.extend(documents)
    for path in application_hives:
        resolved,data,digest=read_artifact(path,registry_hive.MAX_HIVE_BYTES)
        source_id=len(report.sources)+1
        report.sources.append(dict(source_id=source_id,path=str(resolved),browser=None,schema_family='registry_ntuser',
                                   database_sha256=None,wal_sha256=None,source_kind='application_mru',sha256=digest))
        keys,entries=application_mru.analyze_hive(data,source_id,report)
        report.application_mru_keys.extend(keys)
        report.application_mru.extend(entries)
    for path in jump_files:
        resolved,data,digest=read_artifact(path,jump_lists.MAX_JUMP_BYTES)
        source_id=len(report.sources)+1
        summary,entries=jump_lists.parse(data,source_id,report,codepage)
        match=re.fullmatch(r'([0-9a-fA-F]{16})\.(?:automatic|custom)Destinations-ms',resolved.name,re.I|re.ASCII)
        summary['app_id_hint']=match[1] if match else None
        report.sources.append(dict(source_id=source_id,path=str(resolved),browser=None,schema_family='jump_'+summary['container_kind'],
                                   database_sha256=None,wal_sha256=None,source_kind='jump_list',sha256=digest))
        report.jump_lists.append(summary)
        report.jump_list_entries.extend(entries)
    return report
