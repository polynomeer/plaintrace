# Run only inside the dedicated QEMU Windows 10 evaluation guest after user setup.
$ErrorActionPreference = 'Stop'
$client = Get-CimInstance Win32_OperatingSystem
$machine = Get-CimInstance Win32_ComputerSystem
if ($client.ProductType -ne 1 -or [int]$client.BuildNumber -lt 19041 -or [int]$client.BuildNumber -ge 22000) { throw 'Windows 10 client build 19041-21999 is required' }
if ($machine.Manufacturer -notmatch 'QEMU') { throw 'This bootstrap is restricted to the dedicated QEMU guest' }
$root = 'C:\Plaintrace-VM-Test'
$results = 'C:\Plaintrace-VM-Results'
if (Test-Path $root) { throw 'Existing test workspace will not be replaced; inspect it before continuing' }
New-Item -ItemType Directory -Path $root, $results | Out-Null
$client | Select-Object Caption, Version, BuildNumber, ProductType, OSArchitecture | ConvertTo-Json | Set-Content -Encoding utf8 "$results\windows-client.json"
$machine | Select-Object Manufacturer, Model, TotalPhysicalMemory | ConvertTo-Json | Set-Content -Encoding utf8 "$results\guest-machine.json"
$metadata = Get-Content "$PSScriptRoot\payload.json" -Raw | ConvertFrom-Json
function Assert-Hash($file, $expected) {
    if ((Get-FileHash $file -Algorithm SHA256).Hash -ne $expected) { throw "Payload hash mismatch: $file" }
}
foreach ($item in $metadata.files) { Assert-Hash "$PSScriptRoot\$($item.name)" $item.sha256 }
$pythonInstaller = "$PSScriptRoot\python-3.14.8-amd64.exe"
$signature = Get-AuthenticodeSignature $pythonInstaller
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Python Software Foundation') { throw 'Python vendor signature is not valid' }
$pythonHome = "$root\Python"
$installed = Start-Process $pythonInstaller -ArgumentList '/quiet', 'InstallAllUsers=0', 'Include_pip=1', 'Include_test=0', 'PrependPath=0', "TargetDir=$pythonHome" -Wait -PassThru
if ($installed.ExitCode -ne 0) { throw "Python installation failed: $($installed.ExitCode)" }
Expand-Archive "$PSScriptRoot\node-v22.23.4-win-x64.zip" "$root\Node"
Expand-Archive "$PSScriptRoot\plaintrace.zip" "$root\Source"
$env:PATH = "$pythonHome;$pythonHome\Scripts;$root\Node\node-v22.23.4-win-x64;$env:PATH"
& "$pythonHome\python.exe" -m venv "$root\venv"
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed' }
$env:PATH = "$root\venv\Scripts;$env:PATH"
Set-Location "$root\Source"
python -m pip install .
if ($LASTEXITCODE -ne 0) { throw 'Package install failed' }
npm ci
if ($LASTEXITCODE -ne 0) { throw 'Test dependency install failed' }
# These named vendor channels install genuine Chrome/Edge; no Chromium relabeling.
npx playwright install chrome msedge
if ($LASTEXITCODE -ne 0) { throw 'Vendor browser installation failed' }
$env:GITHUB_SHA = $metadata.source_commit
foreach ($channel in @('chrome', 'msedge')) {
    $env:PLAINTRACE_BROWSER_RESULTS = "$results\$channel"
    npm run test:browser -- "--project=$channel"
    if ($LASTEXITCODE -ne 0) { throw "Browser verification failed: $channel" }
}
Write-Host "Browser results: $results"
Write-Host 'Guest tests have finished. Retain result JSON, screenshots and client attestation before claiming validation.'
