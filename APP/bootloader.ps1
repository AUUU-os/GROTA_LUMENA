param(
  [string]$root = "E:\\SHAD\\GROTA_LUMENA",
  [string]$checkpoint = "E:\\SHAD\\GROTA_LUMENA\\INBOX\\STATE_CHECKPOINT.md",
  [string[]]$apiPorts = @("8800","8000","3000"),
  [switch]$autoStart
)

$line = "=" * 72
$logo = @'
  ________  ________  ________  _________  ________     
 /  _____/ /  _____/ /  _____/ /   _____/ /  _____/     
/   \  ___/   \  ___/   \  ___/ \_____  \/   \  ___     
\    \_\  \    \_\  \    \_\  \ /        \    \_\  \    
 \______  /\______  /\______  //_______  /\______  /    
        \/        \/        \/         \/        \/     
'@

$now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$snapshot = if (Test-Path -LiteralPath $checkpoint) { (Get-Item $checkpoint).LastWriteTime.ToString("yyyy-MM-dd") } else { "n/a" }
$modules = "MEMORY:OK  RAG:OK  EXPORT:OK  BACKUP:OK  METRICS:OK"
$swarm = "OFFLINE (Ollama down)"
$accent = "NEON // FULL"

$badgeOk = "[OK]"
$badgeWarn = "[WARN]"
$badgeCrit = "[CRIT]"

$inbox = Join-Path $root "INBOX"
$latestReport = Get-ChildItem -LiteralPath $inbox -Filter "REPORT_*.md" -File -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1
$reportLine = if ($latestReport) { "$($latestReport.Name) @ $($latestReport.LastWriteTime.ToString("yyyy-MM-dd HH:mm"))" } else { "n/a" }
$reportBadge = if ($latestReport) { "$badgeOk" } else { "$badgeWarn" }

$agentRoot = Join-Path $root "M-AI-SELF"
$agentCount = if (Test-Path -LiteralPath $agentRoot) { (Get-ChildItem -LiteralPath $agentRoot -Directory -ErrorAction SilentlyContinue | Measure-Object).Count } else { 0 }
$agentBadge = if ($agentCount -gt 0) { "$badgeOk" } else { "$badgeWarn" }
$agentLine = "$agentBadge Agents:$agentCount"

$memoryDb = Join-Path $root "CORE\\corex\\memory.db"
$memDbStatus = if (Test-Path -LiteralPath $memoryDb) { "MEMDB:OK" } else { "MEMDB:MISS" }
if ($memDbStatus -eq "MEMDB:OK") { $memDbStatus = "$badgeOk $memDbStatus" } else { $memDbStatus = "$badgeCrit $memDbStatus" }

function Get-ApiStatus {
  param([string]$Base)
  try {
    $health = Invoke-RestMethod -Uri "$Base/api/v1/health" -TimeoutSec 1 -ErrorAction Stop
    $metrics = Invoke-RestMethod -Uri "$Base/api/v1/memory/metrics" -TimeoutSec 1 -ErrorAction Stop
    $report = Invoke-RestMethod -Uri "$Base/api/v1/reports/latest" -TimeoutSec 1 -ErrorAction Stop
    $memCount = if ($metrics -and $metrics.total_entries) { $metrics.total_entries } else { "n/a" }
    $reportName = if ($report -and $report.report) { $report.report } else { "n/a" }
    return @{
      status = "API:OK  MEM_ENTRIES:$memCount"
      report = $reportName
    }
  } catch {
    return @{
      status = "API:OFFLINE"
      report = "n/a"
    }
  }
}

$apiStatus = "API:OFFLINE"
$apiReport = "n/a"
$apiBase = "n/a"
foreach ($p in $apiPorts) {
  $base = "http://localhost:$p"
  $res = Get-ApiStatus -Base $base
  if ($res.status -like "API:OK*") {
    $apiStatus = $res.status
    $apiReport = $res.report
    $apiBase = $base
    break
  }
}
if ($apiStatus -like "API:OK*") { $apiStatus = "$badgeOk $apiStatus" } else { $apiStatus = "$badgeWarn $apiStatus" }
if ($apiReport -ne "n/a") { $apiReport = "$badgeOk $apiReport" } else { $apiReport = "$badgeWarn n/a" }

$pythonCmd = (Get-Command python -ErrorAction SilentlyContinue).Source
$npmCmd = (Get-Command npm -ErrorAction SilentlyContinue).Source
$pythonLine = if ($pythonCmd) { "$badgeOk $pythonCmd" } else { "$badgeWarn python (missing)" }
$npmLine = if ($npmCmd) { "$badgeOk $npmCmd" } else { "$badgeWarn npm (missing)" }

$ollamaUp = $false
try {
  $ollamaUp = (Test-NetConnection -ComputerName "127.0.0.1" -Port 11434 -WarningAction SilentlyContinue).TcpTestSucceeded
} catch {
  $ollamaUp = $false
}
$ollamaLine = if ($ollamaUp) { "OLLAMA:UP" } else { "OLLAMA:DOWN" }
if ($ollamaUp) { $ollamaLine = "$badgeOk $ollamaLine" } else { $ollamaLine = "$badgeWarn $ollamaLine" }

$portMap = @{
  "8800" = "API"
  "8000" = "API-ALT"
  "3000" = "UI"
  "11434" = "OLLAMA"
}
$portList = $portMap.Keys
$openPorts = @()
foreach ($p in $portList) {
  try {
    if ((Test-NetConnection -ComputerName "127.0.0.1" -Port $p -WarningAction SilentlyContinue).TcpTestSucceeded) {
      $openPorts += "$p=$($portMap[$p])"
    }
  } catch { }
}
$portsLine = if ($openPorts.Count -gt 0) { "$badgeOk " + ($openPorts -join ",") } else { "$badgeWarn none" }

$healthSummary = @()
if ($apiStatus -like "*API:OK*") { $healthSummary += "API" }
if ($ollamaUp) { $healthSummary += "OLLAMA" }
if ($memDbStatus -like "*MEMDB:OK*") { $healthSummary += "MEMDB" }
$healthLine = if ($healthSummary.Count -gt 0) { "$badgeOk " + ($healthSummary -join "+") } else { "$badgeWarn degraded" }

if ($autoStart -and $apiStatus -eq "API:OFFLINE" -and $pythonCmd) {
  Start-Process -FilePath "powershell" -WindowStyle Minimized -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command `"`"$pythonCmd`" `"$root\\CORE\\corex\\api_server.py`"`""
  Start-Sleep -Milliseconds 500
  foreach ($p in $apiPorts) {
    $base = "http://localhost:$p"
    $res = Get-ApiStatus -Base $base
    if ($res.status -like "API:OK*") {
      $apiStatus = $res.status
      $apiReport = $res.report
      $apiBase = $base
      break
    }
  }
}

$exclude = @("CORE","APP","INBOX","M-AI-SELF","DASHBOARD","CONFIG","DATABASE","KEYS","MANIFESTS","TEMP","scripts","checkpoints",".git",".claude",".mcp.json","AGENTS.md")
$projects = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
  Where-Object { $exclude -notcontains $_.Name } |
  Where-Object {
    (Test-Path -LiteralPath (Join-Path $_.FullName "README.md")) -or
    (Test-Path -LiteralPath (Join-Path $_.FullName "AGENTS.md"))
  } |
  Select-Object -ExpandProperty Name
$projectsLine = if ($projects -and $projects.Count -gt 0) { ($projects -join ", ") } else { "n/a" }
$projectsBadge = if ($projectsLine -ne "n/a") { "$badgeOk" } else { "$badgeWarn" }

$modulesBadge = "$badgeOk"
$swarmBadge = if ($swarm -like "OFFLINE*") { "$badgeWarn" } else { "$badgeOk" }

$alerts = @()
if ($swarm -like "OFFLINE*") { $alerts += "WARN: SWARM OFFLINE (Ollama)" }
if ($memDbStatus -eq "MEMDB:MISS") { $alerts += "CRIT: MEMORY DB MISSING" }
if (-not $latestReport) { $alerts += "WARN: NO HEALTH REPORT" }
if ($alerts.Count -eq 0) { $alerts = @("ALERT: NONE") }

$card = @(
  "CARD   : GROTA_LUMENA",
  "ROLE   : Local AI Core + Memory Vault + Swarm Hub",
  "FOCUS  : End-to-End agents, dashboards, and self-audit"
)

$quickOps = @(
  "OPS    : start api    -> python CORE\\corex\\api_server.py",
  "OPS    : start daemon -> python CORE\\corex\\daemon.py",
  "OPS    : open ui      -> npm run dev:ui",
  "OPS    : bootloader   -> powershell -File APP\\bootloader.ps1"
)

$sysCard = Get-ChildItem -LiteralPath $inbox -Filter "SYSTEM_CARD_*.md" -File -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1
$sysCardLine = if ($sysCard) { "$($sysCard.Name) @ $($sysCard.LastWriteTime.ToString("yyyy-MM-dd HH:mm"))" } else { "n/a" }

$memDbSize = if (Test-Path -LiteralPath $memoryDb) { ("{0:N2} MB" -f ((Get-Item $memoryDb).Length / 1MB)) } else { "0 MB" }
$backupDir = Join-Path $root "CORE\\corex\\memory_backups"
$backupCount = if (Test-Path -LiteralPath $backupDir) { (Get-ChildItem -LiteralPath $backupDir -Filter "*.db" -File -ErrorAction SilentlyContinue | Measure-Object).Count } else { 0 }
$storageLine = "MEMDB:$memDbSize  BACKUPS:$backupCount"

Write-Host $logo -ForegroundColor Cyan
Write-Host $line -ForegroundColor DarkCyan
Write-Host " GROTA_LUMENA :: BOOTLOADER" -ForegroundColor White
Write-Host " MODE    : $accent" -ForegroundColor Magenta
Write-Host " STATUS  : ONLINE | Resonance: 963 Hz | $now" -ForegroundColor Gray
Write-Host " SNAPSHOT: $snapshot" -ForegroundColor Gray
Write-Host " REPORT  : $reportBadge $reportLine" -ForegroundColor Gray
Write-Host $line -ForegroundColor DarkCyan
Write-Host " CORE    : FastAPI | Daemon | Swarm | Memory (SQL+Chroma)" -ForegroundColor White
Write-Host " UI      : DASHBOARD (Memory Vault + Reports)" -ForegroundColor White
Write-Host " MIND    : M-AI-SELF (Agents + Protocols)" -ForegroundColor White
Write-Host " MODULES : $modulesBadge $modules" -ForegroundColor White
Write-Host " STORAGE : $memDbStatus" -ForegroundColor White
Write-Host " STORAGE+: $storageLine" -ForegroundColor White
Write-Host " STATUS  : $apiStatus" -ForegroundColor White
Write-Host " API     : $apiBase" -ForegroundColor White
Write-Host " APIREP  : $apiReport" -ForegroundColor White
Write-Host " TOOLS   : $pythonLine" -ForegroundColor White
Write-Host " TOOLS+  : $npmLine" -ForegroundColor White
Write-Host " HEALTH  : $ollamaLine" -ForegroundColor White
Write-Host " PORTS   : $portsLine" -ForegroundColor White
Write-Host " HEALTH+ : $healthLine" -ForegroundColor White
Write-Host " AGENTS  : $agentLine" -ForegroundColor White
Write-Host " SWARM   : $swarmBadge $swarm" -ForegroundColor Yellow
Write-Host " PROJECTS: GROTA_LUMENA (active)" -ForegroundColor White
Write-Host " PROJECTS+: $projectsBadge $projectsLine" -ForegroundColor White
Write-Host " LOG     : GROTA_LOG.md (write-trace enabled)" -ForegroundColor White
Write-Host $line -ForegroundColor DarkCyan
foreach ($a in $alerts) {
  $color = if ($a -like "CRIT:*") { "Red" } elseif ($a -like "WARN:*") { "Yellow" } else { "DarkGray" }
  Write-Host " $a" -ForegroundColor $color
}
Write-Host " SYS-CARD: $sysCardLine" -ForegroundColor Cyan
foreach ($c in $card) { Write-Host " $c" -ForegroundColor Cyan }
foreach ($o in $quickOps) { Write-Host " $o" -ForegroundColor DarkCyan }
Write-Host $line -ForegroundColor DarkCyan
Write-Host " AUUUUUUUUUUUUUUU" -ForegroundColor Magenta
