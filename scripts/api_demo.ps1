# api_demo.ps1 - the same walk-through as api_demo.sh for Windows PowerShell 5.1+.
# Needs both webservers running (Seller :10050, Buyer :10060).
# Author: Suraj Patel (24BTRBT029)
$Seller = if ($env:SELLER_API) { $env:SELLER_API } else { "http://localhost:10050" }
$Buyer  = if ($env:BUYER_API)  { $env:BUYER_API }  else { "http://localhost:10060" }
$SH = @{ "X-API-KEY" = "seller-secret-key-123" }
$BH = @{ "X-API-KEY" = "buyer-secret-key-456" }

function Show($title, $obj) { Write-Host "`n> $title" -ForegroundColor Cyan; $obj | ConvertTo-Json -Depth 8 }
function Try-Call($title, [scriptblock]$call) {
    Write-Host "`n> $title" -ForegroundColor Yellow
    try { & $call | ConvertTo-Json -Depth 8 }
    catch {
        $code = [int]$_.Exception.Response.StatusCode
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        Write-Host "HTTP $code"; $reader.ReadToEnd()
    }
}

Show "GET /api/health" (Invoke-RestMethod "$Seller/api/health")
Show "GET /api/me (seller)" (Invoke-RestMethod "$Seller/api/me" -Headers $SH)
Show "GET /api/peers" (Invoke-RestMethod "$Seller/api/peers" -Headers $SH)

$no = "INV-PS-" + (Get-Date -Format HHmmss)
$body = @{ invoiceNo = $no; buyer = "O=BuyerCorp,L=Bengaluru,C=IN"; amount = 64000; currency = "INR";
           description = "PowerShell demo invoice"; dueDate = "2026-12-31" } | ConvertTo-Json
$issued = Invoke-RestMethod "$Seller/api/invoices" -Method Post -Headers $SH -ContentType "application/json" -Body $body
Show "POST /api/invoices" $issued
$id = $issued.data.linearId

Show "PUT approve (buyer)" (Invoke-RestMethod "$Buyer/api/invoices/$id/approve" -Method Put -Headers $BH -ContentType "application/json" -Body '{"remarks":"OK from PowerShell"}')
Show "PUT pay (buyer)" (Invoke-RestMethod "$Buyer/api/invoices/$id/pay" -Method Put -Headers $BH -ContentType "application/json" -Body '{"remarks":"UTR-PS-1"}')
Show "GET history (seller)" (Invoke-RestMethod "$Seller/api/invoices/$id/history" -Headers $SH)

Try-Call "Wrong API key (expect 401)" { Invoke-RestMethod "$Seller/api/invoices" -Headers @{ "X-API-KEY" = "wrong" } }
Try-Call "Invalid amount (expect 400)" { Invoke-RestMethod "$Seller/api/invoices" -Method Post -Headers $SH -ContentType "application/json" -Body '{"invoiceNo":"BAD","buyer":"BuyerCorp","amount":-1,"currency":"INR","dueDate":"2026-12-31"}' }
Try-Call "Approve a PAID invoice (expect 422)" { Invoke-RestMethod "$Buyer/api/invoices/$id/approve" -Method Put -Headers $BH }
