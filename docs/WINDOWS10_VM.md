# Windows 10 evaluation VM

**English** | [한국어](WINDOWS10_VM.ko.md)

2026-10-29 · Preparation record; Windows 10 browser qualification remains pending.

## Scope and observed state

An external QEMU x64 VM boots the genuine Microsoft Windows 10 Enterprise LTSC 2021 Evaluation installer on the macOS ARM64 host. Windows Setup has been observed in the local console. This is installation-media boot evidence, not an installed Windows client or a Chrome/Edge pass. No Windows license acceptance or guest bootstrap execution is recorded yet.

The VM uses QEMU 11.1.2, TCG emulation, 8 GiB RAM, four virtual CPUs and a sparse 64 GiB QCOW2 disk. User-mode NAT has no host forwarding; VNC and its console proxy bind only to loopback. There are no host shares or physical-disk attachments. Media, disks, payloads and results stay outside Git under the dedicated VM directory. Emulated execution does not establish native performance or support for all Windows 10 editions/builds.

## Media provenance

The [Microsoft installation ISO](https://software-static.download.prss.microsoft.com/db/download/444969d5-f34g-4e03-ac9d-1f9786c69161/19044.1288.211006-0501.21h2_release_svc_refresh_CLIENT_LTSC_EVAL_x64FRE_en-us.iso) is en-US x64, build 19044.1288. Its 4,898,582,528 bytes match the [official Microsoft hash publication](https://download.microsoft.com/download/9/3/b/93bfb33f-643f-43c9-a36f-cf3611c72187/Windows10Enterprise21H2HashValues.pdf):

`E4AB2E3535BE5748252A8D5D57539A6E59BE8D6726345EE10E7AFD2CB89FEFB5`

## Reproduction

1. Install QEMU from the official Homebrew formula and obtain the official evaluation media. Use [windows10_vm.py](../tools/windows10_vm.py) with `create --directory <external-directory> --iso <ISO>`. Existing VM files are refused; media hashes are checked before launch.
2. Obtain Python 3.14.8 amd64 from python.org and Node 22.23.4 win-x64 with its SHASUMS256.txt from nodejs.org. [prepare_windows10_payload.py](../tools/prepare_windows10_payload.py) builds a new external directory using `--directory`, `--python-installer`, `--node-archive` and `--node-shasums`. It exports committed HEAD with its exact commit ID; uncommitted source is excluded. Node is checked against the supplied official checksum list. Python Authenticode is checked inside the guest before installation.
3. Make that directory a read-only ISO with the host ISO tool. Run the VM helper with `run --directory <external-directory> --display cocoa --tools-iso <tools.iso>`. Alternatively use `--display vnc` (127.0.0.1:5907), a loopback websockify proxy and [the local console template](../tools/windows10_vm_console.html) with a local noVNC installation. The template expects `node_modules/@novnc/novnc/core/rfb.js` beside it; never expose the unauthenticated console publicly.
4. Complete Windows installation, reviewing the evaluation terms at the actual acceptance step. No unattended license acceptance, activation workaround or time manipulation is supplied.
5. After setup, run [windows10_guest_bootstrap.ps1](../tools/windows10_guest_bootstrap.ps1) from the tools CD inside the dedicated guest. It requires Windows client build 19041–21999 and QEMU manufacturer identification, refuses an existing test workspace, verifies payload hashes, installs isolated runtimes and genuine vendor browser channels, then runs the existing nine scenarios for each channel. This prepared bootstrap has not yet been executed on Windows.
6. Retain guest OS/machine attestation, exact browser versions, source commit, results and screenshots outside Git. Correct failures and rerun before updating the [vendor-browser qualification record](WORKBENCH_VENDOR_BROWSERS.md). The initial payload references `566c0e3b2c2f119638c0443d3e10213516bdc8f3`; rebuild it to test a later committed change.

## Remaining gate

Windows installation, evaluation-license confirmation, Chrome/Edge execution, failure repair and final host qualification remain outstanding. Local preparation checks must not be counted as Windows runtime validation. The [manual Windows 10 CI gate](../.github/workflows/windows10-browser.yml) still requires a matching registered self-hosted runner; this VM does not register one automatically.

## Local preparation validation

On 2026-10-29 the macOS/Python 3.14.8 environment passed all 500 Python tests with the EVTX extra, the strict suite gate with zero skips, 12 Node model tests, support inventory validation, Python helper syntax checks and archive-only integrity verification (13 sources and 263 reconstructed commits). The first sandboxed discovery failed because loopback socket binding was denied; the same suite passed after rerunning with the required host permission. Bilingual documentation structure was corrected after its initial checker failure. These results do not execute the guest bootstrap or certify Windows 10 browsers.
