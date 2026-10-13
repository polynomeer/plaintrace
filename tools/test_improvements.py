#!/usr/bin/env python3
"""Portable regression checks of source-derived SQL/output contracts, not EnScript execution."""
import ast
import csv
import io
import json
import re
import sqlite3
import subprocess
import unittest
from pathlib import Path
from inspect_sources import ROOT, decode_source
from reconstruct_history import mask

BASELINE = 'archive/pre-improvements-2026-10-13'

def source(name):
    return decode_source((ROOT/name).read_bytes())

def expression(text, fields=None, variables=None):
    """Evaluate only the string concatenation subset used by selected writers."""
    fields, variables = fields or {}, variables or {}
    def visit(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str): return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add): return visit(node.left)+visit(node.right)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'n': return fields[node.attr]
        if isinstance(node, ast.Name): return variables[node.id]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and len(node.args)==1:
            value = visit(node.args[0])
            if node.func.id == 'KeywordText': return value.replace("'", "''")
            if node.func.id == 'SqlValue': return "'"+value.replace("'", "''")+"'"
            if node.func.id == 'CsvField': return '"'+value.replace('"', '""')+'"'
        raise ValueError(ast.dump(node))
    return visit(ast.parse(text.strip(), mode='eval').body)

class Improvements(unittest.TestCase):
    def test_encoding_and_structure(self):
        changed = subprocess.check_output(['git','diff',BASELINE,'--name-only'],cwd=ROOT).decode().splitlines()
        for name in changed:
            if not name.endswith('.EnScript'): continue
            original = subprocess.check_output(['git','show',f'{BASELINE}:{name}'],cwd=ROOT)
            current = (ROOT/name).read_bytes()
            for bom in (b'\xff\xfe', b'\xef\xbb\xbf'):
                self.assertEqual(original.startswith(bom),current.startswith(bom),name)
            text=decode_source(current)
            self.assertNotIn('\n',text.replace('\r\n',''),name)
            clean=mask(text); depth=0
            for c in clean:
                depth += (c=='{')-(c=='}')
                self.assertGreaterEqual(depth,0,name)
            self.assertEqual(depth,0,name)

    def test_timeline_schema_and_browser_insert(self):
        text=source('Win_TimeLine.EnScript');run=text[text.index('virtual void Run(){'):]
        statements=re.findall(r'ExecuteNonQuery\("(CREATE TABLE[^"\r\n]+)"\)',run)
        db=sqlite3.connect(':memory:');self.addCleanup(db.close)
        for sql in statements: db.execute(sql)
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(tables,{'PC_PowerOnOff','PC_LogOnOff','App_EXEFile','App_Documents','USB_EventLog','PC_UserAccount','Web_Download','Web_Keyword','Web_Visit','Web_Host','File_Deleted'})
        templates=re.findall(r'String union_visit_q = ([^\r\n]+);',text)
        self.assertTrue(templates)
        for template in templates:
            sql=expression(template,variables={'url':'https://example.org/한글','title':'Fixture','date':'2026/10/13 00:00:00','url_str':'https://example.org/한글','time':'2026/10/13 00:00:00'})
            db.execute(sql)
        self.assertEqual(db.execute('SELECT Browser,url,title,time FROM Web_Visit').fetchall(), [('IE','https://example.org/한글',' ','2026/10/13 00:00:00'),('IE','https://example.org/한글','Fixture','2026/10/13 00:00:00')])
        self.assertIn('previousOutput.Open(exportPath, FileClass::READ)',run)
        self.assertIn('if(!schemaReady)',run)

    def test_keyword_independent_queries(self):
        for name in ('Win_TimeLine.EnScript','Win_WebVisitKeyword.EnScript'):
            text=source(name)
            self.assertNotIn('keyword_extract(dataReader, full_path',text)
            self.assertIn('keyword_extract(keywordReader, full_path',text)
            self.assertIn('keywordCommand.ExecuteQuery("select * from urls;", keywordReader)',text)
            self.assertIn('keywordCommand.ExecuteQuery("select * from moz_places;", keywordReader)',text)
            # Independent cursors both retain all rows after the first cursor is exhausted.
            db=sqlite3.connect(':memory:');self.addCleanup(db.close);db.executescript('CREATE TABLE urls(url); INSERT INTO urls VALUES (1),(2);')
            first=db.execute('select * from urls;');list(first)
            self.assertEqual(list(db.execute('select * from urls;')),[(1,),(2,)])

    def test_row_copy_order(self):
        text=source('Win_PowerLogOnOff.EnScript')
        for cls,expected in [('LogonListClass',['eventID','logonID','user','event','eventTime','NetworkAddress','logonType','Computer','Domain','SID','GUID']),('PowerListClass',['eventID','Computer','event','eventTime','SID','GUID'])]:
            copies=re.findall(r'new\s+'+cls+r'\([^;\r\n]*?,\s*(n\.[^;\r\n]+)\);',text)
            self.assertTrue(copies)
            for args in copies: self.assertEqual(re.findall(r'n\.(\w+)',args),expected)
        self.assertIn('search.Find(n.user) == -1',text)

    def test_usb_csv_roundtrip(self):
        text=source('Win_USBInfo.EnScript')
        self.assertIn('value.Replace("\\\"", "\\\"\\\"", 0, -1, 0)',text)
        header=re.search(r'lf.Write\(("Vendor,Product[^\r\n]+)\);',text).group(1)
        template=re.search(r'lf.Write\((CsvField\(n.vendor\)[^\r\n]+)\);',text).group(1)
        names=re.findall(r'CsvField\(n\.(\w+)\)',template)
        fields={name: name+', "한글"\nsecond line' for name in names}
        rows=list(csv.reader(io.StringIO(expression(header)+expression(template,fields))))
        self.assertEqual(len(rows[0]),12)
        self.assertEqual(rows[1],[fields[n] for n in names])
        self.assertEqual(rows[0],['Vendor','Product','State','GeneratedTime','WrittenTime','FirmwareRevision','SerialNumber','LifeTimeGUID','SourceGUID','Source','Computer','SID'])

    def test_recent_sqlite_special_characters(self):
        text=source('Win_LinkFile.EnScript').split('class RecentHandlerClass',1)[1]
        self.assertIn('value.Replace("\'", "\'\'", 0, -1, 0)',text)
        ddl=re.search(r'ExecuteNonQuery\("(CREATE TABLE IF NOT EXISTS App_RecentFile[^"\r\n]+)"\)',text).group(1)
        insert=re.search(r'ExecuteNonQuery\(("INSERT INTO App_RecentFile[^\r\n]+)\)\) \{',text).group(1)
        names=re.findall(r'SqlValue\(n\.(\w+)\)',insert)
        fields={name:"O'Brien, 한글\n\"quoted\""+name for name in names}
        db=sqlite3.connect(':memory:');self.addCleanup(db.close);db.execute(ddl);db.execute(ddl)
        db.execute(expression(insert,fields));db.commit()
        self.assertEqual(db.execute('SELECT * FROM App_RecentFile').fetchone()[1:],tuple(fields[n] for n in names))
        self.assertIn('cmd.ExecuteNonQuery("ROLLBACK;")',text)

    def test_rerun_copy_lists_reset(self):
        text=source('Win_PowerLogOnOff.EnScript')
        for suffix in ('','1'):
            start=text.index('Logon_dialog.List'+suffix+'.Close();')
            end=text.index('foreach (',start)
            self.assertIn('Logon_dialog.CopyList'+suffix+'.Close();',text[start:end])

    def test_keyword_parameters_and_escaping(self):
        from urllib.parse import urlsplit
        expected={'https://example.org/?q=one%26two&next=3':'one%26two',
                  'https://example.org/?search_query=한글#fragment':'한글',
                  'https://example.org/?x=1&query=O%27Brien':'O%27Brien',
                  'https://example.org/path#?q=false':'',
                  'https://example.org/?other=1':''}
        for name in ('Win_TimeLine.EnScript','Win_WebVisitKeyword.EnScript'):
            text=source(name)
            helper=text.split('String SearchParameter(',1)[1].split('String KeywordSqlText(',1)[0]
            names=re.findall(r'parameter.Find\("([^"=]+)=\"\) == 0',helper)
            self.assertEqual(names,['q','query','search_query'])
            self.assertIn('url.Find("#", start + 1)',helper)
            self.assertIn('firstFragment < start',helper)
            # Model the source's exact recognized parameter names on independent URL fixtures.
            for url,value in expected.items():
                parameters=urlsplit(url).query.split('&')
                actual=next((p.split('=',1)[1] for p in parameters if '=' in p and p.split('=',1)[0] in names),'')
                self.assertEqual(actual,value)
            method=text.split('void keyword_extract(',1)[1].split('void visit_csv(',1)[0]
            prefix=ast.literal_eval(re.search(r'String union_insert_q = ("[^\r\n]+) \+ browser \+ ("[^\r\n]+);',method).group(1))+'Fixture'+"','"
            addition=re.search(r'union_insert_q \+= ([^\r\n]+);',method).group(1)
            # KeywordSqlText returns SQL-escaped text without surrounding quotes.
            addition=addition.replace('KeywordSqlText(', 'KeywordText(')
            fields={'union_url':"https://example.org/?q=O'Brien",'union_keyword':"O'Brien",'union_title':"'한글'",'union_time':'2026/10/13'}
            # Use only literal concatenation and the escape model, preserving the actual source template.
            sql=prefix+expression(addition,variables=fields)
            db=sqlite3.connect(':memory:');self.addCleanup(db.close);db.execute('CREATE TABLE Web_Keyword(Browser,url,keyword,title,time)')
            db.execute(sql)
            self.assertEqual(db.execute('SELECT url,keyword,title,time FROM Web_Keyword').fetchone(),tuple(fields.values()))

    def test_recent_failed_batch_rolls_back(self):
        text=source('Win_LinkFile.EnScript').split('class RecentHandlerClass',1)[1]
        ddl=re.search(r'ExecuteNonQuery\("(CREATE TABLE IF NOT EXISTS App_RecentFile[^"\r\n]+)"\)',text).group(1)
        insert=re.search(r'ExecuteNonQuery\(("INSERT INTO App_RecentFile[^\r\n]+)\)\) \{',text).group(1)
        fields={n:'original' for n in re.findall(r'SqlValue\(n\.(\w+)\)',insert)}
        db=sqlite3.connect(':memory:');self.addCleanup(db.close);db.execute(ddl);db.execute(expression(insert,fields));db.commit()
        db.execute("CREATE TRIGGER reject_bad BEFORE INSERT ON App_RecentFile WHEN NEW.FileName='bad' BEGIN SELECT RAISE(ABORT,'fixture'); END;")
        db.execute('BEGIN TRANSACTION;');fields['LinkName']='good';db.execute(expression(insert,fields))
        fields['LinkName']='bad'
        with self.assertRaises(sqlite3.IntegrityError): db.execute(expression(insert,fields))
        db.execute('ROLLBACK;')
        self.assertEqual(db.execute('SELECT FileName FROM App_RecentFile').fetchall(),[('original',)])

    def test_timeline_failure_and_percent_bounds(self):
        run=source('Win_TimeLine.EnScript').split('virtual void Run(){',1)[1]
        self.assertIn('if(!lnk_csv.Open(',run)
        reopen=run[run.index('if(!sqliteFile.Open(exportPath, FileClass::APPEND)'):]
        self.assertLess(reopen.index('return;'),reopen.index('recent_lnk('))
        self.assertIn('TimeLine_dialog.Semaphore.Release();',reopen[:reopen.index('return;')])
        self.assertNotIn('"Timeline Database Created"',run)
        decoder=source('Win_WebVisitKeyword.EnScript').split('String qURLdecode(',1)[1].split('void sql2csv(',1)[0]
        self.assertNotIn('url[i+8]',decoder)
        self.assertIn('i + 2 < url.GetLength()',decoder)
        self.assertIn('IsHexDigit(url[i+1])',decoder)

    def test_shutdown_reads_evidence(self):
        text=source('Win_SystemInfo.EnScript')
        helper=text.split('String GetShutdownTime(',1)[1].split('String GetComputerName(',1)[0]
        for fragment in ('n.GetSize() == 8','n.GetData(value)','value.Seek(0)','value.ReadWinDate(date)'):
            self.assertIn(fragment,helper)
        self.assertNotIn('0x4C88FA9A896FD301',helper)
        self.assertIn('ActiveComputerNameValue = values.Find("ActiveComputerName")',text)

if __name__=='__main__': unittest.main(verbosity=2)
