param(
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [Parameter(Mandatory = $true)][string]$Minisign
)

# Explicit acceptance preparation only. Never reads production signing secrets.
# Invoke serially in the same resource slot as the following native tests.
$ErrorActionPreference = 'Stop'
if (-not [System.IO.Path]::IsPathRooted($OutputDirectory)) { throw 'OutputDirectory must be absolute' }
$nativeFixtureOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $nativeFixtureOutput) { throw 'Use a fresh output directory for each acceptance preparation' }
$nativeFixtureSigner = (Resolve-Path -LiteralPath $Minisign).Path
$nativeFixtureCompiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
if (-not (Test-Path -LiteralPath $nativeFixtureCompiler)) { throw 'Windows .NET Framework C# compiler is required' }
[System.IO.Directory]::CreateDirectory($nativeFixtureOutput) | Out-Null
$nativeFixtureSuccessor = Join-Path $nativeFixtureOutput 'RytmUpdaterAcceptanceSuccessor.exe'
$nativeFixtureInstaller = Join-Path $nativeFixtureOutput 'RytmUpdaterAcceptanceInstaller.exe'
$nativeFixtureCommon = @('/nologo', '/target:winexe', '/platform:x64', '/optimize+', '/reference:System.Web.Extensions.dll',
    ('/win32manifest:"{0}"' -f (Join-Path $PSScriptRoot 'as-invoker.manifest')))
# Framework csc has legacy command-line parsing. Response files keep the quotes
# around each switch value/source path intact across PowerShell native invocation.
# Every switch must precede every source: a later /out starts another assembly.
$nativeFixtureSuccessorArgs = $nativeFixtureCommon + @(
    ('/out:"{0}"' -f $nativeFixtureSuccessor),
    ('"{0}"' -f (Join-Path $PSScriptRoot 'AcceptancePaths.cs')),
    ('"{0}"' -f (Join-Path $PSScriptRoot 'AcceptanceSuccessor.cs')))
$nativeFixtureInstallerArgs = $nativeFixtureCommon + @(
    ('/out:"{0}"' -f $nativeFixtureInstaller),
    ('/resource:"{0}",Acceptance.Successor' -f $nativeFixtureSuccessor),
    ('"{0}"' -f (Join-Path $PSScriptRoot 'AcceptancePaths.cs')),
    ('"{0}"' -f (Join-Path $PSScriptRoot 'AcceptanceInstaller.cs')))
$nativeFixtureEncoding = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllLines((Join-Path $nativeFixtureOutput 'successor.rsp'), $nativeFixtureSuccessorArgs, $nativeFixtureEncoding)
[System.IO.File]::WriteAllLines((Join-Path $nativeFixtureOutput 'installer.rsp'), $nativeFixtureInstallerArgs, $nativeFixtureEncoding)
Push-Location -LiteralPath $nativeFixtureOutput
try {
    & $nativeFixtureCompiler '@successor.rsp'
    if ($LASTEXITCODE -ne 0) { throw 'Acceptance successor compilation failed' }
    & $nativeFixtureCompiler '@installer.rsp'
    if ($LASTEXITCODE -ne 0) { throw 'Acceptance installer compilation failed' }
}
finally { Pop-Location }
$nativeFixturePublic = Join-Path $nativeFixtureOutput 'ephemeral.pub'
$nativeFixtureSecret = Join-Path $nativeFixtureOutput 'ephemeral.key'
$nativeFixtureSignature = Join-Path $nativeFixtureOutput 'installer.minisig'
& $nativeFixtureSigner -G -W -p $nativeFixturePublic -s $nativeFixtureSecret | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Acceptance key generation failed' }
& $nativeFixtureSigner -S -s $nativeFixtureSecret -m $nativeFixtureInstaller -x $nativeFixtureSignature -t 'inert Windows acceptance fixture' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Acceptance signature creation failed' }
& $nativeFixtureSigner -V -p $nativeFixturePublic -m $nativeFixtureInstaller -x $nativeFixtureSignature -q
if ($LASTEXITCODE -ne 0) { throw 'Acceptance signature verification failed' }
$nativeFixtureSources = @{}
foreach ($nativeFixtureName in @('AcceptancePaths.cs', 'AcceptanceInstaller.cs', 'AcceptanceSuccessor.cs', 'as-invoker.manifest')) {
    $nativeFixtureSources[$nativeFixtureName] = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $nativeFixtureName) -Algorithm SHA256).Hash.ToLowerInvariant()
}
$nativeFixtureManifest = @{
    installer = [System.IO.Path]::GetFileName($nativeFixtureInstaller)
    installer_sha256 = (Get-FileHash -LiteralPath $nativeFixtureInstaller -Algorithm SHA256).Hash.ToLowerInvariant()
    successor_sha256 = (Get-FileHash -LiteralPath $nativeFixtureSuccessor -Algorithm SHA256).Hash.ToLowerInvariant()
    public_key = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($nativeFixturePublic))
    signature = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($nativeFixtureSignature))
    source_sha256 = $nativeFixtureSources
}
$nativeFixtureManifestPath = Join-Path $nativeFixtureOutput 'handoff-inputs.json'
[System.IO.File]::WriteAllText($nativeFixtureManifestPath, ($nativeFixtureManifest | ConvertTo-Json -Depth 5) + "`n", [System.Text.UTF8Encoding]::new($false))
Write-Output "Acceptance inputs: $nativeFixtureManifestPath"
