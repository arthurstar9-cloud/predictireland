@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo  PREDICT IRELAND - REMOVE SCHEDULED TASKS
echo ============================================
echo.

powershell -NoProfile -Command ^
  "foreach ($name in @('PredictIreland_Tue','PredictIreland_Thu','PredictIreland_Sat','PredictIreland_Sun')) { ^
     $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue; ^
     if ($task) { Unregister-ScheduledTask -TaskName $name -Confirm:$false; Write-Host \"Removed: $name\" } ^
     else { Write-Host \"Not found: $name (skipped)\" } ^
   }"

echo.
echo All PredictIreland tasks removed.
echo.
pause
