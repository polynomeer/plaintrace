"""Command-line entry point, with separate diagnostics and machine-readable data."""
import argparse
import json
import sqlite3
import sys

from . import __version__
from .execution import analyze
from .evidence import AnalysisError
from .exports import write_report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Analyze acquired browser SQLite, LNK, Prefetch, EVTX, Recycle Bin $I, USB registry, RecentDocs and application MRU hives, Jump Lists, ShellBags, Common Dialog MRUs, UserAssist, RunMRU, TypedPaths, WordWheelQuery Windows system information and SAM accounts without EnCase.")
    parser.add_argument("--sam", action="append", default=[], metavar="HIVE", help="Acquired SAM account metadata; repeat")
    for role in ("software","system"):
        parser.add_argument("--system-info-"+role, action="append", default=[], metavar="HIVE", help="Acquired "+role.upper()+" Windows system information; repeat")
    for artifact in ("typed-paths", "word-wheel-query"):
        parser.add_argument("--"+artifact, action="append", default=[], metavar="NTUSER", help="Acquired NTUSER.DAT "+artifact+"; repeat")
    parser.add_argument("--run-mru", action="append", default=[], metavar="NTUSER", help="Acquired NTUSER.DAT Run dialog MRU; repeat")
    parser.add_argument("--userassist", action="append", default=[], metavar="NTUSER", help="Acquired NTUSER.DAT UserAssist; repeat")
    parser.add_argument("--version", action="version", version=f"plaintrace {__version__}")
    parser.add_argument("--input", action="append", default=[], metavar="DB", help="Acquired History or places.sqlite; repeat for multiple sources")
    parser.add_argument("--lnk", action="append", default=[], metavar="FILE", help="Acquired Shell Link; repeat for multiple files")
    parser.add_argument("--prefetch", action="append", default=[], metavar="FILE", help="Acquired uncompressed SCCA or MAM04 Prefetch; repeat")
    parser.add_argument("--evtx", action="append", default=[], metavar="FILE", help="Acquired Windows EVTX; requires optional evtx extra; repeat")
    parser.add_argument("--recycle-bin", action="append", default=[], metavar="FILE", help="Acquired $Recycle.Bin $I metadata file; repeat")
    parser.add_argument("--recent-docs",action="append",default=[],metavar="NTUSER",help="Acquired NTUSER.DAT Explorer RecentDocs; repeat")
    parser.add_argument("--application-mru",action="append",default=[],metavar="NTUSER",help="Acquired NTUSER.DAT Office/HWP/Adobe MRUs; repeat")
    parser.add_argument("--jump-list",action="append",default=[],metavar="FILE",help="Acquired automatic/custom destinations Jump List; repeat")
    parser.add_argument('--dialog-mru',action='append',default=[],metavar='NTUSER',help='Acquired NTUSER.DAT OpenSavePidlMRU/LastVisitedPidlMRU; repeat')
    parser.add_argument('--dialog-mru-codepage',default='cp1252',help='ANSI-compatible dialog PIDL encoding; Unicode stays UTF-16LE')
    for role in ('ntuser','usrclass'):
        parser.add_argument('--shellbags-'+role,action='append',default=[],metavar='HIVE',help='Acquired '+role.upper()+' ShellBags hive; repeat')
    parser.add_argument('--shellbags-codepage',default='cp1252',help='ANSI-compatible Shell Item name encoding; Unicode remains UTF-16LE')
    for role in ('system','software','ntuser'):
        parser.add_argument('--usb-'+role,action='append',default=[],metavar='HIVE',help='Acquired '+role.upper()+' hive for USB registry observations; repeat')
    parser.add_argument("--lnk-codepage", default="cp1252", help="ANSI-compatible LNK encoding; Unicode fields remain UTF-16LE")
    parser.add_argument("--browser", choices=("auto", "chromium", "chrome", "opera", "firefox"), default="auto", help="Auto detects schema family; Chrome/Opera labels require explicit selection")
    parser.add_argument("--format", choices=("json", "sqlite"), default="json")
    parser.add_argument("--output", metavar="PATH", help="New output file; existing files are never overwritten. JSON defaults to stdout")
    parser.add_argument("--strict", action="store_true", help="Write the report but return exit code 1 if warnings are present")
    args = parser.parse_args(argv)
    if not (args.input or args.lnk or args.prefetch or args.evtx or args.recycle_bin or args.usb_system or args.usb_software or args.usb_ntuser or args.recent_docs or args.application_mru or args.jump_list or args.shellbags_ntuser or args.shellbags_usrclass or args.dialog_mru or args.userassist or args.run_mru or args.typed_paths or args.word_wheel_query or args.system_info_software or args.system_info_system or args.sam):
        parser.error("at least one --input, --lnk, --prefetch, --evtx, --recycle-bin or --usb-{system,software,ntuser} or --recent-docs or --application-mru or --jump-list or --shellbags-{ntuser,usrclass} or --dialog-mru or --userassist or --run-mru or --typed-paths or --word-wheel-query or --system-info-{software,system} or --sam is required")
    if args.format == "sqlite" and not args.output:
        parser.error("--format sqlite requires --output")
    try:
        report = analyze(args.input,args.lnk,args.prefetch,args.browser,args.lnk_codepage,event_logs=args.evtx,recycle_bins=args.recycle_bin,usb_hives=[(role,path) for role in ("system","software","ntuser") for path in getattr(args,"usb_"+role)],recent_hives=args.recent_docs,application_hives=args.application_mru,jump_files=args.jump_list,shellbag_hives=[(role,path) for role in ("ntuser","usrclass") for path in getattr(args,"shellbags_"+role)],shellbags_codepage=args.shellbags_codepage,dialog_hives=args.dialog_mru,dialog_codepage=args.dialog_mru_codepage,userassist_hives=args.userassist,run_mru_hives=args.run_mru,explorer_hives=[(artifact,path) for artifact in ("typed_paths","word_wheel_query") for path in getattr(args,artifact)],system_info_hives=[(role,path) for role in ("software","system") for path in getattr(args,"system_info_"+role)],sam_hives=args.sam)
        if args.output:
            write_report(report, args.output, args.format)
        else:
            payload = json.dumps(report.as_dict(), ensure_ascii=False, indent=2, allow_nan=False)
            sys.stdout.write(payload + "\n")
        for diagnostic in report.diagnostics:
            print(f'warning [{diagnostic["code"]}] source {diagnostic["source_id"]}: {diagnostic["message"]}', file=sys.stderr)
        return 1 if args.strict and report.diagnostics else 0
    except BrokenPipeError:
        return 2
    except (AnalysisError, OSError, sqlite3.Error, ValueError, TypeError, UnicodeError) as error:
        print(f"plaintrace: {error}", file=sys.stderr)
        return 2
