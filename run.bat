@echo off
chcp 65001 >nul
title 旅行助手 - Travel Assistant

echo ============================================
echo   🏖️  旅行计划生成助手 - Travel Assistant
echo ============================================
echo.

:: 检查 .env 文件
if not exist ".env" (
    echo [⚠️]  未找到 .env 配置文件！
    echo.
    echo 请执行以下步骤：
    echo   1. 复制 .env.example 为 .env
    echo   2. 编辑 .env 填入你的 API Key
    echo.
    echo 当前使用默认配置运行（可能部分功能不可用）...
    echo.
)

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [❌] 未找到 Python！请先安装 Python 3.8+
    echo   下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查虚拟环境
if not exist ".venv\" (
    echo [📦] 正在创建虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo [❌] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo [✅] 虚拟环境创建完成
)

:: 激活虚拟环境
call .venv\Scripts\activate.bat

:: 安装依赖
echo [📦] 正在检查依赖...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [❌] 依赖安装失败
    pause
    exit /b 1
)
echo [✅] 依赖已安装

:: 启动应用
echo.
echo [🚀] 正在启动服务器...
echo.
echo 请在浏览器中打开：http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo ============================================
echo.

python app.py

pause
