# Compatibility and version policy

**English** | [한국어](CROSS_PLATFORM_COMPATIBILITY.ko.md)

2026-10-27 · Proposed extension design, not an implementation or compatibility certification. Current package 0.15.0 / report schema 15 remains unchanged.

## Meaning of every version

The goal is extensible coverage of historical, current and future evidence formats. Universal execution on every OS release cannot be guaranteed: runtimes, CPU architectures, security restrictions and undocumented layouts differ. Older evidence can be analyzed on a supported modern host without installing Plaintrace on the original OS. An unrecognized future revision must never inherit a tested label automatically.

Record compatibility as a tuple: host OS/build + CPU + Python + optional dependencies + input family/revision + output schema + test evidence. Vendor lifecycle support and Plaintrace validation are separate dimensions.

## Host execution targets

| Host family | First validation target | Additional track | Current evidence |
| --- | --- | --- | --- |
| Windows | Windows 11 x86-64, explicit build | Windows 10/Server and ARM64 as separately tested lanes | Unvalidated in repository records |
| macOS | macOS 14+ ARM64, each selected release | Intel and older macOS as separate runners | macOS/Python 3.14 recorded; no blanket version/CPU certification |
| Linux | Ubuntu 24.04 LTS x86-64, pinned image | Debian/Fedora, ARM64 and musl separately | Unvalidated in repository records |
| Legacy hosts | No universal native-runtime promise | Analyze exported evidence on a modern host | Per-format qualification required |

These are proposed test targets, not claims about vendor support or completed tests. Retain the current Python 3.10+ declaration until a separate compatibility decision. Exercise the minimum and each claimed interpreter minor; never keep an obsolete interpreter solely to run on legacy evidence systems. Wheel/native dependency availability must be verified per architecture.

## Evidence coverage map

| Evidence family | Existing or proposed format coverage | Version discovery rule |
| --- | --- | --- |
| Windows NT family, client/server | Existing bounded REGF/LNK/Prefetch/EVTX/CFB and selected metadata; legacy EVT/IE and new layouts deferred | Header/revision/schema gates; Windows version is contextual only |
| Windows 9x/DOS-era data | Separate future adapters, not REGF/EVTX fallback | Admit only individually specified formats |
| Mac OS X / OS X / macOS | Proposed XML/binary plist, system metadata, selected Safari SQLite | Container signature, schema and independently acquired build provenance |
| Classic Mac OS | Research backlog; not covered by macOS plist promise | Separate filesystem/artifact investigation |
| Linux distributions | Proposed os-release, passwd/group metadata, journal export, selected text logs | Distribution configuration, producer version, format capabilities |
| Non-systemd Linux | Text logs and supported application artifacts | Do not require journald or invent missing boot IDs |
| Cross-OS browsers | Existing Chromium/Firefox schema-based parsing; Safari proposed | Application schema, not host or filename |
| Future/unknown releases | Raw provenance and explicit unsupported diagnostics | New fixtures and review before promotion |

No finite sample certifies every patch, distribution or configuration. Publish tested builds, artifact producer revisions and explicit exclusions. Browser application versions can change independently of the evidence OS.

## Support lifecycle and registry

Maintain three separate fields: implementation maturity (planned, implemented, partial, unsupported), host qualification (unvalidated, tested, regressed), and evidence qualification (synthetic, acquired, independently compared). A passing synthetic suite cannot set acquired qualification. A format may be implemented while a host remains unvalidated.

A future machine-readable support registry must contain adapter ID/version, exact format predicates, tested host tuple, fixture digest/license, expected-result digest, test command/date/result, known gaps and reviewer. Initially transcribe only existing records; unknown values remain unknown. A release may claim tested support only when all mandatory lanes pass without unexpected skips and documented exclusions remain visible. Regression removes the affected claim until repaired; a new OS release starts unvalidated.

## External constraints and sources

Consulted 2026-10-27. Python distribution/runtime requirements vary; consult [CPython Windows documentation](https://docs.python.org/3/using/windows.html) before fixing packaging targets. This motivates separating legacy evidence from host runtime support.

The [Microsoft Shell Link specification](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-shllink/16cb4ca1-9339-4d0c-a68d-bf1d6cc0f943) publishes revisions, motivating format-specific gates. [systemd journal export](https://systemd.io/JOURNAL_EXPORT_FORMATS/) supports repeated and binary fields; preserving ordered values is a design requirement. Apple's [file access guidance](https://developer.apple.com/documentation/security/accessing-files-from-the-macos-app-sandbox) describes user-granted Full Disk Access; the proposed offline core must not assume it can acquire protected host data. These sources support design constraints, not Plaintrace validation.

## M0 implementation follow-up

On 2026-10-27 the M0 inventory, verification tooling and CI were implemented. See [implementation contracts](M0_BASELINE.md) and [actual results and remaining gates](M0_TESTS.md). M0 is not fully accepted, and universal OS-version support is not claimed, without results from the named hosted runners.
