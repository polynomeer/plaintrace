"""Synthetic SQLite fixtures with independently specified expected artifacts."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from plaintrace.browser import analyze
from plaintrace.cli import main
from plaintrace.evidence import AnalysisError, sha256
from plaintrace.exports import write_report
from plaintrace.model import Report, firefox_end_time, timestamp

ROOT = Path(__file__).resolve().parents[1]
# Independently calculated: 2020-01-01 UTC, with a known microsecond fraction.
CHROME_TIME = 13222310400123456
UNIX_TIME = 1577836800123456
EXPECTED_TIME = "2020-01-01T00:00:00.123456Z"


def chromium(db):
    db.executescript('''
        CREATE TABLE urls(id INTEGER PRIMARY KEY,url TEXT,title TEXT,last_visit_time INTEGER);
        CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER,visit_time INTEGER);
        CREATE TABLE downloads(id INTEGER PRIMARY KEY,current_path TEXT,target_path TEXT,start_time INTEGER,end_time INTEGER,received_bytes INTEGER,total_bytes INTEGER,referrer TEXT,state INTEGER);
        CREATE TABLE downloads_url_chains(id INTEGER,chain_index INTEGER,url TEXT);
        CREATE TABLE keyword_search_terms(keyword_id INTEGER,url_id INTEGER,term TEXT);
    ''')
    db.execute("INSERT INTO urls VALUES (1,?,?,?)", ("https://example.org/?q=O%27Brien+%ED%95%9C%EA%B8%80%26x&query=two&search_query=%F0%9F%98%80&q=again#q=not-search", "'Title', 한글\nnext", CHROME_TIME+100))
    db.executemany("INSERT INTO visits VALUES (?,?,?)", [(10,1,CHROME_TIME),(11,1,CHROME_TIME+1)])
    db.execute("INSERT INTO downloads VALUES (1,?,?,?,?,?,?,?,?)", ("partial%20name", "C:/O'Brien,한글\nfile.txt", CHROME_TIME,CHROME_TIME+2000000,120,120,"https://referrer.example/",1))
    db.executemany("INSERT INTO downloads_url_chains VALUES (?,?,?)", [(1,1,"https://final.example/file"),(1,0,"https://redirect.example/")])
    db.execute("INSERT INTO keyword_search_terms VALUES (2,1,?)", ("stored 'term' 한글",))
    db.commit()


def firefox(db):
    db.executescript('''
        CREATE TABLE moz_places(id INTEGER PRIMARY KEY,url TEXT,title TEXT,last_visit_date INTEGER);
        CREATE TABLE moz_historyvisits(id INTEGER PRIMARY KEY,place_id INTEGER,visit_date INTEGER,visit_type INTEGER);
        CREATE TABLE moz_anno_attributes(id INTEGER PRIMARY KEY,name TEXT);
        CREATE TABLE moz_annos(id INTEGER PRIMARY KEY,place_id INTEGER,anno_attribute_id INTEGER,content TEXT,dateAdded INTEGER,lastModified INTEGER);
    ''')
    db.executemany("INSERT INTO moz_places VALUES (?,?,?,?)", [(1,"https://example.org/?search_query=%ED%95%9C%EA%B8%80%26more","한국어",UNIX_TIME),(2,"https://example.org/file","download",UNIX_TIME)])
    db.executemany("INSERT INTO moz_historyvisits VALUES (?,?,?,?)", [(8,1,UNIX_TIME,1),(9,2,UNIX_TIME,7)])
    # Deliberately arbitrary IDs and reversed row order: no fixed 4/5 or alternating-row assumption.
    db.executemany("INSERT INTO moz_anno_attributes VALUES (?,?)", [(73,"downloads/metaData"),(91,"downloads/destinationFileURI")])
    db.executemany("INSERT INTO moz_annos VALUES (?,?,?,?,?,?)", [(20,2,73,json.dumps({"endTime":1577836802123,"fileSize":55,"state":1}),UNIX_TIME+20,UNIX_TIME+21),(30,2,91,"file:///C:/O%27Brien%20%ED%95%9C%EA%B8%80.txt",UNIX_TIME+10,UNIX_TIME+11)])
    db.commit()


class BrowserTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="plaintrace-tests-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def database(self, name, builder):
        path = self.directory/name
        db = sqlite3.connect(path)
        try:
            builder(db)
        finally:
            db.close()
        return path

    def cli(self, args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(args)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_chromium_visits_keywords_and_downloads(self):
        path = self.database("arbitrary.db",chromium)
        report = analyze([path],"chrome")
        self.assertFalse(report.diagnostics)
        self.assertEqual(len(report.visits),2)
        self.assertEqual(report.visits[0]["visited_at"],EXPECTED_TIME)
        self.assertEqual(report.visits[1]["visited_at"],"2020-01-01T00:00:00.123457Z")
        self.assertEqual(report.visits[0]["record_id"],"visits:10")
        self.assertEqual([k["keyword"] for k in report.keywords[:4]], ["O'Brien 한글&x","two","😀","again"])
        self.assertEqual(len(report.keywords),9)
        stored = report.keywords[-1]
        self.assertEqual(stored["keyword"],"stored 'term' 한글")
        self.assertEqual(stored["time_basis"],"url_summary")
        download = report.downloads[0]
        self.assertEqual(download["url_chain"],["https://redirect.example/","https://final.example/file"])
        self.assertEqual(download["url"],"https://final.example/file")
        self.assertEqual(download["referrer"],"https://referrer.example/")
        self.assertEqual(download["path"],"C:/O'Brien,한글\nfile.txt")
        self.assertEqual(download["ended_at"],"2020-01-01T00:00:02.123456Z")
        self.assertEqual(report.sources[0]["database_sha256"],sha256(path))

    def test_firefox_correlates_annotation_names_and_place(self):
        path = self.database("places.sqlite",firefox)
        report = analyze([path])
        self.assertFalse(report.diagnostics)
        self.assertEqual(report.visits[0]["visited_at"],EXPECTED_TIME)
        self.assertEqual(report.keywords[0]["keyword"],"한글&more")
        row = report.downloads[0]
        self.assertEqual(row["url"],"https://example.org/file")
        self.assertEqual(row["path"],"C:/O'Brien 한글.txt")
        self.assertEqual(row["total_bytes"],55)
        self.assertEqual(row["started_at"],EXPECTED_TIME)
        self.assertEqual(row["start_time_basis"],"latest_download_visit")
        self.assertEqual(row["ended_at"],"2020-01-01T00:00:02.123000Z")
        self.assertEqual(row["record_kind"],"annotation_summary")

    def test_url_summary_is_not_a_visit(self):
        def build(db):
            chromium(db); db.execute("DROP TABLE visits"); db.commit()
        path = self.database("summary.sqlite",build)
        report = analyze([path])
        self.assertEqual(len(report.visits),1)
        self.assertEqual(report.visits[0]["record_kind"],"url_summary")
        self.assertIn("url_summary_only",{d["code"] for d in report.diagnostics})

    def test_missing_downloads_are_diagnosed(self):
        def build(db):
            chromium(db); db.execute("DROP TABLE downloads"); db.commit()
        path = self.database("nodownloads.sqlite",build)
        report = analyze([path])
        self.assertFalse(report.downloads)
        self.assertIn("downloads_unavailable",{d["code"] for d in report.diagnostics})

    def test_firefox_malformed_metadata_and_duplicate_annotations(self):
        def build(db):
            firefox(db)
            db.execute("INSERT INTO moz_annos VALUES (40,2,73,?,?,?)", ("{invalid",UNIX_TIME+50,UNIX_TIME+60))
            db.commit()
        report = analyze([self.database("broken-metadata.sqlite",build)])
        self.assertEqual(report.downloads[0]["metadata_raw"],"{invalid")
        self.assertIsNone(report.downloads[0]["ended_at"])
        self.assertEqual({d["code"] for d in report.diagnostics},{"duplicate_annotation","invalid_download_metadata"})

    def test_iso_firefox_endtime_and_invalid_numeric_metadata(self):
        def build(db):
            firefox(db)
            db.execute("UPDATE moz_annos SET content=? WHERE anno_attribute_id=73", (json.dumps({"endTime":"2020-01-01T09:00:00.123456+09:00","fileSize":{"wrong":1},"state":False}),))
            db.commit()
        report = analyze([self.database("iso.sqlite",build)])
        self.assertEqual(report.downloads[0]["ended_at"],EXPECTED_TIME)
        self.assertIsNone(report.downloads[0]["total_bytes"])
        self.assertIsNone(report.downloads[0]["state"])
        self.assertEqual(len(report.diagnostics),2)

    def test_invalid_timestamp_and_query_preserve_records(self):
        def build(db):
            chromium(db)
            db.execute("UPDATE visits SET visit_time=? WHERE id=10",(2**63-1,))
            db.execute("UPDATE urls SET url='https://example.org/?q=%FF'")
            db.commit()
        report = analyze([self.database("invalid.sqlite",build)])
        self.assertEqual(len(report.visits),2)
        self.assertIsNone(report.visits[0]["visited_at"])
        self.assertEqual(report.visits[0]["timestamp_raw"],str(2**63-1))
        self.assertEqual(len(report.keywords),1)  # Native stored term remains.
        self.assertEqual({d["code"] for d in report.diagnostics},{"invalid_timestamp","invalid_query"})

    def test_unknown_empty_and_corrupt_databases_fail_without_output(self):
        unknown = self.database("unknown.sqlite",lambda db:db.execute("CREATE TABLE unrelated(x)"))
        corrupt = self.directory/"corrupt.sqlite"; corrupt.write_bytes(b"not a SQLite file")
        for path in (unknown,corrupt,self.directory/"missing"):
            out = self.directory/"report.json"
            code,stdout,stderr = self.cli(["--input",str(path),"--output",str(out)])
            self.assertEqual(code,2)
            self.assertFalse(out.exists())
            self.assertFalse(stdout)
            self.assertIn("plaintrace:",stderr)

    def test_multiple_profiles_and_browser_label_conflict(self):
        chrome = self.database("History",chromium); ff = self.database("places.sqlite",firefox)
        report = analyze([chrome,ff])
        self.assertEqual([s["browser"] for s in report.sources],["chromium","firefox"])
        self.assertEqual({r["source_id"] for r in report.visits},{1,2})
        with self.assertRaises(AnalysisError): analyze([ff],"opera")

    def test_json_and_sqlite_roundtrip_and_no_overwrite(self):
        path = self.database("History",chromium); report = analyze([path])
        before = path.read_bytes()
        json_path,sql_path = self.directory/"report.json",self.directory/"report.sqlite"
        write_report(report,json_path);write_report(report,sql_path,"sqlite")
        self.assertEqual(json.loads(json_path.read_text())["visits"],report.visits)
        db = sqlite3.connect(sql_path)
        try:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0],11)
            self.assertEqual(db.execute("SELECT keyword FROM keywords WHERE derivation='stored_search_term'").fetchone()[0],"stored 'term' 한글")
            self.assertEqual(json.loads(db.execute("SELECT url_chain FROM downloads").fetchone()[0]),report.downloads[0]["url_chain"])
            self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(),[])
        finally: db.close()
        with self.assertRaises(AnalysisError): write_report(report,json_path)
        with self.assertRaises(AnalysisError): write_report(report,path)
        with self.assertRaises(AnalysisError): write_report(report,Path(str(path)+"-wal"))
        self.assertEqual(path.read_bytes(),before)
        self.assertFalse(Path(str(path)+"-shm").exists())

    def test_wal_committed_records_and_input_bytes_unchanged(self):
        path = self.directory/"History"
        db = sqlite3.connect(path)
        self.addCleanup(db.close)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA wal_autocheckpoint=0")
        chromium(db)
        inputs = [path,Path(str(path)+"-wal"),Path(str(path)+"-shm")]
        before = {str(p):p.read_bytes() for p in inputs}
        report = analyze([path])
        self.assertEqual(len(report.visits),2)
        self.assertIsNotNone(report.sources[0]["wal_sha256"])
        self.assertEqual({str(p):p.read_bytes() for p in inputs},before)

    def test_changed_snapshot_and_rollback_journal_rejected(self):
        path = self.database("History",chromium)
        with patch("plaintrace.evidence.shutil.copyfile",side_effect=lambda src,dst:Path(dst).write_bytes(b"changed")):
            with self.assertRaisesRegex(AnalysisError,"changed during copying"): analyze([path])
        Path(str(path)+"-journal").write_bytes(b"active rollback journal")
        with self.assertRaisesRegex(AnalysisError,"Rollback journal"): analyze([path])

    def test_cli_stdout_strict_and_sqlite_output(self):
        def build(db):
            chromium(db); db.execute("DROP TABLE downloads");db.commit()
        path = self.database("History",build)
        code,stdout,stderr = self.cli(["--input",str(path),"--strict"])
        self.assertEqual(code,1)
        self.assertEqual(json.loads(stdout)["counts"]["visits"],2)
        self.assertIn("downloads_unavailable",stderr)
        output = self.directory/"report.sqlite"
        code,stdout,stderr = self.cli(["--input",str(path),"--format","sqlite","--output",str(output)])
        self.assertEqual(code,0);self.assertFalse(stdout);self.assertTrue(output.exists())
        result = subprocess.run([sys.executable,"-m","plaintrace","--input",str(path)],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0)
        self.assertEqual(json.loads(result.stdout)["counts"]["visits"],2)

    def test_minimal_chromium_schema_without_optional_fields(self):
        def build(db):
            db.executescript("CREATE TABLE urls(id INTEGER,url TEXT,last_visit_time INTEGER); CREATE TABLE downloads(id INTEGER,current_path TEXT,start_time INTEGER,url TEXT);")
            db.execute("INSERT INTO urls VALUES (1,'https://example.org/',?)",(CHROME_TIME,))
            db.execute("INSERT INTO downloads VALUES (2,'literal%20name',?,'https://example.org/file')",(CHROME_TIME,));db.commit()
        report = analyze([self.database("minimal.sqlite",build)],"opera")
        self.assertIsNone(report.visits[0]["title"])
        self.assertEqual(report.downloads[0]["path"],"literal%20name")
        self.assertEqual(report.downloads[0]["url"],"https://example.org/file")
        self.assertIsNone(report.downloads[0]["ended_at"])
        self.assertEqual(report.sources[0]["browser"],"opera")
        self.assertEqual({d["code"] for d in report.diagnostics},{"url_summary_only","download_chain_unavailable"})

    def test_firefox_summary_missing_downloads_and_incomplete_annotation(self):
        def build(db):
            firefox(db);db.execute("DROP TABLE moz_historyvisits");db.execute("DELETE FROM moz_annos WHERE anno_attribute_id=73");db.commit()
        path = self.database("summary-firefox.sqlite",build)
        report = analyze([path])
        self.assertTrue(all(v["record_kind"] == "url_summary" for v in report.visits))
        self.assertEqual(report.downloads[0]["start_time_basis"],"annotation_date_added")
        self.assertIsNone(report.downloads[0]["ended_at"])
        self.assertIn("incomplete_download",{d["code"] for d in report.diagnostics})
        db = sqlite3.connect(path)
        try: db.execute("DROP TABLE moz_annos");db.commit()
        finally: db.close()
        report = analyze([path]);self.assertFalse(report.downloads)
        self.assertIn("downloads_unavailable",{d["code"] for d in report.diagnostics})

    def test_orphan_visits_and_annotation_urls_are_not_silently_dropped(self):
        def build(db):
            firefox(db);db.execute("DELETE FROM moz_places");db.commit()
        report = analyze([self.database("orphans.sqlite",build)])
        self.assertEqual(len(report.visits),2)
        self.assertEqual(len(report.downloads),1)
        self.assertIsNone(report.visits[0]["url"])
        self.assertIn("orphan_download",{d["code"] for d in report.diagnostics})
        self.assertEqual(report.visits[1]["transition"],7)

    def test_empty_supported_database_is_successful(self):
        def build(db):
            chromium(db)
            for table in ("urls","visits","downloads","downloads_url_chains","keyword_search_terms"):
                db.execute(f"DELETE FROM {table}")
            db.commit()
        report = analyze([self.database("empty.sqlite",build)])
        self.assertFalse(report.visits);self.assertFalse(report.keywords);self.assertFalse(report.downloads)
        self.assertFalse(report.diagnostics)

    def test_malformed_required_and_ambiguous_schemas_are_rejected(self):
        def malformed(db):
            chromium(db);db.execute("DROP TABLE visits");db.execute("CREATE TABLE visits(id INTEGER,url INTEGER)");db.commit()
        def ambiguous(db):
            chromium(db);db.execute("CREATE TABLE moz_places(id INTEGER,url TEXT)");db.commit()
        for name,builder in (("malformed",malformed),("ambiguous",ambiguous)):
            with self.assertRaises(AnalysisError): analyze([self.database(name,builder)])

    def test_fragment_and_literal_bad_escape_query(self):
        def build(db):
            chromium(db);db.execute("UPDATE urls SET url='https://example.org/path#?q=not-a-query'");db.commit()
        path = self.database("fragment",build)
        report = analyze([path]);self.assertEqual(len(report.keywords),1)
        db = sqlite3.connect(path)
        try: db.execute("UPDATE urls SET url='https://example.org/?q=%ZZ&query=&q=one%26two'");db.commit()
        finally: db.close()
        report = analyze([path])
        self.assertEqual([k["keyword"] for k in report.keywords[:2]],["%ZZ","one&two"])
        self.assertIn("malformed_url_escape",{d["code"] for d in report.diagnostics})

    def test_sqlite_cli_requires_destination(self):
        result = subprocess.run([sys.executable,"-m","plaintrace","--input","unused","--format","sqlite"],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,2)
        self.assertIn("requires --output",result.stderr)
        self.assertFalse(result.stdout)

    def test_output_race_preserves_other_writer(self):
        report = analyze([self.database("History",chromium)])
        output = self.directory/"race.json"
        def occupied(src,dst):
            Path(dst).write_text("other writer")
            raise FileExistsError("race")
        with patch("plaintrace.exports.os.link",side_effect=occupied):
            with self.assertRaises(FileExistsError):write_report(report,output)
        self.assertEqual(output.read_text(),"other writer")
        self.assertFalse(list(self.directory.glob(".plaintrace-*")))

    def test_all_or_nothing_multiple_inputs(self):
        path = self.database("History",chromium)
        output = self.directory/"report.json"
        code,stdout,stderr = self.cli(["--input",str(path),"--input",str(self.directory/"missing"),"--output",str(output)])
        self.assertEqual(code,2);self.assertFalse(output.exists())
        self.assertFalse(list(self.directory.glob(".plaintrace-*")))

    def test_output_publication_failure_leaves_no_report_or_temp(self):
        report = analyze([self.database("History",chromium)])
        output = self.directory/"out.json"
        with patch("plaintrace.exports.os.link",side_effect=OSError("no hard links")):
            with self.assertRaises(OSError): write_report(report,output)
        self.assertFalse(output.exists())
        self.assertFalse(list(self.directory.glob(".plaintrace-*")))

    def test_invalid_unrelated_query_does_not_drop_valid_terms(self):
        def build(db):
            chromium(db)
            db.execute("UPDATE urls SET url='https://example.org/?other=%FF&q=valid&query=%FF&search_query=also+valid'");db.commit()
        report = analyze([self.database("mixed-query",build)])
        self.assertEqual([k["keyword"] for k in report.keywords[:2]],["valid","also valid"])
        self.assertEqual(sum(d["code"] == "invalid_query" for d in report.diagnostics),2)

    def test_dangling_output_symlink_is_not_followed(self):
        report = analyze([self.database("History",chromium)])
        target,link = self.directory/"unexpected.json",self.directory/"link.json"
        try: link.symlink_to(target)
        except OSError as error: self.skipTest(str(error))
        with self.assertRaises(AnalysisError):write_report(report,link)
        self.assertFalse(target.exists());self.assertTrue(link.is_symlink())

    def test_existing_output_sqlite_sidecars_are_preserved(self):
        report = analyze([self.database("History",chromium)])
        for suffix in ("-wal","-shm","-journal"):
            output=self.directory/("out"+suffix+".sqlite")
            sidecar=Path(str(output)+suffix);sidecar.write_bytes(b"old evidence")
            with self.assertRaises(AnalysisError):write_report(report,output,"sqlite")
            self.assertEqual(sidecar.read_bytes(),b"old evidence")
            self.assertFalse(output.exists())
        self.assertFalse(list(self.directory.glob(".plaintrace-*")))

    def test_stdout_serialization_failure_has_no_partial_json(self):
        report=Report();report.visits.append({"unsupported":b"binary"})
        with patch("plaintrace.cli.analyze",return_value=report):
            code,out,err=self.cli(["--input","unused"])
        self.assertEqual(code,2);self.assertFalse(out);self.assertIn("plaintrace:",err)
        report.visits=[{"unsupported":float("inf")}]
        with patch("plaintrace.cli.analyze",return_value=report):
            code,out,err=self.cli(["--input","unused"])
        self.assertEqual(code,2);self.assertFalse(out)

    def test_browser_views_are_not_accepted_as_native_tables(self):
        def build(db):
            db.executescript("CREATE TABLE fake(id,url,last_visit_time); CREATE VIEW urls AS SELECT * FROM fake;")
        with self.assertRaisesRegex(AnalysisError,"expected a table"):
            analyze([self.database("view",build)])

    def test_orphan_stored_keyword_is_diagnosed(self):
        def build(db):
            chromium(db);db.execute("UPDATE keyword_search_terms SET url_id=999");db.commit()
        report=analyze([self.database("orphan-term",build)])
        self.assertIn("orphan_keyword",{d["code"] for d in report.diagnostics})
        self.assertIsNone(report.keywords[-1]["url"])

    def test_download_lineage_and_inconsistent_times(self):
        def build(db):
            firefox(db)
            db.execute("UPDATE moz_annos SET content=? WHERE anno_attribute_id=73",(json.dumps({"endTime":1577836799000}),));db.commit()
        report=analyze([self.database("lineage",build)])
        row=report.downloads[0]
        self.assertEqual(row["annotation_ids"],{"downloads/metaData":20,"downloads/destinationFileURI":30})
        self.assertEqual(row["start_visit_id"],9)
        self.assertIn("inconsistent_download_times",{d["code"] for d in report.diagnostics})
        output=self.directory/"lineage.sqlite";write_report(report,output,"sqlite")
        db=sqlite3.connect(output)
        try:
            ids,start_id=db.execute("SELECT annotation_ids,start_visit_id FROM downloads").fetchone()
            self.assertEqual(json.loads(ids),row["annotation_ids"]);self.assertEqual(start_id,9)
        finally:db.close()

    def test_unsupported_export_format_fails_explicitly(self):
        report=analyze([self.database("History",chromium)])
        output=self.directory/"unknown"
        with self.assertRaisesRegex(AnalysisError,"Unsupported output format"):
            write_report(report,output,"csv")
        self.assertFalse(output.exists())


class TimeTests(unittest.TestCase):
    def test_epoch_precision_and_unknown_values(self):
        report = Report()
        self.assertEqual(timestamp(CHROME_TIME,"chromium_us",report,1,"a"),EXPECTED_TIME)
        self.assertEqual(timestamp(UNIX_TIME,"unix_us",report,1,"a"),EXPECTED_TIME)
        self.assertEqual(timestamp(1577836800123,"unix_ms",report,1,"a"),"2020-01-01T00:00:00.123000Z")
        for value in (None,0): self.assertIsNone(timestamp(value,"unix_us",report,1,"a"))
        self.assertFalse(report.diagnostics)
        for value in (-1,1.5,True,"not a number",10**100): self.assertIsNone(timestamp(value,"unix_us",report,1,"a"))
        self.assertEqual(len(report.diagnostics),5)

    def test_iso_timezone_overflow_is_diagnostic_not_exception(self):
        report=Report()
        result,unit=firefox_end_time("0001-01-01T00:00:00+01:00",report,1,"date")
        self.assertIsNone(result);self.assertEqual(unit,"iso8601")
        self.assertEqual(report.diagnostics[0]["code"],"invalid_timestamp")


if __name__ == "__main__":
    unittest.main()
