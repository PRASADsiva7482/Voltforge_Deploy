<#
.SYNOPSIS
    VoltForge Unified Azure Deployment Tool (PowerShell)
.DESCRIPTION
    Deploy UI, Backend (BL), AI Engine, or Configurations with simple switches.
.EXAMPLE
    .\azureDeploy\scripts\deploy.ps1 -UI
    .\azureDeploy\scripts\deploy.ps1 -BL
    .\azureDeploy\scripts\deploy.ps1 -AI
    .\azureDeploy\scripts\deploy.ps1 -Config
    .\azureDeploy\scripts\deploy.ps1 -All
    .\azureDeploy\scripts\deploy.ps1 -Status
#>
param(
    [switch]$UI,
    [switch]$SkipBuild,
    [switch]$BL,
    [switch]$AI,
    [switch]$Config,
    [switch]$All,
    [switch]$Status,
    [string]$HostIp = "4.154.189.115",
    [string]$User = "azureuser",
    [string]$Password = "VoltForge@2026!"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "deploy.py"

$argsList = @()
if ($UI) { $argsList += "--ui" }
if ($SkipBuild) { $argsList += "--skip-build" }
if ($BL) { $argsList += "--bl" }
if ($AI) { $argsList += "--ai" }
if ($Config) { $argsList += "--config" }
if ($All) { $argsList += "--all" }
if ($Status) { $argsList += "--status" }

$argsList += @("--host", $HostIp, "--user", $User, "--password", $Password)

python $pythonScript @argsList
