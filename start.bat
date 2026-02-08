@echo off
chcp 65001 >nul
echo ========================================
echo   B站视频分析系统 - 一键启动脚本
echo ========================================
echo.

cd /d %~dp0

echo [1/2] 正在启动后端服务 (FastAPI)...
start "FastAPI Backend" cmd /k "cd /d %~dp0 && call venv\Scripts\activate && uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"

echo [2/2] 正在启动前端服务 (Vue)...
timeout /t 2 >nul
start "Vue Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo ========================================
echo   启动完成！
echo   后端地址: http://127.0.0.1:8000
echo   前端地址: http://localhost:3000
echo ========================================
echo.
echo 提示: 关闭此窗口不会停止服务
echo       如需停止，请关闭对应的命令行窗口
echo.
pause
