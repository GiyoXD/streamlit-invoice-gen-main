# Streamlit Quick Launcher (No Terminal Interaction)
# This launcher starts Streamlit in a separate window to avoid hanging issues

param(
    [string]$SharedPath = "",
    [int]$Port = 8501
)

Write-Host "🚀 Quick Streamlit Launcher" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan
Write-Host

# Function to find the shared directory
function Find-SharedDirectory {
    param([string]$StartPath)

    if ($StartPath) {
        if (Test-Path $StartPath) {
            $appPy = Join-Path $StartPath "app.py"
            if (Test-Path $appPy) {
                return $StartPath
            }
        }
    }

    $possiblePaths = @(
        "\\Glfnas005\共享文件夹\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB",
        "Z:\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB",
        "$PSScriptRoot",
        "$PSScriptRoot\.."
    )

    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $appPy = Join-Path $path "app.py"
            if (Test-Path $appPy) {
                return $path
            }
        }
    }

    return $null
}

# Find shared directory
$appDirectory = Find-SharedDirectory -StartPath $SharedPath
if (-not $appDirectory) {
    Write-Host "❌ Could not find application directory" -ForegroundColor Red
    Start-Sleep -Seconds 5
    exit 1
}

$appPyPath = Join-Path $appDirectory "app.py"
Write-Host "📂 Found app at: $appDirectory" -ForegroundColor Green

# Ensure absolute path
$appPyPath = [System.IO.Path]::GetFullPath($appPyPath)

# Find Python
$pythonCmd = $null
$pythonCommands = @("python", "python3", "py")

foreach ($cmd in $pythonCommands) {
    try {
        & $cmd -c "import streamlit" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonCmd) {
    Write-Host "❌ Python with streamlit not found" -ForegroundColor Red
    Start-Sleep -Seconds 5
    exit 1
}

Write-Host "✅ Using Python: $pythonCmd" -ForegroundColor Green

# Start Streamlit in a new window (no interaction needed)
Write-Host "🚀 Starting Streamlit in new window..." -ForegroundColor Green
Write-Host "Application will be available at: http://localhost:$Port" -ForegroundColor White
Write-Host
Write-Host "Close the new Streamlit window to stop the application." -ForegroundColor Yellow

# Start in new window with minimal parameters
$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = $pythonCmd
$startInfo.Arguments = "-u -m streamlit run `"$appPyPath`" --server.port $Port --server.headless true --server.runOnSave false --logger.level error"
$startInfo.UseShellExecute = $true
$startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Normal

$process = [System.Diagnostics.Process]::Start($startInfo)

if ($process) {
    Write-Host "✅ Streamlit started successfully!" -ForegroundColor Green
    Write-Host
    Write-Host "Press any key to exit this launcher (Streamlit will keep running)..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
} else {
    Write-Host "❌ Failed to start Streamlit" -ForegroundColor Red
    Start-Sleep -Seconds 5
}