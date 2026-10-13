"""Command-line entry point, with separate diagnostics and machine-readable data."""
import argparse
import json
import sqlite3
import sys

from . import __version__
from .browser import analyze
from .evidence import AnalysisError
from .exports import write_report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Analyze acquired Chromium/Firefox browser SQLite files without EnCase.")
    parser.add_argument("--version", action="version", version=f"plaintrace {__version__}")
    parser.add_argument("--input", action="append", required=True, metavar="DB", help="Acquired History or places.sqlite; repeat for multiple sources")
    parser.add_argument("--browser", choices=("auto", "chromium", "chrome", "opera", "firefox"), default="auto", help="Auto detects schema family; Chrome/Opera labels require explicit selection")
    parser.add_argument("--format", choices=("json", "sqlite"), default="json")
    parser.add_argument("--output", metavar="PATH", help="New output file; existing files are never overwritten. JSON defaults to stdout")
    parser.add_argument("--strict", action="store_true", help="Write the report but return exit code 1 if warnings are present")
    args = parser.parse_args(argv)
    if args.format == "sqlite" and not args.output:
        parser.error("--format sqlite requires --output")
    try:
        report = analyze(args.input, args.browser)
        if args.output:
            write_report(report, args.output, args.format)
        else:
            json.dump(report.as_dict(), sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
        for diagnostic in report.diagnostics:
            print(f'warning [{diagnostic["code"]}] source {diagnostic["source_id"]}: {diagnostic["message"]}', file=sys.stderr)
        return 1 if args.strict and report.diagnostics else 0
    except BrokenPipeError:
        return 2
    except (AnalysisError, OSError, sqlite3.Error, ValueError, TypeError, UnicodeError) as error:
        print(f"plaintrace: {error}", file=sys.stderr)
        return 2
