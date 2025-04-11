@echo off
chcp 65001 > nul
title Maya导出工具启动器

echo ==================================
echo      Maya导出工具启动器(简易版)
echo ==================================
echo.
echo 请选择要启动的工具:
echo 1. ABC批量导出工具
echo 2. 相机FBX批量导出工具
echo 3. 退出
echo.

set /p CHOICE=请输入选项(1-3): 

if "%CHOICE%"=="1" (
    python "%~dp0scripts\multiABCExportStandalone.py"
) else if "%CHOICE%"=="2" (
    python "%~dp0scripts\multiCamFbxExportUI.py"
) else if "%CHOICE%"=="3" (
    exit
) else (
    echo 选择无效，请重新运行程序
    pause
)

pause 