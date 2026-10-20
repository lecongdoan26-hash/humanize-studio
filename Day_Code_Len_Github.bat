@echo off
chcp 65001 > nul
title Day Code Len GitHub - Humanize Studio
cd /d "c:\Users\Admin\Downloads\DOAN MKT AI"
echo ========================================================
echo   🚀 DANG DAY MA NGUON LEN GITHUB
echo   Repo: https://github.com/lecongdoan26-hash/humanize-studio
echo ========================================================
echo.
set "PATH=C:\Program Files\Git\cmd;C:\Program Files\GitHub CLI;%PATH%"
for /f "tokens=*" %%i in ('gh auth token 2^>nul') do set GHTOKEN=%%i
if defined GHTOKEN (
    git push https://lecongdoan26-hash:%GHTOKEN%@github.com/lecongdoan26-hash/humanize-studio.git main
) else (
    git push -u origin main
)
echo.
echo ========================================================
echo Hoan tat! Nhan phim bat ky de thoat...
pause > nul
