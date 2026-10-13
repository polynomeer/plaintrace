# Code Structure and Source Index

**English** | [한국어](CODE_STRUCTURE.ko.md)

Generated on 2026-10-13 from archived source. This is a retrospective reference, not an original design document.

## Repository Layout

The 13 root EnScript files are the preserved implementation; `tools/` contains present-day Python utilities; `docs/` contains retrospective documents and JSON baselines. Module responsibilities are in [analysis](ANALYSIS.md); runtime relationships are in [detailed design](SYSTEM_DESIGN.md).

## Tools

- [inspect_sources.py](../tools/inspect_sources.py): Decode source and show classes or numbered lines.
- [enscript_textconv.py](../tools/enscript_textconv.py): Decode Git diffs without changing blobs.
- [verify_archive.py](../tools/verify_archive.py): Verify current source, archived README and commit baseline; needs local archive ref.
- [reconstruct_history.py](../tools/reconstruct_history.py): Read-only plan by default; --apply mutates Git history and is not a routine check.
- [generate_source_reference.py](../tools/generate_source_reference.py): Generate/check this index and SQL appendix.
- [verify_documentation.py](../tools/verify_documentation.py): Check local links, language pairs and requirement/test mappings.

## Classes and Methods

Declaration locations exclude comments and strings. Constructors are included, forward declarations are omitted. Extraction covers selected return types and is not a compiler-level symbol table.

### Plain View of Multi Artifacts.EnScript

94 lines; UTF-8 / ASCII.

| Class / declaration | Methods / locations |
| --- | --- |
| `ExportDialogClass` ([Plain View of Multi Artifacts.EnScript:17](../Plain%20View%20of%20Multi%20Artifacts.EnScript#L17)) | `ExportDialogClass` ([Plain View of Multi Artifacts.EnScript:20](../Plain%20View%20of%20Multi%20Artifacts.EnScript#L20)) |
| `MainDialogClass` ([Plain View of Multi Artifacts.EnScript:27](../Plain%20View%20of%20Multi%20Artifacts.EnScript#L27)) | `MainDialogClass` ([Plain View of Multi Artifacts.EnScript:43](../Plain%20View%20of%20Multi%20Artifacts.EnScript#L43)) |
| `MainClass` ([Plain View of Multi Artifacts.EnScript:63](../Plain%20View%20of%20Multi%20Artifacts.EnScript#L63)) | `Main` ([Plain View of Multi Artifacts.EnScript:64](../Plain%20View%20of%20Multi%20Artifacts.EnScript#L64)) |

### Win_FileMetaData.EnScript

476 lines; UTF-8 / ASCII.

| Class / declaration | Methods / locations |
| --- | --- |
| `FileListClass` ([Win_FileMetaData.EnScript:3](../Win_FileMetaData.EnScript#L3)) | `FileListClass` ([Win_FileMetaData.EnScript:16](../Win_FileMetaData.EnScript#L16)) |
| `FileHandlerClass` ([Win_FileMetaData.EnScript:38](../Win_FileMetaData.EnScript#L38)) | `FileHandlerClass` ([Win_FileMetaData.EnScript:57](../Win_FileMetaData.EnScript#L57)), `BuildMenu` ([Win_FileMetaData.EnScript:87](../Win_FileMetaData.EnScript#L87)), `MenuEvent` ([Win_FileMetaData.EnScript:93](../Win_FileMetaData.EnScript#L93)) |
| `FileThreadClass` ([Win_FileMetaData.EnScript:184](../Win_FileMetaData.EnScript#L184)) | `FileThreadClass` ([Win_FileMetaData.EnScript:189](../Win_FileMetaData.EnScript#L189)), `Run` ([Win_FileMetaData.EnScript:197](../Win_FileMetaData.EnScript#L197)), `BuildSqlite` ([Win_FileMetaData.EnScript:279](../Win_FileMetaData.EnScript#L279)) |
| `FileDialogClass` ([Win_FileMetaData.EnScript:316](../Win_FileMetaData.EnScript#L316)) | `FileDialogClass` ([Win_FileMetaData.EnScript:334](../Win_FileMetaData.EnScript#L334)), `ChildEvent` ([Win_FileMetaData.EnScript:369](../Win_FileMetaData.EnScript#L369)), `Setup` ([Win_FileMetaData.EnScript:442](../Win_FileMetaData.EnScript#L442)), `TimerEvent` ([Win_FileMetaData.EnScript:447](../Win_FileMetaData.EnScript#L447)), `CanClose` ([Win_FileMetaData.EnScript:470](../Win_FileMetaData.EnScript#L470)) |

### Win_LinkFile.EnScript

1264 lines; UTF-16LE BOM.

| Class / declaration | Methods / locations |
| --- | --- |
| `LinkListClass` ([Win_LinkFile.EnScript:3](../Win_LinkFile.EnScript#L3)) | `LinkListClass` ([Win_LinkFile.EnScript:17](../Win_LinkFile.EnScript#L17)) |
| `RecentListClass` ([Win_LinkFile.EnScript:38](../Win_LinkFile.EnScript#L38)) | `RecentListClass` ([Win_LinkFile.EnScript:51](../Win_LinkFile.EnScript#L51)) |
| `LinkHandlerClass` ([Win_LinkFile.EnScript:74](../Win_LinkFile.EnScript#L74)) | `LinkHandlerClass` ([Win_LinkFile.EnScript:94](../Win_LinkFile.EnScript#L94)), `BuildMenu` ([Win_LinkFile.EnScript:124](../Win_LinkFile.EnScript#L124)), `MenuEvent` ([Win_LinkFile.EnScript:131](../Win_LinkFile.EnScript#L131)) |
| `LinkExtractDialogClass` ([Win_LinkFile.EnScript:224](../Win_LinkFile.EnScript#L224)) | `LinkExtractDialogClass` ([Win_LinkFile.EnScript:230](../Win_LinkFile.EnScript#L230)), `CreateExportPath` ([Win_LinkFile.EnScript:239](../Win_LinkFile.EnScript#L239)), `CanClose` ([Win_LinkFile.EnScript:259](../Win_LinkFile.EnScript#L259)) |
| `RecentHandlerClass` ([Win_LinkFile.EnScript:272](../Win_LinkFile.EnScript#L272)) | `RecentHandlerClass` ([Win_LinkFile.EnScript:290](../Win_LinkFile.EnScript#L290)), `BuildMenu` ([Win_LinkFile.EnScript:320](../Win_LinkFile.EnScript#L320)), `MenuEvent` ([Win_LinkFile.EnScript:326](../Win_LinkFile.EnScript#L326)) |
| `LinkThreadClass` ([Win_LinkFile.EnScript:357](../Win_LinkFile.EnScript#L357)) | `LinkThreadClass` ([Win_LinkFile.EnScript:361](../Win_LinkFile.EnScript#L361)), `_x2c` ([Win_LinkFile.EnScript:372](../Win_LinkFile.EnScript#L372)), `DecodePath` ([Win_LinkFile.EnScript:384](../Win_LinkFile.EnScript#L384)), `Run` ([Win_LinkFile.EnScript:422](../Win_LinkFile.EnScript#L422)), `BuildSqlite` ([Win_LinkFile.EnScript:752](../Win_LinkFile.EnScript#L752)) |
| `RecentThreadClass` ([Win_LinkFile.EnScript:799](../Win_LinkFile.EnScript#L799)) | `RecentThreadClass` ([Win_LinkFile.EnScript:803](../Win_LinkFile.EnScript#L803)), `Run` ([Win_LinkFile.EnScript:811](../Win_LinkFile.EnScript#L811)) |
| `LinkDialogClass` ([Win_LinkFile.EnScript:1120](../Win_LinkFile.EnScript#L1120)) | `LinkDialogClass` ([Win_LinkFile.EnScript:1152](../Win_LinkFile.EnScript#L1152)), `ChildEvent` ([Win_LinkFile.EnScript:1181](../Win_LinkFile.EnScript#L1181)), `Setup` ([Win_LinkFile.EnScript:1237](../Win_LinkFile.EnScript#L1237)), `TimerEvent` ([Win_LinkFile.EnScript:1243](../Win_LinkFile.EnScript#L1243)), `CanClose` ([Win_LinkFile.EnScript:1259](../Win_LinkFile.EnScript#L1259)) |

### Win_PowerLogOnOff.EnScript

809 lines; UTF-16LE BOM.

| Class / declaration | Methods / locations |
| --- | --- |
| `LogonTypeClass` ([Win_PowerLogOnOff.EnScript:3](../Win_PowerLogOnOff.EnScript#L3)) | `LogonTypeClass` ([Win_PowerLogOnOff.EnScript:9](../Win_PowerLogOnOff.EnScript#L9)) |
| `LogonListClass` ([Win_PowerLogOnOff.EnScript:18](../Win_PowerLogOnOff.EnScript#L18)) | `LogonListClass` ([Win_PowerLogOnOff.EnScript:31](../Win_PowerLogOnOff.EnScript#L31)) |
| `PowerListClass` ([Win_PowerLogOnOff.EnScript:49](../Win_PowerLogOnOff.EnScript#L49)) | `PowerListClass` ([Win_PowerLogOnOff.EnScript:57](../Win_PowerLogOnOff.EnScript#L57)) |
| `LogonHandlerClass` ([Win_PowerLogOnOff.EnScript:72](../Win_PowerLogOnOff.EnScript#L72)) | `LogonHandlerClass` ([Win_PowerLogOnOff.EnScript:91](../Win_PowerLogOnOff.EnScript#L91)), `BuildMenu` ([Win_PowerLogOnOff.EnScript:122](../Win_PowerLogOnOff.EnScript#L122)), `MenuEvent` ([Win_PowerLogOnOff.EnScript:128](../Win_PowerLogOnOff.EnScript#L128)) |
| `PowerHandlerClass` ([Win_PowerLogOnOff.EnScript:190](../Win_PowerLogOnOff.EnScript#L190)) | `PowerHandlerClass` ([Win_PowerLogOnOff.EnScript:204](../Win_PowerLogOnOff.EnScript#L204)), `BuildMenu` ([Win_PowerLogOnOff.EnScript:224](../Win_PowerLogOnOff.EnScript#L224)), `MenuEvent` ([Win_PowerLogOnOff.EnScript:230](../Win_PowerLogOnOff.EnScript#L230)) |
| `LogonThreadClass` ([Win_PowerLogOnOff.EnScript:298](../Win_PowerLogOnOff.EnScript#L298)) | `LogonThreadClass` ([Win_PowerLogOnOff.EnScript:303](../Win_PowerLogOnOff.EnScript#L303)), `Run` ([Win_PowerLogOnOff.EnScript:311](../Win_PowerLogOnOff.EnScript#L311)), `BuildSqlite` ([Win_PowerLogOnOff.EnScript:437](../Win_PowerLogOnOff.EnScript#L437)) |
| `PowerThreadClass` ([Win_PowerLogOnOff.EnScript:474](../Win_PowerLogOnOff.EnScript#L474)) | `PowerThreadClass` ([Win_PowerLogOnOff.EnScript:479](../Win_PowerLogOnOff.EnScript#L479)), `Run` ([Win_PowerLogOnOff.EnScript:487](../Win_PowerLogOnOff.EnScript#L487)), `BuildSqlite` ([Win_PowerLogOnOff.EnScript:582](../Win_PowerLogOnOff.EnScript#L582)) |
| `LogonTypeHandlerClass` ([Win_PowerLogOnOff.EnScript:620](../Win_PowerLogOnOff.EnScript#L620)) | `LogonTypeHandlerClass` ([Win_PowerLogOnOff.EnScript:625](../Win_PowerLogOnOff.EnScript#L625)) |
| `LogonTypeReportClass` ([Win_PowerLogOnOff.EnScript:634](../Win_PowerLogOnOff.EnScript#L634)) | `LogonTypeReportClass` ([Win_PowerLogOnOff.EnScript:639](../Win_PowerLogOnOff.EnScript#L639)), `BuildDocument` ([Win_PowerLogOnOff.EnScript:657](../Win_PowerLogOnOff.EnScript#L657)) |
| `LogonDialogClass` ([Win_PowerLogOnOff.EnScript:681](../Win_PowerLogOnOff.EnScript#L681)) | `LogonDialogClass` ([Win_PowerLogOnOff.EnScript:709](../Win_PowerLogOnOff.EnScript#L709)), `ChildEvent` ([Win_PowerLogOnOff.EnScript:738](../Win_PowerLogOnOff.EnScript#L738)), `Setup` ([Win_PowerLogOnOff.EnScript:775](../Win_PowerLogOnOff.EnScript#L775)), `TimerEvent` ([Win_PowerLogOnOff.EnScript:780](../Win_PowerLogOnOff.EnScript#L780)), `CanClose` ([Win_PowerLogOnOff.EnScript:803](../Win_PowerLogOnOff.EnScript#L803)) |

### Win_PrefetchFile.EnScript

834 lines; UTF-16LE BOM.

| Class / declaration | Methods / locations |
| --- | --- |
| `PrefetchListClass` ([Win_PrefetchFile.EnScript:4](../Win_PrefetchFile.EnScript#L4)) | `PrefetchListClass` ([Win_PrefetchFile.EnScript:15](../Win_PrefetchFile.EnScript#L15)) |
| `PrefetchHandlerClass` ([Win_PrefetchFile.EnScript:34](../Win_PrefetchFile.EnScript#L34)) | `PrefetchHandlerClass` ([Win_PrefetchFile.EnScript:51](../Win_PrefetchFile.EnScript#L51)), `BuildMenu` ([Win_PrefetchFile.EnScript:76](../Win_PrefetchFile.EnScript#L76)), `MenuEvent` ([Win_PrefetchFile.EnScript:83](../Win_PrefetchFile.EnScript#L83)) |
| `PrefetchExtractDialogClass` ([Win_PrefetchFile.EnScript:176](../Win_PrefetchFile.EnScript#L176)) | `PrefetchExtractDialogClass` ([Win_PrefetchFile.EnScript:182](../Win_PrefetchFile.EnScript#L182)), `CreateExportPath` ([Win_PrefetchFile.EnScript:192](../Win_PrefetchFile.EnScript#L192)), `CanClose` ([Win_PrefetchFile.EnScript:212](../Win_PrefetchFile.EnScript#L212)) |
| `PrefetchValueListClass` ([Win_PrefetchFile.EnScript:225](../Win_PrefetchFile.EnScript#L225)) | `PrefetchValueListClass` ([Win_PrefetchFile.EnScript:230](../Win_PrefetchFile.EnScript#L230)) |
| `PrefetchValueHandlerClass` ([Win_PrefetchFile.EnScript:239](../Win_PrefetchFile.EnScript#L239)) | `PrefetchValueHandlerClass` ([Win_PrefetchFile.EnScript:244](../Win_PrefetchFile.EnScript#L244)) |
| `PrefetchThreadClass` ([Win_PrefetchFile.EnScript:259](../Win_PrefetchFile.EnScript#L259)) | `PrefetchThreadClass` ([Win_PrefetchFile.EnScript:265](../Win_PrefetchFile.EnScript#L265)), `Run` ([Win_PrefetchFile.EnScript:273](../Win_PrefetchFile.EnScript#L273)), `BuildSqlite` ([Win_PrefetchFile.EnScript:387](../Win_PrefetchFile.EnScript#L387)), `BuildSqlite1` ([Win_PrefetchFile.EnScript:427](../Win_PrefetchFile.EnScript#L427)) |
| `CreatePrefetchChartClass` ([Win_PrefetchFile.EnScript:472](../Win_PrefetchFile.EnScript#L472)) | `CreatePrefetchChartClass` ([Win_PrefetchFile.EnScript:477](../Win_PrefetchFile.EnScript#L477)), `GetChart` ([Win_PrefetchFile.EnScript:481](../Win_PrefetchFile.EnScript#L481)) |
| `PrefetchDialogClass` ([Win_PrefetchFile.EnScript:621](../Win_PrefetchFile.EnScript#L621)) | `PrefetchDialogClass` ([Win_PrefetchFile.EnScript:649](../Win_PrefetchFile.EnScript#L649)), `ChildEvent` ([Win_PrefetchFile.EnScript:681](../Win_PrefetchFile.EnScript#L681)), `BuildChart` ([Win_PrefetchFile.EnScript:764](../Win_PrefetchFile.EnScript#L764)), `ShowChart` ([Win_PrefetchFile.EnScript:770](../Win_PrefetchFile.EnScript#L770)), `MapChartTypes` ([Win_PrefetchFile.EnScript:798](../Win_PrefetchFile.EnScript#L798)), `Setup` ([Win_PrefetchFile.EnScript:810](../Win_PrefetchFile.EnScript#L810)), `TimerEvent` ([Win_PrefetchFile.EnScript:815](../Win_PrefetchFile.EnScript#L815)), `CanClose` ([Win_PrefetchFile.EnScript:829](../Win_PrefetchFile.EnScript#L829)) |

### Win_RecentDocuments.EnScript

691 lines; UTF-8 / ASCII.

| Class / declaration | Methods / locations |
| --- | --- |
| `RecentDocListClass` ([Win_RecentDocuments.EnScript:3](../Win_RecentDocuments.EnScript#L3)) | `RecentDocListClass` ([Win_RecentDocuments.EnScript:13](../Win_RecentDocuments.EnScript#L13)) |
| `RecentDocHandlerClass` ([Win_RecentDocuments.EnScript:30](../Win_RecentDocuments.EnScript#L30)) | `RecentDocHandlerClass` ([Win_RecentDocuments.EnScript:45](../Win_RecentDocuments.EnScript#L45)), `BuildMenu` ([Win_RecentDocuments.EnScript:70](../Win_RecentDocuments.EnScript#L70)), `MenuEvent` ([Win_RecentDocuments.EnScript:77](../Win_RecentDocuments.EnScript#L77)) |
| `RecentDocThreadClass` ([Win_RecentDocuments.EnScript:138](../Win_RecentDocuments.EnScript#L138)) | `RecentDocThreadClass` ([Win_RecentDocuments.EnScript:146](../Win_RecentDocuments.EnScript#L146)), `cmp_lnk_recent` ([Win_RecentDocuments.EnScript:154](../Win_RecentDocuments.EnScript#L154)), `recent_lnk` ([Win_RecentDocuments.EnScript:166](../Win_RecentDocuments.EnScript#L166)), `print_str_list` ([Win_RecentDocuments.EnScript:295](../Win_RecentDocuments.EnScript#L295)), `str_cmp_add` ([Win_RecentDocuments.EnScript:300](../Win_RecentDocuments.EnScript#L300)), `recent_doc` ([Win_RecentDocuments.EnScript:312](../Win_RecentDocuments.EnScript#L312)), `pp_doc` ([Win_RecentDocuments.EnScript:366](../Win_RecentDocuments.EnScript#L366)), `word_doc` ([Win_RecentDocuments.EnScript:378](../Win_RecentDocuments.EnScript#L378)), `excel_doc` ([Win_RecentDocuments.EnScript:390](../Win_RecentDocuments.EnScript#L390)), `hwp_doc` ([Win_RecentDocuments.EnScript:402](../Win_RecentDocuments.EnScript#L402)), `adobe_doc` ([Win_RecentDocuments.EnScript:410](../Win_RecentDocuments.EnScript#L410)), `Run` ([Win_RecentDocuments.EnScript:417](../Win_RecentDocuments.EnScript#L417)) |
| `RecentDocDialogClass` ([Win_RecentDocuments.EnScript:584](../Win_RecentDocuments.EnScript#L584)) | `RecentDocDialogClass` ([Win_RecentDocuments.EnScript:600](../Win_RecentDocuments.EnScript#L600)), `ChildEvent` ([Win_RecentDocuments.EnScript:621](../Win_RecentDocuments.EnScript#L621)), `Setup` ([Win_RecentDocuments.EnScript:657](../Win_RecentDocuments.EnScript#L657)), `TimerEvent` ([Win_RecentDocuments.EnScript:662](../Win_RecentDocuments.EnScript#L662)), `CanClose` ([Win_RecentDocuments.EnScript:686](../Win_RecentDocuments.EnScript#L686)) |

### Win_RecycleBin.EnScript

446 lines; UTF-16LE BOM.

| Class / declaration | Methods / locations |
| --- | --- |
| `RecycleListClass` ([Win_RecycleBin.EnScript:3](../Win_RecycleBin.EnScript#L3)) | `RecycleListClass` ([Win_RecycleBin.EnScript:18](../Win_RecycleBin.EnScript#L18)) |
| `RecycleHandlerClass` ([Win_RecycleBin.EnScript:43](../Win_RecycleBin.EnScript#L43)) | `RecycleHandlerClass` ([Win_RecycleBin.EnScript:65](../Win_RecycleBin.EnScript#L65)), `BuildMenu` ([Win_RecycleBin.EnScript:102](../Win_RecycleBin.EnScript#L102)), `MenuEvent` ([Win_RecycleBin.EnScript:109](../Win_RecycleBin.EnScript#L109)) |
| `ExtractDialogClass` ([Win_RecycleBin.EnScript:179](../Win_RecycleBin.EnScript#L179)) | `ExtractDialogClass` ([Win_RecycleBin.EnScript:185](../Win_RecycleBin.EnScript#L185)), `CreateExportPath` ([Win_RecycleBin.EnScript:193](../Win_RecycleBin.EnScript#L193)), `CanClose` ([Win_RecycleBin.EnScript:213](../Win_RecycleBin.EnScript#L213)) |
| `RecycleThreadClass` ([Win_RecycleBin.EnScript:226](../Win_RecycleBin.EnScript#L226)) | `RecycleThreadClass` ([Win_RecycleBin.EnScript:231](../Win_RecycleBin.EnScript#L231)), `Run` ([Win_RecycleBin.EnScript:239](../Win_RecycleBin.EnScript#L239)) |
| `RecycleDialogClass` ([Win_RecycleBin.EnScript:331](../Win_RecycleBin.EnScript#L331)) | `RecycleDialogClass` ([Win_RecycleBin.EnScript:349](../Win_RecycleBin.EnScript#L349)), `ChildEvent` ([Win_RecycleBin.EnScript:371](../Win_RecycleBin.EnScript#L371)), `Setup` ([Win_RecycleBin.EnScript:410](../Win_RecycleBin.EnScript#L410)), `TimerEvent` ([Win_RecycleBin.EnScript:417](../Win_RecycleBin.EnScript#L417)), `CanClose` ([Win_RecycleBin.EnScript:440](../Win_RecycleBin.EnScript#L440)) |

### Win_SystemInfo.EnScript

689 lines; UTF-8 / ASCII.

| Class / declaration | Methods / locations |
| --- | --- |
| `SysInfoListClass` ([Win_SystemInfo.EnScript:1](../Win_SystemInfo.EnScript#L1)) | `SysInfoListClass` ([Win_SystemInfo.EnScript:6](../Win_SystemInfo.EnScript#L6)) |
| `_HandlerClass` ([Win_SystemInfo.EnScript:14](../Win_SystemInfo.EnScript#L14)) | `_HandlerClass` ([Win_SystemInfo.EnScript:18](../Win_SystemInfo.EnScript#L18)) |
| `_HandlerClass1` ([Win_SystemInfo.EnScript:25](../Win_SystemInfo.EnScript#L25)) | `_HandlerClass1` ([Win_SystemInfo.EnScript:29](../Win_SystemInfo.EnScript#L29)) |
| `_HandlerClass2` ([Win_SystemInfo.EnScript:37](../Win_SystemInfo.EnScript#L37)) | `_HandlerClass2` ([Win_SystemInfo.EnScript:41](../Win_SystemInfo.EnScript#L41)) |
| `FileReportClass` ([Win_SystemInfo.EnScript:49](../Win_SystemInfo.EnScript#L49)) | `FileReportClass` ([Win_SystemInfo.EnScript:55](../Win_SystemInfo.EnScript#L55)), `BuildDocument` ([Win_SystemInfo.EnScript:144](../Win_SystemInfo.EnScript#L144)) |
| `VolumeReportClass` ([Win_SystemInfo.EnScript:167](../Win_SystemInfo.EnScript#L167)) | `VolumeReportClass` ([Win_SystemInfo.EnScript:173](../Win_SystemInfo.EnScript#L173)), `BuildDocument` ([Win_SystemInfo.EnScript:218](../Win_SystemInfo.EnScript#L218)) |
| `OSReportClass` ([Win_SystemInfo.EnScript:239](../Win_SystemInfo.EnScript#L239)) | `OSReportClass` ([Win_SystemInfo.EnScript:245](../Win_SystemInfo.EnScript#L245)), `GetShutdownTime` ([Win_SystemInfo.EnScript:346](../Win_SystemInfo.EnScript#L346)), `GetComputerName` ([Win_SystemInfo.EnScript:364](../Win_SystemInfo.EnScript#L364)), `GetProductKey` ([Win_SystemInfo.EnScript:377](../Win_SystemInfo.EnScript#L377)), `BuildDocument` ([Win_SystemInfo.EnScript:430](../Win_SystemInfo.EnScript#L430)) |
| `CreateChartClass` ([Win_SystemInfo.EnScript:452](../Win_SystemInfo.EnScript#L452)) | `CreateChartClass` ([Win_SystemInfo.EnScript:454](../Win_SystemInfo.EnScript#L454)), `GetChart` ([Win_SystemInfo.EnScript:459](../Win_SystemInfo.EnScript#L459)) |
| `SysInfoDialogClass` ([Win_SystemInfo.EnScript:558](../Win_SystemInfo.EnScript#L558)) | `SysInfoDialogClass` ([Win_SystemInfo.EnScript:585](../Win_SystemInfo.EnScript#L585)), `ChildEvent` ([Win_SystemInfo.EnScript:609](../Win_SystemInfo.EnScript#L609)), `BuildChart` ([Win_SystemInfo.EnScript:629](../Win_SystemInfo.EnScript#L629)), `ShowChart` ([Win_SystemInfo.EnScript:635](../Win_SystemInfo.EnScript#L635)), `MapChartTypes` ([Win_SystemInfo.EnScript:666](../Win_SystemInfo.EnScript#L666)), `PaintEvent` ([Win_SystemInfo.EnScript:677](../Win_SystemInfo.EnScript#L677)) |

### Win_TimeLine.EnScript

2315 lines; UTF-8 / ASCII.

| Class / declaration | Methods / locations |
| --- | --- |
| `TimeLineWindow` ([Win_TimeLine.EnScript:3](../Win_TimeLine.EnScript#L3)) | `TimeLineWindow` ([Win_TimeLine.EnScript:8](../Win_TimeLine.EnScript#L8)), `PaintEvent` ([Win_TimeLine.EnScript:28](../Win_TimeLine.EnScript#L28)) |
| `TimeLineThreadClass` ([Win_TimeLine.EnScript:52](../Win_TimeLine.EnScript#L52)) | `TimeLineThreadClass` ([Win_TimeLine.EnScript:57](../Win_TimeLine.EnScript#L57)), `FileDeleted` ([Win_TimeLine.EnScript:69](../Win_TimeLine.EnScript#L69)), `USBEventLog` ([Win_TimeLine.EnScript:83](../Win_TimeLine.EnScript#L83)), `LogOn` ([Win_TimeLine.EnScript:183](../Win_TimeLine.EnScript#L183)), `PowerOn` ([Win_TimeLine.EnScript:266](../Win_TimeLine.EnScript#L266)), `UserAccount` ([Win_TimeLine.EnScript:314](../Win_TimeLine.EnScript#L314)), `PrefetchEXE` ([Win_TimeLine.EnScript:548](../Win_TimeLine.EnScript#L548)), `cmp_lnk_recent` ([Win_TimeLine.EnScript:610](../Win_TimeLine.EnScript#L610)), `recent_lnk` ([Win_TimeLine.EnScript:622](../Win_TimeLine.EnScript#L622)), `print_str_list` ([Win_TimeLine.EnScript:745](../Win_TimeLine.EnScript#L745)), `str_cmp_add` ([Win_TimeLine.EnScript:750](../Win_TimeLine.EnScript#L750)), `recent_doc` ([Win_TimeLine.EnScript:762](../Win_TimeLine.EnScript#L762)), `pp_doc` ([Win_TimeLine.EnScript:816](../Win_TimeLine.EnScript#L816)), `word_doc` ([Win_TimeLine.EnScript:828](../Win_TimeLine.EnScript#L828)), `excel_doc` ([Win_TimeLine.EnScript:840](../Win_TimeLine.EnScript#L840)), `hwp_doc` ([Win_TimeLine.EnScript:852](../Win_TimeLine.EnScript#L852)), `adobe_doc` ([Win_TimeLine.EnScript:860](../Win_TimeLine.EnScript#L860)), `ExportLink` ([Win_TimeLine.EnScript:867](../Win_TimeLine.EnScript#L867)), `host_extract` ([Win_TimeLine.EnScript:946](../Win_TimeLine.EnScript#L946)), `sql2csv` ([Win_TimeLine.EnScript:975](../Win_TimeLine.EnScript#L975)), `download_sql2csv` ([Win_TimeLine.EnScript:1122](../Win_TimeLine.EnScript#L1122)), `keyword_extract` ([Win_TimeLine.EnScript:1359](../Win_TimeLine.EnScript#L1359)), `visit_csv` ([Win_TimeLine.EnScript:1529](../Win_TimeLine.EnScript#L1529)), `download_csv` ([Win_TimeLine.EnScript:1580](../Win_TimeLine.EnScript#L1580)), `IE_timeformat` ([Win_TimeLine.EnScript:1634](../Win_TimeLine.EnScript#L1634)), `IE_search` ([Win_TimeLine.EnScript:1656](../Win_TimeLine.EnScript#L1656)), `IE_index_dat` ([Win_TimeLine.EnScript:1686](../Win_TimeLine.EnScript#L1686)), `IE_WebCache_dat` ([Win_TimeLine.EnScript:1779](../Win_TimeLine.EnScript#L1779)), `export_file` ([Win_TimeLine.EnScript:1910](../Win_TimeLine.EnScript#L1910)), `WebArtifact` ([Win_TimeLine.EnScript:1981](../Win_TimeLine.EnScript#L1981)), `Run` ([Win_TimeLine.EnScript:2006](../Win_TimeLine.EnScript#L2006)) |
| `TimeLineDialogClass` ([Win_TimeLine.EnScript:2125](../Win_TimeLine.EnScript#L2125)) | `TimeLineDialogClass` ([Win_TimeLine.EnScript:2144](../Win_TimeLine.EnScript#L2144)), `ChildEvent` ([Win_TimeLine.EnScript:2162](../Win_TimeLine.EnScript#L2162)), `Setup` ([Win_TimeLine.EnScript:2279](../Win_TimeLine.EnScript#L2279)), `TimerEvent` ([Win_TimeLine.EnScript:2289](../Win_TimeLine.EnScript#L2289)), `CanClose` ([Win_TimeLine.EnScript:2312](../Win_TimeLine.EnScript#L2312)) |

### Win_USBInfo.EnScript

886 lines; UTF-8 / ASCII.

| Class / declaration | Methods / locations |
| --- | --- |
| `USBRegListClass` ([Win_USBInfo.EnScript:4](../Win_USBInfo.EnScript#L4)) | `USBRegListClass` ([Win_USBInfo.EnScript:17](../Win_USBInfo.EnScript#L17)) |
| `USBEventLogListClass` ([Win_USBInfo.EnScript:31](../Win_USBInfo.EnScript#L31)) | `USBEventLogListClass` ([Win_USBInfo.EnScript:45](../Win_USBInfo.EnScript#L45)) |
| `USBWindowsHandlerClass` ([Win_USBInfo.EnScript:67](../Win_USBInfo.EnScript#L67)) | `USBWindowsHandlerClass` ([Win_USBInfo.EnScript:83](../Win_USBInfo.EnScript#L83)), `BuildMenu` ([Win_USBInfo.EnScript:109](../Win_USBInfo.EnScript#L109)), `MenuEvent` ([Win_USBInfo.EnScript:114](../Win_USBInfo.EnScript#L114)) |
| `USBEventLogHandlerClass` ([Win_USBInfo.EnScript:143](../Win_USBInfo.EnScript#L143)) | `USBEventLogHandlerClass` ([Win_USBInfo.EnScript:161](../Win_USBInfo.EnScript#L161)), `BuildMenu` ([Win_USBInfo.EnScript:193](../Win_USBInfo.EnScript#L193)), `MenuEvent` ([Win_USBInfo.EnScript:199](../Win_USBInfo.EnScript#L199)) |
| `ExportUSBWindowsDialogClass` ([Win_USBInfo.EnScript:257](../Win_USBInfo.EnScript#L257)) | `ExportUSBWindowsDialogClass` ([Win_USBInfo.EnScript:260](../Win_USBInfo.EnScript#L260)) |
| `USBWindowsThreadClass` ([Win_USBInfo.EnScript:265](../Win_USBInfo.EnScript#L265)) | `USBWindowsThreadClass` ([Win_USBInfo.EnScript:272](../Win_USBInfo.EnScript#L272)), `Run` ([Win_USBInfo.EnScript:279](../Win_USBInfo.EnScript#L279)), `Parse` ([Win_USBInfo.EnScript:479](../Win_USBInfo.EnScript#L479)), `DecodeHex` ([Win_USBInfo.EnScript:520](../Win_USBInfo.EnScript#L520)) |
| `USBEventLogThreadClass` ([Win_USBInfo.EnScript:535](../Win_USBInfo.EnScript#L535)) | `USBEventLogThreadClass` ([Win_USBInfo.EnScript:542](../Win_USBInfo.EnScript#L542)), `Run` ([Win_USBInfo.EnScript:549](../Win_USBInfo.EnScript#L549)), `BuildSqlite` ([Win_USBInfo.EnScript:697](../Win_USBInfo.EnScript#L697)) |
| `USBDialogClass` ([Win_USBInfo.EnScript:735](../Win_USBInfo.EnScript#L735)) | `USBDialogClass` ([Win_USBInfo.EnScript:775](../Win_USBInfo.EnScript#L775)), `ChildEvent` ([Win_USBInfo.EnScript:804](../Win_USBInfo.EnScript#L804)), `Setup` ([Win_USBInfo.EnScript:855](../Win_USBInfo.EnScript#L855)), `TimerEvent` ([Win_USBInfo.EnScript:860](../Win_USBInfo.EnScript#L860)), `CanClose` ([Win_USBInfo.EnScript:883](../Win_USBInfo.EnScript#L883)) |

### Win_UserAccount.EnScript

609 lines; UTF-16LE BOM.

| Class / declaration | Methods / locations |
| --- | --- |
| `AccountListClass` ([Win_UserAccount.EnScript:4](../Win_UserAccount.EnScript#L4)) | `AccountListClass` ([Win_UserAccount.EnScript:24](../Win_UserAccount.EnScript#L24)) |
| `AccountHandlerClass` ([Win_UserAccount.EnScript:51](../Win_UserAccount.EnScript#L51)) | `AccountHandlerClass` ([Win_UserAccount.EnScript:73](../Win_UserAccount.EnScript#L73)), `BuildMenu` ([Win_UserAccount.EnScript:115](../Win_UserAccount.EnScript#L115)), `MenuEvent` ([Win_UserAccount.EnScript:122](../Win_UserAccount.EnScript#L122)) |
| `ExportAccountDialogClass` ([Win_UserAccount.EnScript:187](../Win_UserAccount.EnScript#L187)) | `ExportAccountDialogClass` ([Win_UserAccount.EnScript:190](../Win_UserAccount.EnScript#L190)) |
| `AccountThreadClass` ([Win_UserAccount.EnScript:195](../Win_UserAccount.EnScript#L195)) | `AccountThreadClass` ([Win_UserAccount.EnScript:202](../Win_UserAccount.EnScript#L202)), `Run` ([Win_UserAccount.EnScript:209](../Win_UserAccount.EnScript#L209)) |
| `AccountDialogClass` ([Win_UserAccount.EnScript:482](../Win_UserAccount.EnScript#L482)) | `AccountDialogClass` ([Win_UserAccount.EnScript:518](../Win_UserAccount.EnScript#L518)), `ChildEvent` ([Win_UserAccount.EnScript:539](../Win_UserAccount.EnScript#L539)), `Setup` ([Win_UserAccount.EnScript:577](../Win_UserAccount.EnScript#L577)), `TimerEvent` ([Win_UserAccount.EnScript:582](../Win_UserAccount.EnScript#L582)), `CanClose` ([Win_UserAccount.EnScript:605](../Win_UserAccount.EnScript#L605)) |

### Win_WebDownloads.EnScript

910 lines; UTF-16LE BOM.

| Class / declaration | Methods / locations |
| --- | --- |
| `DownloadsListClass` ([Win_WebDownloads.EnScript:3](../Win_WebDownloads.EnScript#L3)) | `DownloadsListClass` ([Win_WebDownloads.EnScript:12](../Win_WebDownloads.EnScript#L12)) |
| `DownloadsHandlerClass` ([Win_WebDownloads.EnScript:28](../Win_WebDownloads.EnScript#L28)) | `DownloadsHandlerClass` ([Win_WebDownloads.EnScript:42](../Win_WebDownloads.EnScript#L42)), `BuildMenu` ([Win_WebDownloads.EnScript:65](../Win_WebDownloads.EnScript#L65)), `MenuEvent` ([Win_WebDownloads.EnScript:72](../Win_WebDownloads.EnScript#L72)) |
| `DownloadsThreadClass` ([Win_WebDownloads.EnScript:132](../Win_WebDownloads.EnScript#L132)) | `DownloadsThreadClass` ([Win_WebDownloads.EnScript:137](../Win_WebDownloads.EnScript#L137)), `_x2c` ([Win_WebDownloads.EnScript:151](../Win_WebDownloads.EnScript#L151)), `qURLdecode` ([Win_WebDownloads.EnScript:164](../Win_WebDownloads.EnScript#L164)), `sql2csv` ([Win_WebDownloads.EnScript:201](../Win_WebDownloads.EnScript#L201)), `download_csv` ([Win_WebDownloads.EnScript:461](../Win_WebDownloads.EnScript#L461)), `IE_timeformat` ([Win_WebDownloads.EnScript:515](../Win_WebDownloads.EnScript#L515)), `IE_WebCache_dat` ([Win_WebDownloads.EnScript:537](../Win_WebDownloads.EnScript#L537)), `export_file` ([Win_WebDownloads.EnScript:649](../Win_WebDownloads.EnScript#L649)), `Run` ([Win_WebDownloads.EnScript:716](../Win_WebDownloads.EnScript#L716)) |
| `DownloadsDialogClass` ([Win_WebDownloads.EnScript:802](../Win_WebDownloads.EnScript#L802)) | `DownloadsDialogClass` ([Win_WebDownloads.EnScript:818](../Win_WebDownloads.EnScript#L818)), `ChildEvent` ([Win_WebDownloads.EnScript:839](../Win_WebDownloads.EnScript#L839)), `Setup` ([Win_WebDownloads.EnScript:878](../Win_WebDownloads.EnScript#L878)), `TimerEvent` ([Win_WebDownloads.EnScript:883](../Win_WebDownloads.EnScript#L883)), `CanClose` ([Win_WebDownloads.EnScript:907](../Win_WebDownloads.EnScript#L907)) |

### Win_WebVisitKeyword.EnScript

1550 lines; UTF-16LE BOM.

| Class / declaration | Methods / locations |
| --- | --- |
| `WebListClass` ([Win_WebVisitKeyword.EnScript:5](../Win_WebVisitKeyword.EnScript#L5)) | `WebListClass` ([Win_WebVisitKeyword.EnScript:10](../Win_WebVisitKeyword.EnScript#L10)) |
| `KeywordListClass` ([Win_WebVisitKeyword.EnScript:20](../Win_WebVisitKeyword.EnScript#L20)) | `KeywordListClass` ([Win_WebVisitKeyword.EnScript:27](../Win_WebVisitKeyword.EnScript#L27)) |
| `WebHandlerClass` ([Win_WebVisitKeyword.EnScript:41](../Win_WebVisitKeyword.EnScript#L41)) | `WebHandlerClass` ([Win_WebVisitKeyword.EnScript:52](../Win_WebVisitKeyword.EnScript#L52)), `BuildMenu` ([Win_WebVisitKeyword.EnScript:67](../Win_WebVisitKeyword.EnScript#L67)), `MenuEvent` ([Win_WebVisitKeyword.EnScript:74](../Win_WebVisitKeyword.EnScript#L74)) |
| `KeywordHandlerClass` ([Win_WebVisitKeyword.EnScript:131](../Win_WebVisitKeyword.EnScript#L131)) | `KeywordHandlerClass` ([Win_WebVisitKeyword.EnScript:143](../Win_WebVisitKeyword.EnScript#L143)), `BuildMenu` ([Win_WebVisitKeyword.EnScript:162](../Win_WebVisitKeyword.EnScript#L162)), `MenuEvent` ([Win_WebVisitKeyword.EnScript:169](../Win_WebVisitKeyword.EnScript#L169)) |
| `WebThreadClass` ([Win_WebVisitKeyword.EnScript:230](../Win_WebVisitKeyword.EnScript#L230)) | `WebThreadClass` ([Win_WebVisitKeyword.EnScript:235](../Win_WebVisitKeyword.EnScript#L235)), `host_extract` ([Win_WebVisitKeyword.EnScript:248](../Win_WebVisitKeyword.EnScript#L248)), `Search_Keyword` ([Win_WebVisitKeyword.EnScript:277](../Win_WebVisitKeyword.EnScript#L277)), `_x2c` ([Win_WebVisitKeyword.EnScript:292](../Win_WebVisitKeyword.EnScript#L292)), `qURLdecode` ([Win_WebVisitKeyword.EnScript:305](../Win_WebVisitKeyword.EnScript#L305)), `sql2csv` ([Win_WebVisitKeyword.EnScript:343](../Win_WebVisitKeyword.EnScript#L343)), `keyword_extract` ([Win_WebVisitKeyword.EnScript:515](../Win_WebVisitKeyword.EnScript#L515)), `visit_csv` ([Win_WebVisitKeyword.EnScript:689](../Win_WebVisitKeyword.EnScript#L689)), `IE_timeformat` ([Win_WebVisitKeyword.EnScript:742](../Win_WebVisitKeyword.EnScript#L742)), `IE_search` ([Win_WebVisitKeyword.EnScript:764](../Win_WebVisitKeyword.EnScript#L764)), `IE_index_dat` ([Win_WebVisitKeyword.EnScript:788](../Win_WebVisitKeyword.EnScript#L788)), `IE_WebCache_dat` ([Win_WebVisitKeyword.EnScript:900](../Win_WebVisitKeyword.EnScript#L900)), `export_file` ([Win_WebVisitKeyword.EnScript:1041](../Win_WebVisitKeyword.EnScript#L1041)), `Run` ([Win_WebVisitKeyword.EnScript:1111](../Win_WebVisitKeyword.EnScript#L1111)) |
| `CreateWebChartClass` ([Win_WebVisitKeyword.EnScript:1207](../Win_WebVisitKeyword.EnScript#L1207)) | `CreateWebChartClass` ([Win_WebVisitKeyword.EnScript:1212](../Win_WebVisitKeyword.EnScript#L1212)), `GetChart` ([Win_WebVisitKeyword.EnScript:1217](../Win_WebVisitKeyword.EnScript#L1217)) |
| `WebDialogClass` ([Win_WebVisitKeyword.EnScript:1341](../Win_WebVisitKeyword.EnScript#L1341)) | `WebDialogClass` ([Win_WebVisitKeyword.EnScript:1367](../Win_WebVisitKeyword.EnScript#L1367)), `BuildChart` ([Win_WebVisitKeyword.EnScript:1407](../Win_WebVisitKeyword.EnScript#L1407)), `ShowChart` ([Win_WebVisitKeyword.EnScript:1413](../Win_WebVisitKeyword.EnScript#L1413)), `MapChartTypes` ([Win_WebVisitKeyword.EnScript:1441](../Win_WebVisitKeyword.EnScript#L1441)), `ChildEvent` ([Win_WebVisitKeyword.EnScript:1452](../Win_WebVisitKeyword.EnScript#L1452)), `Setup` ([Win_WebVisitKeyword.EnScript:1518](../Win_WebVisitKeyword.EnScript#L1518)), `TimerEvent` ([Win_WebVisitKeyword.EnScript:1523](../Win_WebVisitKeyword.EnScript#L1523)), `CanClose` ([Win_WebVisitKeyword.EnScript:1547](../Win_WebVisitKeyword.EnScript#L1547)) |

```sh
python3 tools/generate_source_reference.py --check
```
