@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo  PREDICT IRELAND - TASK SCHEDULER SETUP
echo ============================================
echo.
echo Run as Administrator on this machine.
echo.
echo Working directory: %cd%
echo User: %USERNAME%
echo.

set WORKDIR=%cd%

:: Remove existing tasks first
echo Removing existing tasks (if any)...
powershell -NoProfile -Command ^
  "foreach ($name in @('PredictIreland_Tue','PredictIreland_Thu','PredictIreland_Sat','PredictIreland_Sun')) { Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue }"
echo.

echo Creating tasks...
echo.

:: 1. Tuesday 19:30 - Pillar 1 (bookie comparison)
echo [1/4] PredictIreland_Tue (Tuesday 19:30 - Pillar 1)...
powershell -NoProfile -Command ^
  "$action = New-ScheduledTaskAction -Execute '%WORKDIR%\run_post.bat' -Argument '1' -WorkingDirectory '%WORKDIR%'; ^
   $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday -At '19:30'; ^
   $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable; ^
   Register-ScheduledTask -TaskName 'PredictIreland_Tue' -Action $action -Trigger $trigger -Settings $settings -User '%USERNAME%' -Force"
echo.

:: 2. Thursday 19:30 - Pillar 2 (weekly roundup)
echo [2/4] PredictIreland_Thu (Thursday 19:30 - Pillar 2)...
powershell -NoProfile -Command ^
  "$action = New-ScheduledTaskAction -Execute '%WORKDIR%\run_post.bat' -Argument '2' -WorkingDirectory '%WORKDIR%'; ^
   $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Thursday -At '19:30'; ^
   $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable; ^
   Register-ScheduledTask -TaskName 'PredictIreland_Thu' -Action $action -Trigger $trigger -Settings $settings -User '%USERNAME%' -Force"
echo.

:: 3. Saturday 20:00 - Pillar 3 (educational)
echo [3/4] PredictIreland_Sat (Saturday 20:00 - Pillar 3)...
powershell -NoProfile -Command ^
  "$action = New-ScheduledTaskAction -Execute '%WORKDIR%\run_post.bat' -Argument '3' -WorkingDirectory '%WORKDIR%'; ^
   $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Saturday -At '20:00'; ^
   $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable; ^
   Register-ScheduledTask -TaskName 'PredictIreland_Sat' -Action $action -Trigger $trigger -Settings $settings -User '%USERNAME%' -Force"
echo.

:: 4. Sunday 19:00 - Pillar 2 (weekly roundup)
echo [4/4] PredictIreland_Sun (Sunday 19:00 - Pillar 2)...
powershell -NoProfile -Command ^
  "$action = New-ScheduledTaskAction -Execute '%WORKDIR%\run_post.bat' -Argument '2' -WorkingDirectory '%WORKDIR%'; ^
   $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At '19:00'; ^
   $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable; ^
   Register-ScheduledTask -TaskName 'PredictIreland_Sun' -Action $action -Trigger $trigger -Settings $settings -User '%USERNAME%' -Force"
echo.

:: Verify
echo ============================================
echo  VERIFICATION
echo ============================================
powershell -NoProfile -Command "Get-ScheduledTask | Where-Object {$_.TaskName -like 'PredictIreland_*'} | Select-Object TaskName, State | Format-Table -AutoSize"

echo.
echo Done! To test manually: run_post.bat 1
echo To remove all tasks:    stop_posting.bat
echo.
pause
