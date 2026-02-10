param(
  [string] = "E:\\SHAD\\GROTA_LUMENA",
  [string] = "E:\\SHAD\\GROTA_LUMENA\\INBOX"
)

 = Get-Date -Format "yyyyMMdd_HHmmss"
 = Join-Path  "REPORT_.md"

 = git -C  status -sb 2>&1
 = python -c "import asyncio, json, sys; sys.path.insert(0, r'\\CORE'); from corex.health import health_checker; print(json.dumps(asyncio.run(health_checker.deep_check()), indent=2))" 2>&1

 = "# REPORT\n\n## Git Status\n\n```text\n\n```\n\n## Health\n\n```json\n\n```\n"
Set-Content -LiteralPath  -Value  -Encoding UTF8
Write-Host "Saved report to "
