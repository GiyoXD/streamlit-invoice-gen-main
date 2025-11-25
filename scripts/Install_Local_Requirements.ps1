# Local Requirements Installer for Invoice Generation App
# This script installs the required Python packages locally on the user's PC
# Run this once on each computer that needs to access the shared Invoice app

param(
    [string]$SharedPath = "",
    [switch]$Force
)

Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "  Invoice App - Local Requirements Installer" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host

# Function to find the shared directory
function Find-SharedDirectory {
    param([string]$StartPath)

    # If path provided, use it
    if ($StartPath) {
        if (Test-Path $StartPath) {
            return $StartPath
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
            $requirementsFile = Join-Path $path "requirements.txt"
            if (Test-Path $requirementsFile) {
                Write-Host "✅ Found shared directory: $path" -ForegroundColor Green
                return $path
            }
        }
    }

    return $null
}

# Function to check Python installation
function Test-PythonInstallation {
    Write-Host "🔍 Checking Python installation..." -ForegroundColor Yellow

    # Try different Python commands
    $pythonCommands = @("python", "python3", "py")

    foreach ($cmd in $pythonCommands) {
        try {
            $version = & $cmd --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Python found: $version (using '$cmd')" -ForegroundColor Green

                # Check if pip is available
                $pipVersion = & $cmd -m pip --version 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✅ Pip found: $pipVersion" -ForegroundColor Green
                    return $cmd
                } else {
                    Write-Host "❌ Pip not found or not working with '$cmd'" -ForegroundColor Red
                }
            }
        } catch {
            # Continue to next command
        }
    }

    Write-Host "❌ Python not found. Please install Python 3.8+ from https://python.org" -ForegroundColor Red
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    return $null
}

# Function to install requirements
function Install-Requirements {
    param([string]$PythonCmd, [string]$RequirementsPath, [bool]$ForceInstall)

    Write-Host "📦 Installing requirements from: $RequirementsPath" -ForegroundColor Yellow
    Write-Host

    # Check if requirements file exists
    if (-not (Test-Path $RequirementsPath)) {
        Write-Host "❌ Requirements file not found: $RequirementsPath" -ForegroundColor Red
        return $false
    }

    # Show what will be installed
    Write-Host "📋 Requirements to install:" -ForegroundColor Cyan
    Get-Content $RequirementsPath | ForEach-Object {
        Write-Host "  - $_" -ForegroundColor Gray
    }
    Write-Host

    if (-not $ForceInstall) {
        $confirm = Read-Host "Continue with installation? (Y/n)"
        if ($confirm -eq "n" -or $confirm -eq "N") {
            Write-Host "Installation cancelled." -ForegroundColor Yellow
            return $false
        }
    }

    # Upgrade pip first
    Write-Host "⬆️  Upgrading pip..." -ForegroundColor Yellow
    try {
        $upgradeResult = & $PythonCmd -m pip install --upgrade pip --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Pip upgraded successfully" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Pip upgrade failed, continuing anyway..." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Pip upgrade failed, continuing anyway..." -ForegroundColor Yellow
    }

    # Install requirements
    Write-Host "📦 Installing packages..." -ForegroundColor Yellow
    try {
        $installResult = & $PythonCmd -m pip install -r $RequirementsPath --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ All requirements installed successfully!" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Installation failed" -ForegroundColor Red
            Write-Host "Error details:" -ForegroundColor Red
            Write-Host $installResult -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Installation failed with exception: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to verify installation
function Test-Installation {
    param([string]$PythonCmd)

    Write-Host "🔍 Verifying installation..." -ForegroundColor Yellow

    $packages = @("streamlit", "pandas", "openpyxl", "plotly")

    $allGood = $true
    foreach ($package in $packages) {
        try {
            $testResult = & $PythonCmd -c "import $package; print('$package OK')" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ $package - OK" -ForegroundColor Green
            } else {
                Write-Host "❌ $package - FAILED" -ForegroundColor Red
                $allGood = $false
            }
        } catch {
            Write-Host "❌ $package - FAILED" -ForegroundColor Red
            $allGood = $false
        }
    }

    return $allGood
}

# Main script
Write-Host "This script will install Python packages locally on your PC." -ForegroundColor White
Write-Host "These packages are required to run the Invoice Generation app." -ForegroundColor White
Write-Host

# Find shared directory
Write-Host "🔍 Finding shared directory..." -ForegroundColor Yellow
$sharedDir = Find-SharedDirectory -StartPath $SharedPath

if (-not $sharedDir) {
    Write-Host "❌ Could not find the shared Invoice Generation directory." -ForegroundColor Red
    Write-Host "Please ensure:" -ForegroundColor Yellow
    Write-Host "  1. You have access to the shared folder" -ForegroundColor Gray
    Write-Host "  2. Or specify the path using -SharedPath parameter" -ForegroundColor Gray
    Write-Host
    Write-Host "Example: .\Install_Local_Requirements.ps1 -SharedPath 'Z:\Path\To\Shared\Folder'" -ForegroundColor Cyan
    Start-Sleep -Seconds 10
    exit 1
}

$requirementsPath = Join-Path $sharedDir "requirements.txt"
Write-Host "📄 Requirements file: $requirementsPath" -ForegroundColor Green
Write-Host

# Check Python installation
$pythonCmd = Test-PythonInstallation
if (-not $pythonCmd) {
    Write-Host
    Write-Host "💡 Installation instructions:" -ForegroundColor Cyan
    Write-Host "  1. Download Python from: https://python.org/downloads/" -ForegroundColor White
    Write-Host "  2. Run the installer" -ForegroundColor White
    Write-Host "  3. IMPORTANT: Check 'Add Python to PATH'" -ForegroundColor Yellow
    Write-Host "  4. Restart PowerShell and run this script again" -ForegroundColor White
    Write-Host
    Start-Sleep -Seconds 10
    exit 1
}

Write-Host

# Install requirements
$installSuccess = Install-Requirements -PythonCmd $pythonCmd -RequirementsPath $requirementsPath -ForceInstall $Force

if ($installSuccess) {
    Write-Host
    Write-Host "🎉 Installation completed!" -ForegroundColor Green
    Write-Host

    # Verify installation
    $verifySuccess = Test-Installation -PythonCmd $pythonCmd

    if ($verifySuccess) {
        Write-Host
        Write-Host "✅ All packages verified successfully!" -ForegroundColor Green
        Write-Host
        Write-Host "🚀 You can now run the Invoice Generation app using:" -ForegroundColor Cyan
        Write-Host "   .\Run_Shared_App.ps1" -ForegroundColor White
        Write-Host "   or" -ForegroundColor White
        Write-Host "   .\launch_app.bat" -ForegroundColor White
        Write-Host
        Write-Host "The app will use the shared virtual environment but your local packages." -ForegroundColor Gray
    } else {
        Write-Host
        Write-Host "⚠️  Some packages may not be working correctly." -ForegroundColor Yellow
        Write-Host "Try running the app anyway, or reinstall with -Force parameter." -ForegroundColor Yellow
    }
} else {
    Write-Host
    Write-Host "❌ Installation failed." -ForegroundColor Red
    Write-Host "Please check the error messages above and try again." -ForegroundColor Yellow
    Write-Host
    Write-Host "💡 Troubleshooting:" -ForegroundColor Cyan
    Write-Host "  1. Make sure you have internet connection" -ForegroundColor White
    Write-Host "  2. Try running as Administrator" -ForegroundColor White
    Write-Host "  3. Check if antivirus is blocking the installation" -ForegroundColor White
    Write-Host "  4. Try: .\Install_Local_Requirements.ps1 -Force" -ForegroundColor White
    Write-Host
    Start-Sleep -Seconds 10
    exit 1
}

Write-Host
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")