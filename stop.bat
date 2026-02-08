@echo off
chcp 65001 >nul
echo ========================================
echo   B站视频分析系统 - 停止服务脚本
echo ========================================
echo.

echo 正在停止后端服务 (uvicorn)...
taskkill /f /im uvicorn.exe 2>nul
taskkill /f /im python.exe /fi "WINDOWTITLE eq FastAPI*" 2>nul

echo 正在停止前端服务 (node)...
taskkill /f /im node.exe /fi "WINDOWTITLE eq Vue*" 2>nul

echo.
echo 服务已停止！
echo.
pause
