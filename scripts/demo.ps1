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
    session_id      = "demo-smoke-$(Get-Date -Format 'yyyyMMddHHmmss')"
    message         = "Say hello in one short sentence."
    bot_name        = "Sakura"
    bot_personality = "tsundere guide"
    history         = @()
} | ConvertTo-Json -Compress -Depth 5

$streamOk = $false
if (Get-Command curl.exe -ErrorAction SilentlyContinue) {
    $bodyFile = New-TemporaryFile
    try {
        # PowerShell splits JSON strings passed to curl -d; write a file instead.
        [System.IO.File]::WriteAllText($bodyFile.FullName, $body)
        $streamOut = curl.exe -s -N -X POST "$BaseUrl/api/v1/completions" `
            -H "Content-Type: application/json" `
            --data-binary "@$($bodyFile.FullName)" `
            --max-time 60
        $streamText = ($streamOut -join "")
        if ($streamText -match '"detail"' -or $streamText -match 'json_invalid') {
            throw "Stream request failed: $($streamText.Substring(0, [Math]::Min(200, $streamText.Length)))"
        }
        if ([string]::IsNullOrWhiteSpace($streamText)) {
            throw "Stream response was empty."
        }
        $preview = $streamText.Substring(0, [Math]::Min(120, $streamText.Length))
        Write-Host "[demo] Stream preview: $preview..."
        $streamOk = $true
    } finally {
        Remove-Item $bodyFile -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "[demo] curl.exe not found — skipping stream test (health passed)."
    $streamOk = $true
}

if (-not $streamOk) {
    throw "Streaming completion check failed."
}

Write-Host "[demo] All checks passed."
