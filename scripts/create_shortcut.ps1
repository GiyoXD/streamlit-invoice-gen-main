# Create Windows Shortcut for Invoice App
# This script creates a .lnk shortcut file

$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$PSScriptRoot\Run Invoice App.lnk")

# Set the target (batch file)
$Shortcut.TargetPath = "$PSScriptRoot\launch_app.bat"

# Set working directory
$Shortcut.WorkingDirectory = $PSScriptRoot

# Set icon (optional - uses cmd icon)
$Shortcut.IconLocation = "cmd.exe,0"

# Set description
$Shortcut.Description = "Launch Invoice Generation Streamlit App"

# Save the shortcut
$Shortcut.Save()

Write-Host "✅ Shortcut created: 'Run Invoice App.lnk'"
Write-Host "Double-click this shortcut to run the application."