@echo off
chcp 65001 > nul
title Maya导出工具启动器

:: 设置窗口颜色 - 蓝底白字
color 1F

:: 获取当前目录
set SCRIPT_DIR=%~dp0scripts\

:menu
:: 输出欢迎信息
echo ====================================================
echo                Maya导出工具启动器
echo ====================================================
echo.
echo 请选择要启动的工具:
echo.
echo 1. ABC批量导出工具 (multiABCExportStandalone.py)
echo 2. 相机FBX批量导出工具 (multiCamFbxExportUI.py)
echo 3. 退出
echo.

:: 获取用户选择
set /p CHOICE=请输入选项 (1, 2 或 3): 

:: 处理用户选择
if "%CHOICE%"=="1" (
    echo.
    echo 正在启动ABC批量导出工具...
    echo.
    python "%SCRIPT_DIR%multiABCExportStandalone.py"
) else if "%CHOICE%"=="2" (
    echo.
    echo 正在启动相机FBX批量导出工具...
    echo.
    python "%SCRIPT_DIR%multiCamFbxExportUI.py"
) else if "%CHOICE%"=="3" (
    echo.
    echo 感谢使用，再见！
    ping -n 2 127.0.0.1 > nul
    exit
) else (
    echo.
    echo 无效的选择！请输入1、2或3。
    echo 按任意键重新启动...
    pause > nul
    cls
    goto menu
)

:: 如果程序结束，询问是否重新启动
echo.
echo 程序已结束。
echo.
set /p RESTART=是否重新启动工具选择界面？(Y/N): 

if /i "%RESTART%"=="Y" (
    cls
    goto menu
) else (
    echo 感谢使用，再见！
    ping -n 2 127.0.0.1 > nul
) 