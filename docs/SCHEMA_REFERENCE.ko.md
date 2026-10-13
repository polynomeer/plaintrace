# SQLite 선언 참조

[English](SCHEMA_REFERENCE.md) | **한국어**

2026-10-13 현재 체크아웃의 소스에서 생성한 사후 참조입니다. 당시 원본 설계 문서가 아닙니다.

`ExecuteNonQuery`에 직접 전달한 정적 CREATE TABLE 문자열만 추출합니다. 주석·동적 table_name·변수로 전달한 SQL·INSERT/SELECT는 제외합니다. 전체 런타임 스키마가 아니며 SQL을 실행하거나 오류를 수정하지 않습니다. 공백을 정리하고 동일 선언 위치를 합쳤으며 스키마 변형은 별도 보존했습니다. [데이터 모델](DATA_MODEL.ko.md)을 함께 읽으세요.

19 개 테이블 이름, 24개 선언 변형.

## App_Documents

변형 1: [Win_RecentDocuments.EnScript:113](../Win_RecentDocuments.EnScript#L113), [Win_RecentDocuments.EnScript:198](../Win_RecentDocuments.EnScript#L198), [Win_TimeLine.EnScript:648](../Win_TimeLine.EnScript#L648), [Win_TimeLine.EnScript:2055](../Win_TimeLine.EnScript#L2055).

```sql
CREATE TABLE App_Documents (
  Viewer LONGVARCHAR,
  Name LONGVARCHAR,
  mtime LONGVARCHAR,
  atime LONGVARCHAR,
  ctime LONGVARCHAR,
  FileSize LONGVARCHAR,
  DriveType LONGVARCHAR,
  Path LONGVARCHAR
);
```

## App_EXEFile

변형 1: [Win_LinkFile.EnScript:183](../Win_LinkFile.EnScript#L183), [Win_LinkFile.EnScript:808](../Win_LinkFile.EnScript#L808), [Win_PrefetchFile.EnScript:135](../Win_PrefetchFile.EnScript#L135), [Win_TimeLine.EnScript:2054](../Win_TimeLine.EnScript#L2054).

```sql
CREATE TABLE IF NOT EXISTS App_EXEFile (
  id INTEGER PRIMARY KEY,
  SourceFile LONGVARCHAR,
  FileName LONGVARCHAR,
  CreatedTime LONGVARCHAR,
  FileSize LONGVARCHAR,
  RunCount LONGVARCHAR,
  FilePath LONGVARCHAR
);
```

변형 2: [Win_PrefetchFile.EnScript:405](../Win_PrefetchFile.EnScript#L405).

```sql
CREATE TABLE IF NOT EXISTS App_EXEFile (
  id INTEGER PRIMARY KEY,
  SourceFile LONGVARCHAR,
  FileName LONGVARCHAR,
  CreatedTime LONGVARCHAR,
  FileSize LONGVARCHAR,
  RunCount INTEGER DEFAULT 0 NOT NULL,
  FilePath LONGVARCHAR
);
```

## App_LinkFile

변형 1: [Win_LinkFile.EnScript:169](../Win_LinkFile.EnScript#L169).

```sql
CREATE TABLE App_LinkFile (
  id INTEGER PRIMARY KEY,
  FileName LONGVARCHAR,
  OriginalFile LONGVARCHAR,
  AccessedTime LONGVARCHAR,
  CreatedTime LONGVARCHAR,
  WrittenTIme LONGVARCHAR,
  FileSize LONGVARCHAR,
  MachineID LONGVARCHAR,
  Volume LONGVARCHAR,
  DriveType LONGVARCHAR,
  SerialNumber LONGVARCHAR,
  MACaddress LONGVARCHAR
);
```

## App_PrefetchFile

변형 1: [Win_PrefetchFile.EnScript:121](../Win_PrefetchFile.EnScript#L121), [Win_PrefetchFile.EnScript:445](../Win_PrefetchFile.EnScript#L445).

```sql
CREATE TABLE App_PrefetchFile (
  id INTEGER PRIMARY KEY,
  FileName LONGVARCHAR,
  LastRunTime LONGVARCHAR,
  ModifiedTime LONGVARCHAR,
  CreatedTime LONGVARCHAR,
  ProcessEXE LONGVARCHAR,
  ProcessPath LONGVARCHAR,
  FileSize LONGVARCHAR,
  RunCount INTEGER DEFAULT 0 NOT NULL
);
```

## App_PrefetchFile_Sorted

변형 1: [Win_PrefetchFile.EnScript:507](../Win_PrefetchFile.EnScript#L507).

```sql
create table App_PrefetchFile_Sorted (
  ProcessEXE LONGVARCHAR,
  RunCount INTEGER DEFAULT 0 NOT NULL
);
```

## App_RecentFile

변형 1: [Win_LinkFile.EnScript:366](../Win_LinkFile.EnScript#L366).

```sql
CREATE TABLE IF NOT EXISTS App_RecentFile (
  id INTEGER PRIMARY KEY,
  FileName LONGVARCHAR,
  OriginalFile LONGVARCHAR,
  AccessedTime LONGVARCHAR,
  CreatedTime LONGVARCHAR,
  WrittenTime LONGVARCHAR,
  FileSize LONGVARCHAR,
  MachineID LONGVARCHAR,
  Volume LONGVARCHAR,
  DriveType LONGVARCHAR,
  SerialNumber LONGVARCHAR,
  MACaddress LONGVARCHAR
);
```

## File_Common

변형 1: [Win_FileMetaData.EnScript:130](../Win_FileMetaData.EnScript#L130).

```sql
CREATE TABLE File_Common (
  id INTEGER PRIMARY KEY,
  FileName LONGVARCHAR,
  FileExt LONGVARCHAR,
  FileCategory LONGVARCHAR,
  FileProperty LONGVARCHAR,
  FileSize LONGVARCHAR,
  AccessedTime LONGVARCHAR,
  CreatedTime LONGVARCHAR,
  WrittenTime LONGVARCHAR,
  FilePath LONGVARCHAR
);
```

## File_Deleted

변형 1: [Win_FileMetaData.EnScript:156](../Win_FileMetaData.EnScript#L156), [Win_FileMetaData.EnScript:294](../Win_FileMetaData.EnScript#L294), [Win_TimeLine.EnScript:2062](../Win_TimeLine.EnScript#L2062).

```sql
CREATE TABLE File_Deleted (
  id INTEGER PRIMARY KEY,
  FileName LONGVARCHAR,
  FileExt LONGVARCHAR,
  FileCategory LONGVARCHAR,
  FileProperty LONGVARCHAR,
  FileSize LONGVARCHAR,
  AccessedTime LONGVARCHAR,
  CreatedTime LONGVARCHAR,
  WrittenTime LONGVARCHAR,
  FilePath LONGVARCHAR
);
```

## File_Hidden

변형 1: [Win_FileMetaData.EnScript:143](../Win_FileMetaData.EnScript#L143).

```sql
CREATE TABLE File_Hidden (
  id INTEGER PRIMARY KEY,
  FileName LONGVARCHAR,
  FileExt LONGVARCHAR,
  FileCategory LONGVARCHAR,
  FileProperty LONGVARCHAR,
  FileSize LONGVARCHAR,
  AccessedTime LONGVARCHAR,
  CreatedTime LONGVARCHAR,
  WrittenTime LONGVARCHAR,
  FilePath LONGVARCHAR
);
```

## File_RecycleBin

변형 1: [Win_RecycleBin.EnScript:144](../Win_RecycleBin.EnScript#L144).

```sql
CREATE TABLE File_RecycleBin (
  id INTEGER PRIMARY KEY,
  FileName LONGVARCHAR,
  FileExt LONGVARCHAR,
  FileSize LONGVARCHAR,
  AccessedTime LONGVARCHAR,
  CreatedTime LONGVARCHAR,
  WrittenTime LONGVARCHAR,
  FilePath LONGVARCHAR,
  MD5HashValue LONGVARCHAR,
  DeletedFileName LONGVARCHAR,
  DeletedFileSize LONGVARCHAR,
  DeletedTime LONGVARCHAR,
  DeletedFilePath LONGVARCHAR,
  SID LONGVARCHAR
);
```

## PC_LogOnOff

변형 1: [Win_PowerLogOnOff.EnScript:164](../Win_PowerLogOnOff.EnScript#L164), [Win_PowerLogOnOff.EnScript:453](../Win_PowerLogOnOff.EnScript#L453), [Win_TimeLine.EnScript:2053](../Win_TimeLine.EnScript#L2053).

```sql
CREATE TABLE PC_LogOnOff (
  id INTEGER PRIMARY KEY,
  EventID LONGVARCHAR,
  LogonID LONGVARCHAR,
  User LONGVARCHAR,
  Event LONGVARCHAR,
  EventTime LONGVARCHAR,
  NetworkAddress LONGVARCHAR,
  LogonType LONGVARCHAR,
  SID LONGVARCHAR,
  GUID LONGVARCHAR
);
```

## PC_PowerOnOff

변형 1: [Win_PowerLogOnOff.EnScript:268](../Win_PowerLogOnOff.EnScript#L268), [Win_PowerLogOnOff.EnScript:599](../Win_PowerLogOnOff.EnScript#L599), [Win_TimeLine.EnScript:2052](../Win_TimeLine.EnScript#L2052).

```sql
CREATE TABLE PC_PowerOnOff (
  id INTEGER PRIMARY KEY,
  EventID LONGVARCHAR,
  Computer LONGVARCHAR,
  Event LONGVARCHAR,
  EventTime LONGVARCHAR,
  SID LONGVARCHAR,
  GUID LONGVARCHAR
);
```

## PC_UserAccount

변형 1: [Win_TimeLine.EnScript:2057](../Win_TimeLine.EnScript#L2057), [Win_UserAccount.EnScript:162](../Win_UserAccount.EnScript#L162).

```sql
CREATE TABLE PC_UserAccount (
  id INTEGER PRIMARY KEY,
  User LONGVARCHAR,
  RID LONGVARCHAR,
  LogonCount LONGVARCHAR,
  InvalidLogonCount LONGVARHAR,
  LastLogonTime LONGVARCHAR,
  InvalidLogonTime LONGVARCHAR,
  LastPasswordChangedTime LONGVARCHAR,
  ExpiredTime LONGVARCHAR,
  PasswordExpiredTime LONGVARCHAR,
  FullName LONGVARCHAR,
  Description LONGVARCHAR,
  HomeDirectory LONGVARCHAR,
  LMHash LONGVARCHAR,
  NTHash LONGVARCHAR,
  Activation LONGVARCHAR,
  UserPrivilege LONGVARCHAR,
  CountryCode LONGVARCHAR
);
```

## USB_EventLog

변형 1: [Win_TimeLine.EnScript:2056](../Win_TimeLine.EnScript#L2056), [Win_USBInfo.EnScript:237](../Win_USBInfo.EnScript#L237), [Win_USBInfo.EnScript:715](../Win_USBInfo.EnScript#L715).

```sql
CREATE TABLE USB_EventLog (
  id INTEGER PRIMARY KEY,
  Vendor LONGVARCHAR,
  Product LONGVARCHAR,
  State LONGVARCHAR,
  GeneratedTime LONGVARCHAR,
  WrittenTime LONGVARCHAR,
  FirmwareRevision LONGVARCHAR,
  SerialNumber LONGVARCHAR,
  LifeTimeGUID LONGVARCHAR,
  SourceGUID LONGVARCHAR,
  Source LONGVARCHAR,
  Computer LONGVARCHAR,
  SID LONGVARCHAR
);
```

## Web_Download

변형 1: [Win_TimeLine.EnScript:2058](../Win_TimeLine.EnScript#L2058), [Win_WebDownloads.EnScript:108](../Win_WebDownloads.EnScript#L108).

```sql
CREATE TABLE Web_Download (
  Browser LONGVARCHAR,
  Path LONGVARCHAR,
  StartTime LONGVARCHAR,
  EndTime LONGVARCHAR,
  RecvBytes LONGVARCHAR,
  TotalBytes,
  Url LONGVARCHAR
);
```

변형 2: [Win_WebDownloads.EnScript:257](../Win_WebDownloads.EnScript#L257), [Win_WebDownloads.EnScript:553](../Win_WebDownloads.EnScript#L553).

```sql
CREATE TABLE Web_Download (
  Browser LONGVARCHAR,
  Path LONGVARCHAR,
  StartTime LONGVARCHAR,
  EndTime LONGVARCHAR,
  RecvBytes LONGVARCHAR,
  TotalBytes LONGVARCHAR,
  Url LONGVARCHAR
);
```

## Web_Host

변형 1: [Win_TimeLine.EnScript:2060](../Win_TimeLine.EnScript#L2060), [Win_WebVisitKeyword.EnScript:393](../Win_WebVisitKeyword.EnScript#L393), [Win_WebVisitKeyword.EnScript:831](../Win_WebVisitKeyword.EnScript#L831), [Win_WebVisitKeyword.EnScript:938](../Win_WebVisitKeyword.EnScript#L938).

```sql
CREATE TABLE Web_Host (
  Browser LONGVARCHAR,
  host LONGVARCHAR,
  visit_count INTEGER DEFAULT 0 NOT NULL
);
```

## Web_Host_Union

변형 1: [Win_WebVisitKeyword.EnScript:1250](../Win_WebVisitKeyword.EnScript#L1250).

```sql
create table Web_Host_Union (
  host LONGVARCHAR,
  visit_count INTEGER DEFAULT 0
);
```

## Web_Keyword

변형 1: [Win_TimeLine.EnScript:2061](../Win_TimeLine.EnScript#L2061), [Win_WebVisitKeyword.EnScript:205](../Win_WebVisitKeyword.EnScript#L205), [Win_WebVisitKeyword.EnScript:830](../Win_WebVisitKeyword.EnScript#L830), [Win_WebVisitKeyword.EnScript:937](../Win_WebVisitKeyword.EnScript#L937).

```sql
CREATE TABLE Web_Keyword (
  Browser LONGVARCHAR,
  url LONGVARCHAR,
  keyword LONGVARCHAR,
  title LONGVARCHAR,
  time LONGVARCHAR
);
```

변형 2: [Win_WebVisitKeyword.EnScript:588](../Win_WebVisitKeyword.EnScript#L588).

```sql
CREATE TABLE IF NOT EXISTS Web_Keyword (
  Browser LONGVARCHAR,
  url LONGVARCHAR,
  keyword LONGVARCHAR,
  title LONGVARCHAR,
  time LONGVARCHAR
);
```

## Web_Visit

변형 1: [Win_TimeLine.EnScript:2059](../Win_TimeLine.EnScript#L2059), [Win_WebVisitKeyword.EnScript:394](../Win_WebVisitKeyword.EnScript#L394), [Win_WebVisitKeyword.EnScript:829](../Win_WebVisitKeyword.EnScript#L829).

```sql
CREATE TABLE Web_Visit (
  Browser LONGVARCHAR,
  url LONGVARCHAR,
  title LONGVARCHAR,
  time LONGVARCHAR
);
```

변형 2: [Win_WebVisitKeyword.EnScript:109](../Win_WebVisitKeyword.EnScript#L109).

```sql
CREATE TABLE Web_Visit (
  Browser LONGVARCHAR,
  url LONGVARCHAR,
  time LONGVARCHAR
);
```

변형 3: [Win_WebVisitKeyword.EnScript:936](../Win_WebVisitKeyword.EnScript#L936).

```sql
CREATE TABLE Web_Visit(
  Browser LONGVARCHAR,
  url LONGVARCHAR,
  title LONGVARCHAR,
  time LONGVARCHAR
);
```

```sh
python3 tools/generate_source_reference.py --check
```
