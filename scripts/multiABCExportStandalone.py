# -*- coding: utf-8 -*-
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import QBrush, QColor
import sys
import os
import subprocess
import tempfile
import time
import codecs
import re
import gc

class ABCExportWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Maya ABC批量导出工具")
        self.maya_path = self._find_maya_path()
        if not self.maya_path:
            QMessageBox.critical(self, "错误", "找不到Maya安装路径！")
            sys.exit(1)
        self.setup_ui()
        self.files_to_export = []  # 存储待导出的文件列表
        self.current_export_index = -1  # 当前正在导出的文件索引
        self.export_running = False  # 是否有导出任务正在运行
        self.shader_errors = []  # 存储材质应用错误的列表
        
    def _find_maya_path(self):
        """查找Maya安装路径"""
        default_paths = [
            r"C:\Program Files\Autodesk\Maya2020",
            r"C:\Program Files\Autodesk\Maya2020-x64",
            r"C:\Program Files\Autodesk\Maya2022",
            r"C:\Program Files\Autodesk\Maya2023",
            r"C:\Program Files\Autodesk\Maya2024"
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                return path
        return None
        
    def setup_ui(self):
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 文件操作区域
        file_group = QGroupBox("文件操作")
        file_layout = QVBoxLayout()
        
        # Maya文件选择布局
        maya_file_layout = QHBoxLayout()
        add_files_btn = QPushButton("添加Maya文件")
        add_files_btn.clicked.connect(self.add_maya_files)
        remove_files_btn = QPushButton("移除选中文件")
        remove_files_btn.clicked.connect(self.remove_selected_files)
        clear_files_btn = QPushButton("清空文件列表")
        clear_files_btn.clicked.connect(self.clear_files)
        maya_file_layout.addWidget(add_files_btn)
        maya_file_layout.addWidget(remove_files_btn)
        maya_file_layout.addWidget(clear_files_btn)
        
        # 文件列表视图
        self.file_list = QTableWidget()
        self.file_list.setColumnCount(2)
        self.file_list.setHorizontalHeaderLabels(["文件名", "状态"])
        self.file_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.file_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.file_list.setMinimumHeight(150)
        
        file_layout.addLayout(maya_file_layout)
        file_layout.addWidget(self.file_list)
        file_group.setLayout(file_layout)
        
        # 命名空间筛选框
        filter_group = QGroupBox("命名空间筛选")
        filter_layout = QVBoxLayout()
        
        # 预设命名空间选项
        self.namespace_tbx_chr = QCheckBox("tbx_chr")
        self.namespace_tbx_chr.setChecked(True)
        self.namespace_tbx_prp = QCheckBox("tbx_prp")
        self.namespace_tbx_prp.setChecked(True)
        
        # 自定义命名空间
        custom_layout = QHBoxLayout()
        self.custom_namespace_check = QCheckBox("自定义命名空间:")
        self.custom_namespace_input = QLineEdit()
        self.custom_namespace_input.setPlaceholderText("输入自定义命名空间，用逗号分隔")
        self.custom_namespace_input.setEnabled(False)
        self.custom_namespace_check.toggled.connect(self.custom_namespace_input.setEnabled)
        custom_layout.addWidget(self.custom_namespace_check)
        custom_layout.addWidget(self.custom_namespace_input)
        
        filter_layout.addWidget(self.namespace_tbx_chr)
        filter_layout.addWidget(self.namespace_tbx_prp)
        filter_layout.addLayout(custom_layout)
        filter_group.setLayout(filter_layout)
        
        # 添加文件夹分隔设置选项
        folder_option_group = QGroupBox("子文件夹命名方式")
        folder_layout = QVBoxLayout()
        
        # 创建单选按钮组
        self.folder_option_group = QButtonGroup()
        self.use_second_underscore = QRadioButton("使用第二个下划线前的字符")
        self.use_third_underscore = QRadioButton("使用第三个下划线前的字符")
        self.use_third_underscore.setChecked(True)  # 默认选中第三个下划线
        
        self.folder_option_group.addButton(self.use_second_underscore)
        self.folder_option_group.addButton(self.use_third_underscore)
        
        folder_layout.addWidget(self.use_second_underscore)
        folder_layout.addWidget(self.use_third_underscore)
        folder_option_group.setLayout(folder_layout)
        
        # 输出路径选择
        output_layout = QHBoxLayout()
        self.output_input = QLineEdit()
        output_btn = QPushButton("选择输出路径")
        output_btn.clicked.connect(self.select_output_path)
        output_layout.addWidget(QLabel("输出路径:"))
        output_layout.addWidget(self.output_input)
        output_layout.addWidget(output_btn)
        
        # 材质设置选项
        self.apply_shader_to_faces = QCheckBox("将材质指定到面上")
        self.apply_shader_to_faces.setChecked(True)
        
        # 三角面选项
        self.triangulate_meshes = QCheckBox("导出前将模型转换为三角面")
        self.triangulate_meshes.setChecked(False)  # 默认不选中
        
        # 添加多边形光滑选项
        smooth_group = QGroupBox("多边形光滑")
        smooth_layout = QHBoxLayout()
        
        self.enable_smooth = QCheckBox("导出前应用多边形光滑")
        self.enable_smooth.setChecked(False)  # 默认不选中
        
        smooth_layout.addWidget(self.enable_smooth)
        smooth_layout.addWidget(QLabel("光滑层数:"))
        
        self.smooth_divisions = QSpinBox()
        self.smooth_divisions.setMinimum(1)
        self.smooth_divisions.setMaximum(3)  # 避免设置过高导致性能问题
        self.smooth_divisions.setValue(1)    # 默认值为1
        self.smooth_divisions.setEnabled(False)  # 初始禁用
        
        # 连接选框状态变化和数值选择器的启用状态
        self.enable_smooth.toggled.connect(self.smooth_divisions.setEnabled)
        
        smooth_layout.addWidget(self.smooth_divisions)
        smooth_group.setLayout(smooth_layout)
        
        # 状态与进度区域
        status_group = QGroupBox("状态与进度")
        status_layout = QVBoxLayout()
        
        # 总体状态
        overall_status_layout = QHBoxLayout()
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: green;")
        overall_status_layout.addWidget(QLabel("总体状态:"))
        overall_status_layout.addWidget(self.status_label)
        overall_status_layout.addStretch()
        
        # 总体进度条
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setRange(0, 100)
        self.overall_progress_bar.setValue(0)
        
        # 当前任务状态
        current_task_layout = QHBoxLayout()
        current_task_layout.addWidget(QLabel("当前任务:"))
        self.current_task_label = QLabel("无")
        current_task_layout.addWidget(self.current_task_label)
        current_task_layout.addStretch()
        
        # 当前任务进度条
        self.task_progress_bar = QProgressBar()
        self.task_progress_bar.setRange(0, 100)
        self.task_progress_bar.setValue(0)
        
        status_layout.addLayout(overall_status_layout)
        status_layout.addWidget(self.overall_progress_bar)
        status_layout.addLayout(current_task_layout)
        status_layout.addWidget(self.task_progress_bar)
        status_group.setLayout(status_layout)
        
        # 日志显示区域
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(150)
        self.log_text.setStyleSheet("background-color: #f0f0f0; color: #333333;")
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        self.export_btn = QPushButton("开始批量导出")
        self.export_btn.clicked.connect(self.start_batch_export)
        self.stop_btn = QPushButton("停止导出")
        self.stop_btn.clicked.connect(self.stop_export)
        self.stop_btn.setEnabled(False)
        
        action_layout.addStretch()
        action_layout.addWidget(self.export_btn)
        action_layout.addWidget(self.stop_btn)
        
        # 添加所有控件到主布局
        main_layout.addWidget(file_group)
        main_layout.addWidget(filter_group)
        main_layout.addLayout(output_layout)
        main_layout.addWidget(folder_option_group)
        main_layout.addWidget(self.apply_shader_to_faces)
        main_layout.addWidget(self.triangulate_meshes)
        main_layout.addWidget(smooth_group)  # 添加光滑选项组
        main_layout.addWidget(status_group)
        main_layout.addWidget(log_group)
        main_layout.addLayout(action_layout)
        
        # 设置默认大小
        self.resize(800, 700)
        
    def select_output_path(self):
        dir_name = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            ""
        )
        if dir_name:
            self.output_input.setText(dir_name)
            
    def log(self, message):
        """添加日志到日志区域"""
        current_time = time.strftime("%H:%M:%S", time.localtime())
        log_message = "[%s] %s" % (current_time, message)
        self.log_text.append(log_message)
        # 滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        # 确保UI更新
        QApplication.processEvents()
        
        # 在log方法中添加日志长度限制
        if self.log_text.document().lineCount() > 1500:
            self.log_text.clear()
            self.log("已清理历史日志以提高性能...")
        
    def start_batch_export(self):
        output_path = self.output_input.text()
        
        if not self.files_to_export:
            QMessageBox.warning(self, "错误", "请先添加要导出的Maya文件")
            return
        
        if not output_path:
            QMessageBox.warning(self, "错误", "请选择输出路径")
            return
        
        # 检查输出路径是否存在
        if not os.path.exists(output_path):
            try:
                os.makedirs(output_path)
                self.log(f"创建输出目录: {output_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法创建输出目录: {str(e)}")
                return
        
        # 更新UI状态
        self.export_running = True
        self.export_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.current_export_index = -1
        
        # 重置所有文件状态为"等待导出"
        for file_info in self.files_to_export:
            if file_info["status"] != "success":
                file_info["status"] = "waiting"
                row = file_info["row"]
                status_item = QTableWidgetItem("等待导出")
                status_item.setForeground(QBrush(QColor("blue")))
                self.file_list.setItem(row, 1, status_item)
        
        # 更新总体进度条
        self.overall_progress_bar.setValue(0)
        self.task_progress_bar.setValue(0)
        self.status_label.setText("批量导出中...")
        self.status_label.setStyleSheet("color: blue;")
        
        # 开始导出第一个文件
        self.export_next_file()

    def export_next_file(self):
        if not self.export_running:
            self.log("导出过程被用户中止")
            self.finish_batch_export()
            return
        
        # 更新当前导出索引
        self.current_export_index += 1
        
        # 检查是否所有文件都已导出
        if self.current_export_index >= len(self.files_to_export):
            self.log("所有文件导出完成")
            self.finish_batch_export()
            return
        
        # 获取当前要导出的文件信息
        file_info = self.files_to_export[self.current_export_index]
        maya_file = file_info["path"]
        row = file_info["row"]
        
        # 如果该文件已成功导出，跳过
        if file_info["status"] == "success":
            self.log(f"文件已成功导出，跳过: {os.path.basename(maya_file)}")
            self.export_next_file()
            return
        
        # 更新文件状态
        self.update_file_status("exporting")
        self.file_list.scrollToItem(self.file_list.item(row, 0))
        
        # 更新当前任务标签
        self.current_task_label.setText(os.path.basename(maya_file))
        
        # 更新总体进度
        overall_progress = int((self.current_export_index / len(self.files_to_export)) * 100)
        self.overall_progress_bar.setValue(overall_progress)
        
        # 重置任务进度条
        self.task_progress_bar.setValue(0)
        
        # 获取选择的文件夹选项
        use_underscore_index = 2 if self.use_second_underscore.isChecked() else 3
        
        # 准备导出过程
        self.log(f"开始导出文件 ({self.current_export_index + 1}/{len(self.files_to_export)}): {os.path.basename(maya_file)}")
        self.export_abc_file(maya_file, use_underscore_index)

    def export_abc_file(self, maya_file, use_underscore_index):
        output_path = self.output_input.text()
        
        if not os.path.exists(maya_file):
            self.log(f"错误: Maya文件不存在: {maya_file}")
            self.update_file_status("failed", "文件不存在")
            self.export_next_file()
            return
        
        # 获取命名空间筛选条件
        namespaces = []
        if self.namespace_tbx_chr.isChecked():
            namespaces.append("tbx_chr")
        if self.namespace_tbx_prp.isChecked():
            namespaces.append("tbx_prp")
        if self.custom_namespace_check.isChecked() and self.custom_namespace_input.text():
            custom_namespaces = [ns.strip() for ns in self.custom_namespace_input.text().split(",")]
            namespaces.extend(custom_namespaces)
        
        if not namespaces:
            self.log("错误: 请至少选择一个命名空间筛选条件")
            self.update_file_status("failed", "未选择命名空间")
            self.export_next_file()
            return
        
        # 进度文件路径
        progress_file = os.path.join(output_path, "export_progress.txt")
        
        try:
            # 获取当前脚本所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.log("当前脚本目录: %s" % current_dir)
            
            # 使用独立的abcExportScript.py文件
            self.log("使用独立的ABC导出脚本...")
            export_script_path = os.path.join(current_dir, "abcExportScript.py")
            if not os.path.exists(export_script_path):
                raise Exception("找不到导出脚本: %s" % export_script_path)
            
            self.log("导出脚本路径: %s" % export_script_path)
            
            # 创建进度文件
            if os.path.exists(progress_file):
                os.remove(progress_file)
            
            # 获取Maya文件名作为子子文件夹名称（不含路径和扩展名）
            maya_file_basename = os.path.basename(maya_file)
            maya_file_name = os.path.splitext(maya_file_basename)[0]
            
            # 创建子文件夹名称
            parts = maya_file_name.split('_')
            if len(parts) > use_underscore_index:
                subfolder_name = '_'.join(parts[:use_underscore_index])
            else:
                subfolder_name = maya_file_name
            
            # 创建子文件夹路径
            project_folder_path = os.path.join(output_path, subfolder_name)
            if not os.path.exists(project_folder_path):
                os.makedirs(project_folder_path)
            
            # 创建子子文件夹路径（使用完整Maya文件名）
            subfolder_path = os.path.join(project_folder_path, maya_file_name)
            if not os.path.exists(subfolder_path):
                os.makedirs(subfolder_path)
            
            # 创建日志文件
            log_file = os.path.join(subfolder_path, "export_log.txt")
            if os.path.exists(log_file):
                os.remove(log_file)
            
            # 使用mayapy执行导出
            mayapy = os.path.join(self.maya_path, "bin", "mayapy.exe")
            self.log("使用Maya路径: %s" % mayapy)
            
            # 添加环境变量，确保禁用所有插件
            env = os.environ.copy()
            env["MAYA_DISABLE_PLUGINS"] = "1"
            env["MAYA_DISABLE_CIP"] = "1"
            env["MAYA_DISABLE_CER"] = "1"
            env["MAYA_PLUG_IN_PATH"] = ""
            env["MAYA_SCRIPT_PATH"] = ""
            env["PYTHONPATH"] = current_dir  # 只保留当前目录
            # 设置Python编码环境变量
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONLEGACYWINDOWSIOENCODING"] = "0"
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            
            # 获取导出选项
            apply_shader = self.apply_shader_to_faces.isChecked()
            triangulate = self.triangulate_meshes.isChecked()
            enable_smooth = self.enable_smooth.isChecked()
            smooth_divisions = self.smooth_divisions.value() if enable_smooth else 0
            
            # 构建命令参数列表
            cmd_args = [
                maya_file,
                output_path,
                ",".join(namespaces),
                str(apply_shader).lower(),
                str(triangulate).lower(),
                str(use_underscore_index),
                str(enable_smooth).lower(),
                str(smooth_divisions)
            ]
            
            # 完整的命令
            cmd = [
                mayapy, 
                export_script_path
            ] + cmd_args
            
            self.log("启动导出进程...")
            
            # 使用QProcess替代subprocess
            self.process = QProcess()
            
            # 连接信号
            self.process.readyReadStandardOutput.connect(self.read_process_output)
            self.process.readyReadStandardError.connect(self.read_process_error)
            self.process.finished.connect(self.on_process_finished)
            
            # 设置环境变量
            process_env = QProcessEnvironment()
            for key, value in env.items():
                process_env.insert(key, value)
            self.process.setProcessEnvironment(process_env)
            
            # 启动进程
            self.process.start(cmd[0], cmd[1:])
            
            # 监控进度文件和日志文件
            self.log("开始监控导出进度...")
            start_time = time.time()
            self.timer = QTimer()
            self.timer.timeout.connect(lambda: self.check_progress(start_time, subfolder_path, progress_file, log_file))
            self.timer.start(1000)  # 每秒检查一次
            
            # 进程信息记录到类变量
            self.progress_file = progress_file
            
        except Exception as e:
            self.log(f"导出设置失败: {str(e)}")
            self.update_file_status("failed", "设置失败")
            
            # 继续下一个文件
            self.export_next_file()

    def update_file_status(self, status, message=""):
        """更新当前处理文件的状态"""
        if 0 <= self.current_export_index < len(self.files_to_export):
            file_info = self.files_to_export[self.current_export_index]
            file_info["status"] = status
            row = file_info["row"]
            
            if status == "success":
                status_item = QTableWidgetItem("导出成功")
                status_item.setForeground(QBrush(QColor("green")))
            elif status == "failed":
                status_text = "导出失败"
                if message:
                    status_text += f": {message}"
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(QBrush(QColor("red")))
            elif status == "exporting":
                status_item = QTableWidgetItem("正在导出")
                status_item.setForeground(QBrush(QColor("orange")))
            elif status == "shader_error":
                # 新增材质应用错误状态
                status_text = "材质应用错误"
                if message:
                    status_text += f": {message}"
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(QBrush(QColor("red")))
                # 更新状态栏显示材质错误
                self.show_shader_error(message)
            else:
                status_item = QTableWidgetItem(message)
                status_item.setForeground(QBrush(QColor("blue")))
            
            self.file_list.setItem(row, 1, status_item)
            
    def show_shader_error(self, error_message):
        """显示材质应用错误到状态栏"""
        # 保存错误信息
        self.shader_errors.append(error_message)
        
        # 更新状态栏显示
        self.status_label.setText(f"材质应用错误！")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        # 记录到日志
        self.log(f"材质应用错误: {error_message}")
        
        # 去掉弹窗显示

    def stop_export(self):
        if not self.export_running:
            return
        
        reply = QMessageBox.question(
            self,
            "确认停止",
            "确定要停止当前导出任务吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.export_running = False
            
            # 如果有进程在运行，终止它
            if hasattr(self, 'process') and self.process.state() != QProcess.NotRunning:
                self.process.terminate()
                self.log("正在终止当前导出进程...")
            
            self.status_label.setText("导出已停止")
            self.status_label.setStyleSheet("color: red;")
            
            # 更新当前文件状态为失败
            if 0 <= self.current_export_index < len(self.files_to_export):
                self.update_file_status("failed", "用户中止")

    def finish_batch_export(self):
        # 计算导出结果统计
        success_count = sum(1 for file in self.files_to_export if file["status"] == "success")
        failed_count = sum(1 for file in self.files_to_export if file["status"] == "failed" or file["status"] == "shader_error")
        shader_error_count = sum(1 for file in self.files_to_export if file["status"] == "shader_error")
        
        # 更新UI状态
        self.export_running = False
        self.export_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.current_task_label.setText("无")
        self.overall_progress_bar.setValue(100)
        self.task_progress_bar.setValue(0)
        
        if failed_count == 0:
            self.status_label.setText("所有导出任务完成")
            self.status_label.setStyleSheet("color: green;")
            QMessageBox.information(self, "完成", f"所有 {len(self.files_to_export)} 个文件导出成功！")
        else:
            if shader_error_count > 0:
                self.status_label.setText(f"导出完成 (成功: {success_count}, 失败: {failed_count}, 材质错误: {shader_error_count})")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                
                # 移除材质错误摘要弹窗
                # 只在日志中记录错误信息
                self.log("材质应用错误摘要:")
                for i, file_info in enumerate(self.files_to_export):
                    if file_info["status"] == "shader_error":
                        file_name = os.path.basename(file_info["path"])
                        self.log(f"• {file_name}")
            else:
                self.status_label.setText(f"导出完成 (成功: {success_count}, 失败: {failed_count})")
                self.status_label.setStyleSheet("color: orange;")
            
            QMessageBox.warning(self, "部分完成", f"导出完成，成功: {success_count}，失败: {failed_count}")

    def on_process_finished(self, exit_code, exit_status):
        """处理单个文件导出进程结束事件"""
        self.timer.stop()
        
        if exit_code == 0:
            self.log("文件导出成功")
            self.task_progress_bar.setValue(100)
            
            # 检查是否有材质错误
            has_shader_error = False
            for line in self.log_text.toPlainText().split('\n'):
                if ("应用材质到对象" in line and ("出错" in line or "失败" in line)) or \
                   "Set modification failed" in line or "Connection not made" in line:
                    has_shader_error = True
                    error_msg = line.split('] ')[-1] if '] ' in line else line
                    break
            
            if has_shader_error:
                # 即使导出成功，仍然标记为材质错误
                self.update_file_status("shader_error", error_msg)
                
                # 确保状态栏显示材质错误
                self.status_label.setText(f"导出成功，但存在材质应用错误")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                self.log("导出成功，但存在材质应用错误")
            else:
                self.update_file_status("success")
        else:
            self.log(f"导出进程返回错误代码: {exit_code}")
            
            # 从日志中查找具体错误原因
            error_reason = self.extract_error_reason()
            if error_reason:
                self.update_file_status("failed", error_reason)
                self.log(f"导出失败原因: {error_reason}")
            else:
                self.update_file_status("failed", f"代码: {exit_code}")
        
        # 清理进度文件
        if hasattr(self, 'progress_file') and os.path.exists(self.progress_file):
            try:
                os.remove(self.progress_file)
                self.log("进度文件已删除")
            except Exception as e:
                self.log(f"无法删除进度文件: {str(e)}")
        
        # 如果导出过程仍在运行，处理下一个文件
        if self.export_running:
            # 继续处理下一个文件
            gc.collect()
            QTimer.singleShot(2000, self.export_next_file)  # 增加到2秒
            
    def extract_error_reason(self):
        """从日志和进程输出中提取具体的错误原因"""
        # 尝试从日志文本中提取错误原因
        log_lines = self.log_text.toPlainText().split('\n')
        
        # 常见错误消息及其简化解释
        error_patterns = [
            ("未找到符合条件的cache组", "未找到符合条件的cache组"),
            ("cache组.*不可见", "cache组不可见"),
            ("没有可导出模型", "没有可导出模型"),
            ("打开文件.*失败", "打开文件失败"),
            ("加载.*插件.*出错", "加载插件失败"),
            ("导出ABC时出错", "ABC导出失败"),
            ("处理对象时出错", "对象处理错误"),
            ("导入引用.*出错", "导入引用失败"),
            ("将材质指定到面上时出错", "材质应用失败"),
            ("三角化模型时出错", "三角化模型失败")
        ]
        
        # 从最近的日志开始查找错误原因
        for line in reversed(log_lines):
            # 跳过空行
            if not line.strip():
                continue
                
            # 查找常见错误消息
            for pattern, explanation in error_patterns:
                if re.search(pattern, line):
                    # 提取具体错误信息
                    if '] ' in line:
                        specific_error = line.split('] ')[-1]
                    else:
                        specific_error = line
                    
                    # 截取合适长度的错误信息
                    if len(specific_error) > 50:
                        return explanation
                    else:
                        return specific_error
        
        # 如果找不到具体错误原因，返回通用消息
        return "导出过程失败"

    def add_maya_files(self):
        file_names, _ = QFileDialog.getOpenFileNames(
            self,
            "选择Maya文件",
            "",
            "Maya Files (*.ma *.mb)"
        )
        
        if file_names:
            added_count = 0
            for file_path in file_names:
                # 检查文件是否已在列表中
                file_exists = False
                for file_info in self.files_to_export:
                    if file_info["path"] == file_path:
                        file_exists = True
                        break
                
                if not file_exists:
                    # 将新文件添加到files_to_export
                    self.files_to_export.append({
                        "path": file_path,
                        "status": "waiting",
                        "row": 0  # 临时值，稍后重建
                    })
                    added_count += 1
            
            if added_count > 0:
                self.log(f"已添加 {added_count} 个文件到导出列表")
                # 重新构建整个表格
                self._rebuild_file_list_ui()
            else:
                self.log("没有添加新文件，选择的文件已在列表中")

    def _rebuild_file_list_ui(self):
        """重新构建文件列表UI"""
        # 清空表格
        self.file_list.setRowCount(0)
        
        # 重新为每个文件分配行号
        for i, file_info in enumerate(self.files_to_export):
            file_info["row"] = i
            
            # 添加到表格
            self.file_list.insertRow(i)
            
            # 文件名
            file_name = os.path.basename(file_info["path"])
            self.file_list.setItem(i, 0, QTableWidgetItem(file_name))
            
            # 状态
            status_text = "等待导出"
            color = "blue"
            
            if file_info["status"] == "success":
                status_text = "导出成功"
                color = "green"
            elif file_info["status"] == "failed":
                status_text = "导出失败"
                color = "red"
            elif file_info["status"] == "exporting":
                status_text = "正在导出"
                color = "orange"
            
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QBrush(QColor(color)))
            self.file_list.setItem(i, 1, status_item)
        
        # 刷新UI
        self.file_list.update()
        QApplication.processEvents()

    def remove_selected_files(self):
        selected_rows = sorted(set(index.row() for index in self.file_list.selectedIndexes()), reverse=True)
        
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择要移除的文件")
            return
        
        # 如果导出正在进行，不允许移除
        if self.export_running:
            QMessageBox.warning(self, "警告", "导出过程中不能移除文件")
            return
        
        removed_count = 0
        # 从files_to_export中移除对应文件
        for row in selected_rows:
            for i, file_info in enumerate(self.files_to_export):
                if file_info["row"] == row:
                    self.files_to_export.pop(i)
                    removed_count += 1
        
        self.log(f"已移除 {removed_count} 个文件")
        
        # 重建UI
        self._rebuild_file_list_ui()

    def clear_files(self):
        # 如果导出正在进行，不允许清空
        if self.export_running:
            QMessageBox.warning(self, "警告", "导出过程中不能清空文件列表")
            return
        
        # 清空文件列表
        self.files_to_export.clear()
        self.file_list.setRowCount(0)
        self.log("已清空文件列表")

    def read_process_output(self):
        """读取进程的标准输出"""
        data = self.process.readAllStandardOutput()
        line_str = bytes(data).decode('utf-8', errors='ignore').strip()
        if line_str:
            self.log("输出: %s" % line_str)
            
            # 检测材质应用错误
            if "应用材质到对象" in line_str and ("出错" in line_str or "失败" in line_str):
                self.update_file_status("shader_error", line_str)
            # 检测Set modification failed错误
            elif "Set modification failed" in line_str or "Connection not made" in line_str:
                self.update_file_status("shader_error", line_str)

    def read_process_error(self):
        """读取进程的错误输出"""
        data = self.process.readAllStandardError()
        line_str = bytes(data).decode('utf-8', errors='ignore').strip()
        if line_str:
            self.log("错误: %s" % line_str)
            
            # 检测材质应用错误
            if "应用材质到对象" in line_str and ("出错" in line_str or "失败" in line_str):
                self.update_file_status("shader_error", line_str)
            # 检测Set modification failed错误
            elif "Set modification failed" in line_str or "Connection not made" in line_str:
                self.update_file_status("shader_error", line_str)

    def check_progress(self, start_time, output_path, progress_file, log_file):
        """检查进度和日志文件"""
        # 检查超时 - 默认为30分钟
        if time.time() - start_time > 1800:  # 30分钟 = 1800秒
            self.log("导出过程超时，中止任务")
            self.process.terminate()
            self.timer.stop()
            self.update_file_status("failed", "超时")
            
            # 继续下一个文件
            if self.export_running:
                QTimer.singleShot(2000, self.export_next_file)
            return
        
        # 检查进度文件
        if os.path.exists(progress_file):
            try:
                with codecs.open(progress_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip().split('\n')
                    if len(content) >= 2:
                        try:
                            progress = int(content[0])
                            message = content[1]
                            self.task_progress_bar.setValue(progress)
                            self.current_task_label.setText(message)
                        except ValueError:
                            self.log("进度值格式错误: %s" % content[0])
            except Exception as e:
                self.log("读取进度文件时出错: %s" % str(e))
        
        # 检查日志文件
        if os.path.exists(log_file):
            try:
                with codecs.open(log_file, 'r', encoding='utf-8') as f:
                    logs = f.readlines()
                    for log_line in logs[-10:]:  # 只读取最新的10行
                        if log_line.strip() and not log_line.strip() in self.log_text.toPlainText():
                            self.log(log_line.strip())
            except Exception as e:
                self.log("读取日志文件时出错: %s" % str(e))

def main():
    app = QApplication(sys.argv)
    window = ABCExportWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 