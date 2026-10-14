"""Mix browser, LNK, Prefetch and EVTX reports while preserving input source IDs."""
from .binary import read_artifact
from .browser import analyze as analyze_browsers
from .model import Report
from . import lnk, prefetch, evtx


def analyze(inputs=(), links=(), prefetches=(), browser="auto", codepage="cp1252", event_logs=()):
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
    return report
