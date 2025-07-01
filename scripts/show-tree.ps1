function Show-Tree($path, $level = 0, $maxLevel = 2) {
    if ($level -gt $maxLevel) { return }
    Get-ChildItem $path | Where-Object { 
        -not ($_.Name.StartsWith('.') -or $_.Name -eq '__pycache__') 
    } | ForEach-Object {
        Write-Host ("  " * $level) + "+-- " + $_.Name
        if ($_.PSIsContainer) {
            Show-Tree $_.FullName ($level + 1) $maxLevel
        }
    }
}

# If you get a policy error, run the following command in PowerShell to allow script execution:
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
Show-Tree . 0 2
