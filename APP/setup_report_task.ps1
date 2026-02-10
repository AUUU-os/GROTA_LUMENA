param(
  [string]$Repo = "E:\SHAD\GROTA_LUMENA"
)

$taskName = "GROTA_REPORT"
$script = "$Repo\APP\generate_report.ps1"

# Create or replace task: run every 6 hours
schtasks /Create /F /SC HOURLY /MO 6 /TN $taskName /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$script`"" | Out-Null
Write-Host "Scheduled task created: $taskName (every 6 hours)"
