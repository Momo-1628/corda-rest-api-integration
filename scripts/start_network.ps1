# start_network.ps1 - starts Notary, SellerCorp and BuyerCorp headless, waits for "started up",
# then starts the Seller (10050) and Buyer (10060) REST APIs and waits for /api/health = UP.
# Prerequisite: .\gradlew.bat deployNodes :webserver:writeLaunchArgs
#
# -NodesDir lets the nodes run from another drive. Artemis (the broker inside every node) blocks all
# messaging when the disk holding the node folder is more than 90 % full, so on a nearly full C: drive
# use for example:  .\scripts\start_network.ps1 -NodesDir D:\corda-rest-api-run\nodes
#
# Author: Suraj Patel (24BTRBT029)
param([int]$NodeHeapMb = 512, [int]$ApiHeapMb = 384, [int]$TimeoutSec = 300, [string]$NodesDir = "")
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$srcNodes = Join-Path $root "build\nodes"
$activeNodes = $srcNodes
$runDir = Join-Path $root "build\run"

if ($NodesDir -ne "") {
    # fresh copy of the deployed nodes every time = clean ledger for each run
    if (Test-Path $NodesDir) { Remove-Item -Recurse -Force $NodesDir }
    New-Item -ItemType Directory -Force $NodesDir | Out-Null
    Copy-Item -Recurse -Force (Join-Path $srcNodes "*") $NodesDir
    $activeNodes = $NodesDir
}
New-Item -ItemType Directory -Force $runDir | Out-Null
Set-Content -Path (Join-Path $runDir "nodes_dir.txt") -Value $activeNodes

function Wait-For([scriptblock]$cond, [string]$what) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while (-not (& $cond)) {
        if ($sw.Elapsed.TotalSeconds -gt $TimeoutSec) { throw "Timed out waiting for $what" }
        Start-Sleep -Seconds 2
    }
    Write-Host ("  {0} ready after {1:N0} s" -f $what, $sw.Elapsed.TotalSeconds)
}

foreach ($n in "Notary", "SellerCorp", "BuyerCorp") {
    $dir = Join-Path $activeNodes $n
    $log = Join-Path $runDir "$n.out.log"
    Remove-Item $log, "$log.err" -ErrorAction SilentlyContinue
    $p = Start-Process -FilePath "java" -ArgumentList "-Xmx${NodeHeapMb}m", "-jar", "corda.jar", "--no-local-shell" `
        -WorkingDirectory $dir -RedirectStandardOutput $log -RedirectStandardError "$log.err" -WindowStyle Hidden -PassThru
    Set-Content -Path (Join-Path $runDir "$n.pid") -Value $p.Id
    Write-Host "Started $n (pid $($p.Id)) in $dir"
}
foreach ($n in "Notary", "SellerCorp", "BuyerCorp") {
    $log = Join-Path $runDir "$n.out.log"
    Wait-For { (Test-Path $log) -and (Select-String -Path $log -Pattern "started up" -Quiet) } "$n node"
}

$argsFile = Join-Path $root "clients\webserver\build\webserver.args"
foreach ($api in @(@{ name = "seller"; port = 10050 }, @{ name = "buyer"; port = 10060 })) {
    $log = Join-Path $runDir "api-$($api.name).out.log"
    Remove-Item $log, "$log.err" -ErrorAction SilentlyContinue
    $p = Start-Process -FilePath "java" -ArgumentList "-Xmx${ApiHeapMb}m", "@$argsFile", "com.cordarest.webserver.Starter", "--spring.profiles.active=$($api.name)" `
        -WorkingDirectory $root -RedirectStandardOutput $log -RedirectStandardError "$log.err" -WindowStyle Hidden -PassThru
    Set-Content -Path (Join-Path $runDir "api-$($api.name).pid") -Value $p.Id
    Write-Host "Started $($api.name) API (pid $($p.Id)) on port $($api.port)"
}
foreach ($port in 10050, 10060) {
    Wait-For { try { (Invoke-RestMethod "http://localhost:$port/api/health" -TimeoutSec 3).data.status -eq "UP" } catch { $false } } "API :$port"
}
Write-Host "Network and APIs are up. Swagger UI: http://localhost:10050/swagger-ui.html"
