// UI projection of compatibility/support.json; checked by tests.
export default {
  "updated_on": "2026-10-27",
  "schema": 15,
  "adapters": [
    {
      "id": "chromium",
      "implementation_maturity": "partial",
      "format_predicate": "SQLite urls/visits and supported downloads schemas; family detection by native tables, not filename.",
      "known_gaps": [
        "IE/WebCache, encrypted DBs and unreviewed required schemas.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "firefox",
      "implementation_maturity": "partial",
      "format_predicate": "SQLite moz_places/moz_historyvisits and named download annotations; missing event tables are explicit summaries.",
      "known_gaps": [
        "Every historical download, unsupported required schemas and encrypted DBs.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "lnk",
      "implementation_maturity": "partial",
      "format_predicate": "Shell Link header/CLSID and bounded selected blocks; explicit ANSI codepage.",
      "known_gaps": [
        "Target resolution/execution and unsupported blocks.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "prefetch",
      "implementation_maturity": "partial",
      "format_predicate": "SCCA 17/23/26/30/31 with admitted layout offsets; MAM04 XPRESS Huffman.",
      "known_gaps": [
        "Other MAM flags/layouts and device-to-drive inference.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "evtx",
      "implementation_maturity": "partial",
      "format_predicate": "Validated EVTX container/chunks/records and bounded decoder/XML; provider-qualified classifications.",
      "known_gaps": [
        "Carving, repair, message DLL loading and native Windows APIs.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "recycle_bin",
      "implementation_maturity": "partial",
      "format_predicate": "Explicit $I files with version 1/2 layouts, bounded UTF-16 path.",
      "known_gaps": [
        "Ownership, $R presence/restoration and shifted layout repair.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "usb_registry",
      "implementation_maturity": "partial",
      "format_predicate": "Selected SYSTEM/SOFTWARE keys using bounded clean REGF 1.3/1.4/1.5; Select/Current required.",
      "known_gaps": [
        "Log replay, deleted recovery, guessed drive/user joins.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "recent_docs",
      "implementation_maturity": "partial",
      "format_predicate": "RecentDocs in bounded clean REGF; strict MRUListEx ranks with raw tails.",
      "known_gaps": [
        "Shell Item target resolution and per-document open times.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "application_mru",
      "implementation_maturity": "partial",
      "format_predicate": "Selected Office/HWP/Adobe key/value profiles; sparse slots and literal metadata.",
      "known_gaps": [
        "Universal slot ranks, Adobe drive guesses and pinned-state inference.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "jump_lists",
      "implementation_maturity": "partial",
      "format_predicate": "CFB 3/4; DestList 1/3/4 and custom destinations 2; separate stream associations.",
      "known_gaps": [
        "Signature carving, missing associations and execution/owner inference.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "shellbags",
      "implementation_maturity": "partial",
      "format_predicate": "Selected BagMRU/Bags roots and bounded supported Shell Items/extensions.",
      "known_gaps": [
        "Missing ancestry, unsupported component normalization and folder-access claims.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "dialog_mru",
      "implementation_maturity": "partial",
      "format_predicate": "OpenSavePidlMRU/LastVisitedPidlMRU with strict controls and terminal PIDL requirement.",
      "known_gaps": [
        "Open/save success, target execution and identity joins.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "userassist",
      "implementation_maturity": "partial",
      "format_predicate": "Explicit Version 3/5, REG_BINARY 16/72 bytes; NoEncrypt-aware names.",
      "known_gaps": [
        "Size-based version guessing, corrected counts and focus-duration claims.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "run_mru",
      "implementation_maturity": "partial",
      "format_predicate": "RunMRU REG_SZ commands and strict MRUList, preserving tails.",
      "known_gaps": [
        "MRUListEx fallback, suffix trimming and command execution.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "explorer_history",
      "implementation_maturity": "partial",
      "format_predicate": "TypedPaths slots and WordWheelQuery strict MRUListEx as distinct observations.",
      "known_gaps": [
        "TypedPaths ranks, navigation success and identity attribution.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "system_info",
      "implementation_maturity": "partial",
      "format_predicate": "Selected SOFTWARE/SYSTEM observations with Select/Current and raw values/times.",
      "known_gaps": [
        "Product-key derivation, guessed identity and boot/uptime inference.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "sam_accounts",
      "implementation_maturity": "partial",
      "format_predicate": "Canonical SAM account keys; exact 80-byte F and selected strings from bounded V header.",
      "known_gaps": [
        "Credential extraction, full V payload, SID/groups/effective privilege inference.",
        "Actual acquired-version/build coverage remains unvalidated."
      ]
    },
    {
      "id": "macos_plist",
      "implementation_maturity": "planned",
      "format_predicate": "XML/binary plist selected system metadata",
      "known_gaps": [
        "No parser implemented; no compatibility claim."
      ]
    },
    {
      "id": "safari",
      "implementation_maturity": "planned",
      "format_predicate": "Selected Safari SQLite schemas",
      "known_gaps": [
        "No parser implemented; no compatibility claim."
      ]
    },
    {
      "id": "linux_metadata",
      "implementation_maturity": "planned",
      "format_predicate": "os-release and passwd/group metadata",
      "known_gaps": [
        "No parser implemented; no compatibility claim."
      ]
    },
    {
      "id": "linux_journal_export",
      "implementation_maturity": "planned",
      "format_predicate": "Acquired systemd journal export with duplicate/binary fields",
      "known_gaps": [
        "No parser implemented; no compatibility claim."
      ]
    }
  ],
  "hosts": [
    {
      "runner_label": "windows-2022",
      "os_family": "Windows",
      "python_minors": [
        "3.10",
        "3.14"
      ],
      "host_qualification": "tested"
    },
    {
      "runner_label": "macos-14",
      "os_family": "Darwin",
      "python_minors": [
        "3.10",
        "3.14"
      ],
      "host_qualification": "tested"
    },
    {
      "runner_label": "ubuntu-24.04",
      "os_family": "Linux",
      "python_minors": [
        "3.10",
        "3.14"
      ],
      "host_qualification": "tested"
    }
  ]
};
