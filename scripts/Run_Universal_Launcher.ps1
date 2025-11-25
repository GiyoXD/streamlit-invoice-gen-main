# Universal Invoice Generation App Launcher
# This script runs the Invoice app using local Python packages
# Works on any PC that has run Install_Local_Requirements.ps1

param(
    [string]$SharedPath = "",
    [switch]$NoBrowser,
    [int]$Port = 8501
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Universal Invoice Generation Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host

# Function to find the shared directory
function Find-SharedDirectory {
    param([string]$StartPath)

    # If path provided, use it
    if ($StartPath) {
        if (Test-Path $StartPath) {
            $appPy = Join-Path $StartPath "app.py"
            if (Test-Path $appPy) {
                return $StartPath
            }
        }
    }

    # Look for the shared directory in common locations
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
                Write-Host "✅ Found shared directory: $path" -ForegroundColor Green
                return $path
            }
        }
    }

    return $null
}

# Function to find Python executable
function Find-PythonExecutable {
    Write-Host "🔍 Finding Python executable..." -ForegroundColor Yellow

    # Try different Python commands
    $pythonCommands = @("python", "python3", "py")

    foreach ($cmd in $pythonCommands) {
        try {
            $version = & $cmd --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Python found: $version (using '$cmd')" -ForegroundColor Green

                # Test if streamlit is available
                $streamlitTest = & $cmd -c "import streamlit; print('Streamlit OK')" 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✅ Streamlit package found" -ForegroundColor Green
                    return $cmd
                } else {
                    Write-Host "⚠️  Streamlit not found with '$cmd', trying next..." -ForegroundColor Yellow
                }
            }
        } catch {
            # Continue to next command
        }
    }

    return $null
}

# Function to check if all required packages are installed
function Test-RequiredPackages {
    param([string]$PythonCmd)

    Write-Host "🔍 Checking required packages..." -ForegroundColor Yellow

    $requiredPackages = @("streamlit", "pandas", "openpyxl", "plotly")
    $missingPackages = @()

    foreach ($package in $requiredPackages) {
        try {
            $testResult = & $PythonCmd -c "import $package" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ $package - OK" -ForegroundColor Green
            } else {
                Write-Host "❌ $package - MISSING" -ForegroundColor Red
                $missingPackages += $package
            }
        } catch {
            Write-Host "❌ $package - MISSING" -ForegroundColor Red
            $missingPackages += $package
        }
    }

    if ($missingPackages.Count -gt 0) {
        Write-Host
        Write-Host "❌ Missing required packages: $($missingPackages -join ', ')" -ForegroundColor Red
        Write-Host "Please run: .\Install_Local_Requirements.ps1" -ForegroundColor Yellow
        return $false
    }

    Write-Host "✅ All required packages found" -ForegroundColor Green
    return $true
}

# Function to setup network drive if needed
function Setup-NetworkDrive {
    param([string]$AppDirectory)

    $isNetworkPath = $AppDirectory.StartsWith("\\") -or $AppDirectory.StartsWith("Z:")

    if ($isNetworkPath) {
        Write-Host "🌐 Network path detected. Setting up drive mapping..." -ForegroundColor Yellow

        $driveLetter = "Z:"
        $uncPath = "\\Glfnas005\共享文件夹\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB"

        try {
            # Check if Z: is already mapped to the correct location
            $currentMapping = net use $driveLetter 2>$null | Where-Object { $_ -match "\\\\Glfnas005\\共享文件夹\\营销团队\\software to use\\GENERATE_INVOICE_STREAMLIT_WEB" }
            if ($currentMapping) {
                Write-Host "✅ Z: drive already mapped correctly" -ForegroundColor Green
                return $AppDirectory.Replace($uncPath, $driveLetter)
            } else {
                # Remove existing mapping if it exists
                if (Test-Path $driveLetter) {
                    Write-Host "🔄 Remapping Z: drive..." -ForegroundColor Yellow
                    net use $driveLetter /delete /y 2>$null | Out-Null
                }

                # Map to the correct UNC path
                if (Test-Path $uncPath) {
                    net use $driveLetter $uncPath /persistent:no | Out-Null
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "✅ Network drive mapped: $driveLetter" -ForegroundColor Green
                        return $AppDirectory.Replace($uncPath, $driveLetter)
                    }
                }
            }
        } catch {
            Write-Host "⚠️  Drive mapping failed, using original path..." -ForegroundColor Yellow
        }
    }

    return $AppDirectory
}

# Main script
Write-Host "This launcher uses your local Python installation with packages." -ForegroundColor White
Write-Host "Make sure you've run Install_Local_Requirements.ps1 first." -ForegroundColor White
Write-Host

# Find shared directory
Write-Host "🔍 Finding shared directory..." -ForegroundColor Yellow
$appDirectory = Find-SharedDirectory -StartPath $SharedPath

if (-not $appDirectory) {
    Write-Host "❌ Could not find the shared Invoice Generation directory." -ForegroundColor Red
    Write-Host "Please ensure:" -ForegroundColor Yellow
    Write-Host "  1. You have access to the shared folder" -ForegroundColor Gray
    Write-Host "  2. Or specify the path using -SharedPath parameter" -ForegroundColor Gray
    Write-Host
    Write-Host "Example: .\Run_Universal_Launcher.ps1 -SharedPath 'Z:\Path\To\Shared\Folder'" -ForegroundColor Cyan
    Start-Sleep -Seconds 10
    exit 1
}

Write-Host "📂 Application directory: $appDirectory" -ForegroundColor Green

# Setup network drive if needed
$appDirectory = Setup-NetworkDrive -AppDirectory $appDirectory
Write-Host "📂 Using directory: $appDirectory" -ForegroundColor Green
Write-Host

# Find Python executable
$pythonCmd = Find-PythonExecutable
if (-not $pythonCmd) {
    Write-Host "❌ Python not found or streamlit not installed." -ForegroundColor Red
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "  1. Install Python 3.8+ from https://python.org" -ForegroundColor Gray
    Write-Host "  2. Run: .\Install_Local_Requirements.ps1" -ForegroundColor Gray
    Write-Host "  3. Make sure Python is in your PATH" -ForegroundColor Gray
    Start-Sleep -Seconds 10
    exit 1
}

# Check required packages
if (-not (Test-RequiredPackages -PythonCmd $pythonCmd)) {
    Write-Host
    Write-Host "💡 To install missing packages, run:" -ForegroundColor Cyan
    Write-Host "   .\Install_Local_Requirements.ps1" -ForegroundColor White
    Start-Sleep -Seconds 10
    exit 1
}

# Check if app.py exists
$appPyPath = Join-Path $appDirectory "app.py"
if (-not (Test-Path $appPyPath)) {
    Write-Host "❌ app.py not found in: $appDirectory" -ForegroundColor Red
    Start-Sleep -Seconds 5
    exit 1
}

# Ensure absolute path
$appPyPath = [System.IO.Path]::GetFullPath($appPyPath)

Write-Host
Write-Host "🚀 Starting Invoice Generation Application..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Application will be available at:" -ForegroundColor Cyan
Write-Host "http://localhost:$Port" -ForegroundColor White
Write-Host
Write-Host "Press Ctrl+C in this window to stop the application" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host

# Build streamlit arguments
$streamlitArgs = @("run", $appPyPath, "--server.port", $Port.ToString(), "--server.headless", "true", "--server.runOnSave", "false", "--logger.level", "info")

if ($NoBrowser) {
    $streamlitArgs += @("--server.headless", "true")
}

# Start the application
try {
    Write-Host "🔧 Starting Streamlit with command:" -ForegroundColor Gray
    Write-Host "  $pythonCmd -u -m streamlit $($streamlitArgs -join ' ')" -ForegroundColor Gray
    Write-Host

    # Use -u flag for unbuffered output to prevent hanging
    & $pythonCmd -u -m streamlit $streamlitArgs
} catch {
    Write-Host "❌ Error starting application: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Write-Host
    Write-Host "🛑 Application stopped." -ForegroundColor Yellow
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}