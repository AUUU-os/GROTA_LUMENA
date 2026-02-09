param(
  [Parameter(Mandatory=True)][string],
  [string] = "E:\\SHAD\\GROTA_LUMENA",
  [switch],
  [string] = "E:\\SHAD\\GROTA_LUMENA\\INBOX"
)

Continue = "Stop"

# Run Codex non-interactively against the repo
 = @("codex", "-C", , "exec", )
 = & [0] [1] [2] [3] [4] 2>&1

if () {
  if (-not (Test-Path -LiteralPath )) {
    New-Item -ItemType Directory -Path  | Out-Null
  }
   = Get-Date -Format "yyyyMMdd_HHmmss"
   = Join-Path  "CODEX_RESULT_.md"
   = "# CODEX RESULT\n\n## TASK\n\n\n## OUTPUT\n\n```text\n\n```\n"
  Set-Content -LiteralPath  -Value  -Encoding UTF8
  Write-Host "Saved output to "
}


