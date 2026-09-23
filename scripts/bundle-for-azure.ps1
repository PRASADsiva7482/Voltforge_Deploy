# =============================================================================
# VoltForge — Package Clean Bundle for Azure Deployment
# Creates a minimal archive excluding node_modules, target, toolchains, training runs, and git
# =============================================================================
param(
    [string]$OutputPath = "d:\Project\voltforge\azureDeploy\voltforge-azure-bundle.zip"
)

$ErrorActionPreference = "Stop"
$rootDir = "d:\Project\voltforge"
$tempDir = Join-Path $env:TEMP "voltforge-bundle-$(Get-Random)"

Write-Host "[*] Creating clean package for Azure deployment..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

try {
    # 1. Copy azureDeploy
    Write-Host "  -> Packing azureDeploy..."
    $azureDeployDest = "$tempDir\azureDeploy"
    New-Item -ItemType Directory -Path $azureDeployDest -Force | Out-Null
    Get-ChildItem -Path "$rootDir\azureDeploy" | Where-Object { $_.Name -notmatch '\.zip$' } | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $azureDeployDest -Recurse -Force
    }

    # 2. Copy Voltforge_UI (exclude node_modules, dist, .git)
    Write-Host "  -> Packing Voltforge_UI..."
    $uiDest = "$tempDir\Voltforge_UI"
    New-Item -ItemType Directory -Path $uiDest -Force | Out-Null
    Get-ChildItem -Path "$rootDir\Voltforge_UI" | Where-Object { $_.Name -notin @('node_modules', 'dist', '.git') } | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $uiDest -Recurse -Force
    }

    # 3. Copy Voltforge_BL (exclude target, .git)
    Write-Host "  -> Packing Voltforge_BL..."
    $blDest = "$tempDir\Voltforge_BL"
    New-Item -ItemType Directory -Path $blDest -Force | Out-Null
    Get-ChildItem -Path "$rootDir\Voltforge_BL" | Where-Object { $_.Name -notin @('target', '.git') } | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $blDest -Recurse -Force
    }

    # 4. Copy Voltforge_AI (only runtime directories and files matching Dockerfile)
    Write-Host "  -> Packing Voltforge_AI..."
    $aiDest = "$tempDir\Voltforge_AI"
    New-Item -ItemType Directory -Path $aiDest -Force | Out-Null
    
    $aiRuntimeItems = @(
        'api', 'api_contract', 'engine', 'context_compiler',
        'data_governance', 'electronics_corpus', 'engineering_tools',
        'evaluation', 'feedback_governance', 'grounding', 'memory_store',
        'internet_retrieval', 'local_retrieval', 'task_schema', 'tests',
        'circuit_verifier.py', 'web_search_engine.py', 'observability.py',
        'config.py', 'main.py', 'app.py', 'dataset.txt', 'requirements.txt',
        'Dockerfile'
    )
    
    foreach ($item in $aiRuntimeItems) {
        $sourcePath = Join-Path "$rootDir\Voltforge_AI" $item
        if (Test-Path $sourcePath) {
            Copy-Item -Path $sourcePath -Destination $aiDest -Recurse -Force
        }
    }

    # 5. Compress to zip
    if (Test-Path $OutputPath) {
        Remove-Item -Path $OutputPath -Force
    }
    Write-Host "[*] Compressing to $OutputPath..." -ForegroundColor Cyan
    Compress-Archive -Path "$tempDir\*" -DestinationPath $OutputPath -CompressionLevel Fastest

    $sizeMb = [Math]::Round((Get-Item $OutputPath).Length / 1MB, 2)
    Write-Host "[+] Clean package created successfully: $OutputPath ($sizeMb MB)" -ForegroundColor Green
}
finally {
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}
