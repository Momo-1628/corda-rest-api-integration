# stop_network.ps1 - stops the two REST APIs first, then the three Corda nodes (PIDs saved in build\run).
# Author: Suraj Patel (24BTRBT029)
$root = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $root "build\run"
foreach ($n in "api-seller", "api-buyer", "BuyerCorp", "SellerCorp", "Notary") {
    $pidFile = Join-Path $runDir "$n.pid"
    if (-not (Test-Path $pidFile)) { continue }
    $procId = [int](Get-Content $pidFile)
    $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
    if ($proc) {
        # polite taskkill first, then force the whole tree (Corda 4.12 re-launches itself as a child JVM)
        cmd /c "taskkill /PID $procId /T >nul 2>&1"
        if (-not $proc.WaitForExit(8000)) { cmd /c "taskkill /PID $procId /T /F >nul 2>&1" }
        Write-Host "Stopped $n (pid $procId)"
    }
    Remove-Item $pidFile -ErrorAction SilentlyContinue
}
