"""Analyze isolated, verified copies so SQLite never opens the input files."""
from contextlib import contextmanager
import hashlib
from pathlib import Path
import shutil
import sqlite3
import tempfile


class AnalysisError(Exception):
    """A source cannot be safely interpreted under the supported contract."""


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fingerprint(path):
    wal = Path(str(path) + "-wal")
    return {"database_sha256": sha256(path),
            "wal_sha256": sha256(wal) if wal.exists() else None}


@contextmanager
def snapshot(path):
    """Copy DB and WAL, verify stable bytes, then open only the copy read-only.

    This is not atomic acquisition from a live browser. Source SHM is neither
    read nor written; SQLite can reconstruct SHM in the temporary directory.
    """
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise AnalysisError(f"Input is not a file: {path}")
    journal = Path(str(path) + "-journal")
    if journal.exists() and journal.stat().st_size:
        raise AnalysisError(f"Rollback journal present: {path}; acquire a clean snapshot")
    before = fingerprint(path)
    with tempfile.TemporaryDirectory(prefix="plaintrace-") as directory:
        local = Path(directory) / "browser.sqlite"
        shutil.copyfile(path, local)
        if before["wal_sha256"] is not None:
            shutil.copyfile(Path(str(path) + "-wal"), Path(str(local) + "-wal"))
        if (fingerprint(local) != before or fingerprint(path) != before or
                (journal.exists() and journal.stat().st_size)):
            raise AnalysisError(f"Input changed during copying: {path}; acquire a stable snapshot")
        connection = sqlite3.connect(local.as_uri() + "?mode=ro", uri=True)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA query_only=ON")
            connection.execute("PRAGMA trusted_schema=OFF")
            result = connection.execute("PRAGMA quick_check").fetchall()
            if len(result) != 1 or result[0][0] != "ok":
                raise AnalysisError(f"SQLite integrity check failed: {path}")
            yield connection, before
        finally:
            connection.close()
