# Invoice Generation App Launcher (PowerShell)
# This script can handle UNC paths and network shares

param(
    [string]$NetworkPath = ""
)

# If no network path provided, use current directory
if (-not $NetworkPath) {
    $NetworkPath = $PSScriptRoot
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Invoice Generation App Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Target path: $NetworkPath" -ForegroundColor Gray
Write-Host

# Change to the target directory
Set-Location $NetworkPath

# Check if running from network path
if ($NetworkPath.StartsWith("\\")) {
    Write-Host "🌐 Network path detected: $NetworkPath" -ForegroundColor Yellow

    # Try to map the network drive
    $driveLetter = "Z:"
    Write-Host "Mapping network drive $driveLetter to $NetworkPath..." -ForegroundColor Yellow

    try {
        # Remove existing mapping if it exists
        if (Test-Path $driveLetter) {
            net use $driveLetter /delete /y 2>$null | Out-Null
        }

        # Map the drive
        net use $driveLetter $NetworkPath /persistent:no | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Network drive mapped successfully: $driveLetter" -ForegroundColor Green

            # Change to the mapped drive
            Set-Location $driveLetter

            Write-Host "📂 Changed to directory: $(Get-Location)" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to map network drive" -ForegroundColor Red
            Write-Host "Please map the drive manually and try again:" -ForegroundColor Yellow
            Write-Host "net use Z: `"$NetworkPath`"" -ForegroundColor Cyan
            Start-Sleep -Seconds 5  # Give user time to see the message
            exit 1
        }
    } catch {
        Write-Host "❌ Error mapping network drive: $($_.Exception.Message)" -ForegroundColor Red
        Start-Sleep -Seconds 5  # Give user time to see the message
        exit 1
    }
} else {
    Write-Host "📂 Using local path: $NetworkPath" -ForegroundColor Green
    Set-Location $NetworkPath
}

# Check if virtual environment exists
$venvPath = Join-Path (Get-Location) "venv\Scripts\activate.bat"
if (-not (Test-Path $venvPath)) {
    Write-Host "❌ Virtual environment not found at: $venvPath" -ForegroundColor Red
    Write-Host "Please make sure you're running this from the correct directory" -ForegroundColor Yellow
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    Start-Sleep -Seconds 5  # Give user time to see the message
    exit 1
}

Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& $venvPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    Start-Sleep -Seconds 5  # Give user time to see the message
    exit 1
}

Write-Host "✅ Virtual environment activated" -ForegroundColor Green
Write-Host

Write-Host "🚀 Starting Streamlit application..." -ForegroundColor Green
Write-Host "Access the app at: http://localhost:8501" -ForegroundColor Cyan
Write-Host "Close this window to stop the application" -ForegroundColor Yellow
Write-Host

try {
    streamlit run app.py
} catch {
    Write-Host "❌ Error starting Streamlit: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Write-Host
    Write-Host "🛑 Application stopped." -ForegroundColor Yellow

    # Clean up network drive mapping if we created one
    if ($NetworkPath.StartsWith("\\")) {
        Write-Host "🧹 Cleaning up network drive mapping..." -ForegroundColor Yellow
        net use $driveLetter /delete /y 2>$null | Out-Null
        Write-Host "✅ Network drive unmapped" -ForegroundColor Green
    }

    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}