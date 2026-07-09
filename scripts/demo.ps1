# Nebula API smoke test — run from repo root with backend up.
# Usage: .\scripts\demo.ps1 [-BaseUrl http://127.0.0.1:8000]

param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

Write-Host "[demo] Health check: $BaseUrl/health"
$health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
if ($health.status -ne "ok") {
    throw "Health check failed: $($health | ConvertTo-Json -Compress)"
}
Write-Host "[demo] Health OK"

Write-Host "[demo] Streaming completion (first chunks)..."
$body = @{
    session_id = "demo-smoke-$(Get-Date -Format 'yyyyMMddHHmmss')"
    message    = "Say hello in one short sentence."
    bot_name   = "Sakura"
    bot_personality = "tsundere guide"
    history    = @()
} | ConvertTo-Json

# curl -N streams raw bytes; Invoke-WebRequest buffers unless we read the stream.
# Use curl.exe if available for true streaming preview.
if (Get-Command curl.exe -ErrorAction SilentlyContinue) {
    $tmp = New-TemporaryFile
    try {
        curl.exe -s -N -X POST "$BaseUrl/api/v1/completions" `
            -H "Content-Type: application/json" `
            -d $body `
            --max-time 60 | Tee-Object -Variable streamOut | Out-Null
        $preview = ($streamOut -join "").Substring(0, [Math]::Min(120, ($streamOut -join "").Length))
        Write-Host "[demo] Stream preview: $preview..."
    } finally {
        Remove-Item $tmp -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "[demo] curl.exe not found — skipping stream test (health passed)."
}

Write-Host "[demo] All checks passed."
