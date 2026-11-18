#!/usr/bin/env bash
# api_demo.sh - walks through every REST endpoint with curl.
# Needs: both webservers running (Seller :10050, Buyer :10060), curl, python (for JSON pretty-print / parsing).
# Author: Suraj Patel (24BTRBT029)
set -u
SELLER=${SELLER_API:-http://localhost:10050}
BUYER=${BUYER_API:-http://localhost:10060}
SKEY=${SELLER_KEY:-seller-secret-key-123}
BKEY=${BUYER_KEY:-buyer-secret-key-456}
PY=${PYTHON:-python}
pretty() { "$PY" -m json.tool; }
step() { echo; echo "\$ $*"; }

step curl -s $SELLER/api/health
curl -s "$SELLER/api/health" | pretty

step curl -s -H "X-API-KEY: ***" $SELLER/api/me
curl -s -H "X-API-KEY: $SKEY" "$SELLER/api/me" | pretty

step curl -s -H "X-API-KEY: ***" $SELLER/api/peers
curl -s -H "X-API-KEY: $SKEY" "$SELLER/api/peers" | pretty

step curl -s -H "X-API-KEY: ***" $SELLER/api/notaries
curl -s -H "X-API-KEY: $SKEY" "$SELLER/api/notaries" | pretty

NO="INV-CURL-$(date +%H%M%S)"
step curl -s -X POST $SELLER/api/invoices -d '{"invoiceNo":"'$NO'",...}'
RESP=$(curl -s -X POST "$SELLER/api/invoices" -H "X-API-KEY: $SKEY" -H "Content-Type: application/json" \
  -d '{"invoiceNo":"'"$NO"'","buyer":"O=BuyerCorp,L=Bengaluru,C=IN","amount":75000,"currency":"INR","description":"curl demo invoice","dueDate":"2026-12-31"}')
echo "$RESP" | pretty
ID=$(echo "$RESP" | "$PY" -c "import sys,json;print(json.load(sys.stdin)['data']['linearId'])")

step curl -s -H "X-API-KEY: ***" $BUYER/api/invoices/$ID
curl -s -H "X-API-KEY: $BKEY" "$BUYER/api/invoices/$ID" | pretty

step curl -s -X PUT $BUYER/api/invoices/$ID/approve -d '{"remarks":"Approved via curl"}'
curl -s -X PUT "$BUYER/api/invoices/$ID/approve" -H "X-API-KEY: $BKEY" -H "Content-Type: application/json" \
  -d '{"remarks":"Approved via curl"}' | pretty

step curl -s -X PUT $BUYER/api/invoices/$ID/pay -d '{"remarks":"UTR-CURL-001"}'
curl -s -X PUT "$BUYER/api/invoices/$ID/pay" -H "X-API-KEY: $BKEY" -H "Content-Type: application/json" \
  -d '{"remarks":"UTR-CURL-001"}' | pretty

step curl -s -H "X-API-KEY: ***" "$SELLER/api/invoices?status=PAID"
curl -s -H "X-API-KEY: $SKEY" "$SELLER/api/invoices?status=PAID" | pretty

step curl -s -H "X-API-KEY: ***" $SELLER/api/invoices/$ID/history
curl -s -H "X-API-KEY: $SKEY" "$SELLER/api/invoices/$ID/history" | pretty

echo; echo "---------------- error cases ----------------"
step curl -s -H "X-API-KEY: wrong" $SELLER/api/invoices   "(expect 401)"
curl -s -w "\nHTTP %{http_code}\n" -H "X-API-KEY: wrong" "$SELLER/api/invoices"

step curl -s -X POST $SELLER/api/invoices -d '{"amount":0,...}'   "(expect 400)"
curl -s -w "\nHTTP %{http_code}\n" -X POST "$SELLER/api/invoices" -H "X-API-KEY: $SKEY" -H "Content-Type: application/json" \
  -d '{"invoiceNo":"BAD-1","buyer":"BuyerCorp","amount":0,"currency":"inr","dueDate":"2026-12-31"}'

step curl -s -X PUT $BUYER/api/invoices/$ID/approve   "(already PAID, expect 422)"
curl -s -w "\nHTTP %{http_code}\n" -X PUT "$BUYER/api/invoices/$ID/approve" -H "X-API-KEY: $BKEY"

step curl -s $BUYER/api/invoices/00000000-0000-0000-0000-000000000000   "(expect 404)"
curl -s -w "\nHTTP %{http_code}\n" -H "X-API-KEY: $BKEY" "$BUYER/api/invoices/00000000-0000-0000-0000-000000000000"
