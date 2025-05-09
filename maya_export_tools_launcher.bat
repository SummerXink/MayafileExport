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
echo 3. 安装环境 (Python 2.7 + pip + PySide2)
echo 4. 退出
echo.

:: 获取用户选择
set /p CHOICE=请输入选项 (1, 2, 3 或 4): 

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
    echo 正在检查并安装环境...
    echo.
    
    :: 检查Python是否已安装
    python --version > nul 2>&1
    if errorlevel 1 (
        echo Python未安装，正在下载Python 2.7...
        echo 请稍等...
        
        :: 创建临时目录
        mkdir "%TEMP%\python_install" 2>nul
        
        :: 下载Python 2.7安装程序
        powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/2.7.18/python-2.7.18.amd64.msi' -OutFile '%TEMP%\python_install\python-2.7.18.msi'}"
        
        :: 安装Python
        echo 正在安装Python 2.7...
        msiexec /i "%TEMP%\python_install\python-2.7.18.msi" /qn
        
        :: 等待安装完成
        timeout /t 30 /nobreak
        
        :: 清理临时文件
        rmdir /s /q "%TEMP%\python_install"
        
        echo Python 2.7 安装完成！
    ) else (
        echo Python已安装，跳过安装步骤。
    )
    
    :: 检查pip是否已安装
    pip --version > nul 2>&1
    if errorlevel 1 (
        echo 正在安装pip...
        powershell -Command "& {Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/pip/2.7/get-pip.py' -OutFile '%TEMP%\get-pip.py'}"
        python "%TEMP%\get-pip.py"
        del "%TEMP%\get-pip.py"
        echo pip安装完成！
    ) else (
        echo pip已安装，跳过安装步骤。
    )
    
    :: 安装PySide2
    echo 正在安装PySide2...
    pip install PySide2
    
    echo.
    echo 环境安装完成！
    echo 请确保已安装Maya 2020。
    pause
    cls
    goto menu
) else if "%CHOICE%"=="4" (
    echo.
    echo 感谢使用，再见！
    ping -n 2 127.0.0.1 > nul
    exit
) else (
    echo.
    echo 无效的选择！请输入1、2、3或4。
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