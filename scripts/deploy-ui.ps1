<#
.SYNOPSIS
    VoltForge UI Fast Deployment Script (PowerShell)
.DESCRIPTION
    Builds the UI locally and deploys directly to the Azure VM via Python or SSH.
#>
param(
    [switch]$SkipBuild,
    [string]$HostIp = "4.154.189.115",
    [string]$User = "azureuser",
    [string]$Password = "VoltForge@2026!"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "deploy-ui.py"

$argsList = @()
if ($SkipBuild) {
    $argsList += "--skip-build"
}
$argsList += @("--host", $HostIp, "--user", $User, "--password", $Password)

python $pythonScript @argsList
