#!/usr/bin/env pwsh
# Windows counterpart of run_blender.sh. Keeps batch caches/config inside the
# project and runs headless with factory startup. Set BLENDER_BIN to override
# the detected Blender executable.
$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
if (-not $env:BLENDER_BIN) { $env:BLENDER_BIN = 'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe' }
if (-not (Test-Path $env:BLENDER_BIN)) {
    $found = Get-Command blender -ErrorAction SilentlyContinue
    if ($found) { $env:BLENDER_BIN = $found.Source } else { throw "Blender not found. Set BLENDER_BIN." }
}
New-Item -ItemType Directory -Force -Path "$ProjectDir/.runtime/config" | Out-Null
New-Item -ItemType Directory -Force -Path "$ProjectDir/.runtime/cache" | Out-Null
$env:BLENDER_USER_CONFIG = "$ProjectDir/.runtime/config"
$env:XDG_CACHE_HOME = "$ProjectDir/.runtime/cache"
& $env:BLENDER_BIN -noaudio -b --factory-startup --python-exit-code 1 @args
exit $LASTEXITCODE
