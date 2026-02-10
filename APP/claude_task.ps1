param(
  [Parameter(Mandatory=True)][string],
  [string] = "E:\\SHAD\\GROTA_LUMENA",
  [switch],
  [string] = "E:\\SHAD\\GROTA_LUMENA\\INBOX"
)

Continue = "Stop"
Set-Location -LiteralPath 

# Run Claude Code non-interactively (one-shot)
 = & claude -p  2>&1

if () {
  if (-not (Test-Path -LiteralPath )) {
    New-Item -ItemType Directory -Path  | Out-Null
  }
   = Get-Date -Format "yyyyMMdd_HHmmss"
   = Join-Path  "CLAUDE_RESULT_.md"
   = "# CLAUDE RESULT\n\n## TASK\n\n\n## OUTPUT\n\n```text\n\n```\n"
  Set-Content -LiteralPath  -Value  -Encoding UTF8
  Write-Host "Saved output to "
}


