# -*- coding: utf-8 -*-
from PySide2.QtWidgets import *
from PySide2.QtCore import *
import sys
import os
import subprocess
import tempfile
import time
import codecs
import re

class ABCExportWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Maya ABC导出工具")
        self.maya_path = self._find_maya_path()
        if not self.maya_path:
            QMessageBox.critical(self, "错误", "找不到Maya安装路径！")
            sys.exit(1)
        self.setup_ui()
        
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
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # Maya文件选择
        maya_file_layout = QHBoxLayout()
        self.maya_file_input = QLineEdit()
        maya_file_btn = QPushButton("选择Maya文件")
        maya_file_btn.clicked.connect(self.select_maya_file)
        maya_file_layout.addWidget(QLabel("Maya文件:"))
        maya_file_layout.addWidget(self.maya_file_input)
        maya_file_layout.addWidget(maya_file_btn)
        
        # 命名空间筛选框
        filter_group = QGroupBox("命名空间筛选")
        filter_layout = QVBoxLayout(filter_group)
        
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
        
        # 添加文件夹分隔设置选项
        folder_option_group = QGroupBox("子文件夹命名方式")
        folder_layout = QVBoxLayout()
        
        # 创建单选按钮组
        self.use_second_underscore = QRadioButton("使用第二个下划线前的字符")
        self.use_third_underscore = QRadioButton("使用第三个下划线前的字符")
        self.use_third_underscore.setChecked(True)  # 默认选中第三个下划线
        
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
        
        # 在材质设置选项下面添加三角面选项
        self.triangulate_meshes = QCheckBox("导出前将模型转换为三角面")
        self.triangulate_meshes.setChecked(False)  # 默认不选中
        
        # 状态显示
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: green;")
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)  # 设置为0-100的进度条
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        
        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(150)
        self.log_text.setStyleSheet("background-color: #f0f0f0; color: #333333;")
        
        # 导出按钮
        self.export_btn = QPushButton("导出ABC")
        self.export_btn.clicked.connect(self.export_abc_standalone)
        
        # 添加所有控件到主布局
        layout.addLayout(maya_file_layout)
        layout.addWidget(filter_group)
        layout.addLayout(output_layout)
        layout.addWidget(folder_option_group)
        layout.addWidget(self.apply_shader_to_faces)
        layout.addWidget(self.triangulate_meshes)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(QLabel("操作日志:"))
        layout.addWidget(self.log_text)
        layout.addWidget(self.export_btn)
        
        # 设置默认大小
        self.resize(800, 600)
        
    def select_maya_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "选择Maya文件",
            "",
            "Maya Files (*.ma *.mb)"
        )
        if file_name:
            self.maya_file_input.setText(file_name)
            
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
        
    def export_abc_standalone(self):
        maya_file = self.maya_file_input.text()
        output_path = self.output_input.text()
        
        if not maya_file or not output_path:
            QMessageBox.warning(self, "错误", "请选择Maya文件和输出路径")
            return
            
        if not os.path.exists(maya_file):
            QMessageBox.warning(self, "错误", "Maya文件不存在")
            return
            
        # 获取Maya文件名作为子子文件夹名称（不含路径和扩展名）
        maya_file_basename = os.path.basename(maya_file)
        maya_file_name = os.path.splitext(maya_file_basename)[0]
        
        # 获取选择的文件夹选项
        use_underscore_index = 2 if self.use_second_underscore.isChecked() else 3
        
        # 创建子文件夹名称 (使用第N个下划线前的部分)
        parts = maya_file_name.split('_')
        if len(parts) > use_underscore_index:
            # 有足够的下划线，取到第N个下划线前的部分
            subfolder_name = '_'.join(parts[:use_underscore_index])
        else:
            # 如果下划线不足，使用整个名称
            subfolder_name = maya_file_name
            
        self.log("Maya文件名: %s" % maya_file_basename)
        self.log("使用第%d个下划线前的字符作为子文件夹名称" % use_underscore_index)
        self.log("子文件夹名称: %s" % subfolder_name)
        
        # 创建子文件夹路径
        project_folder_path = os.path.join(output_path, subfolder_name)
        if not os.path.exists(project_folder_path):
            os.makedirs(project_folder_path)
        self.log("创建项目子文件夹: %s" % project_folder_path)
        
        # 创建子子文件夹路径（使用完整Maya文件名）
        subfolder_path = os.path.join(project_folder_path, maya_file_name)
        if not os.path.exists(subfolder_path):
            os.makedirs(subfolder_path)
        self.log("创建导出子子文件夹: %s" % subfolder_path)
        
        # 禁用导出按钮并显示进度条
        self.export_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.status_label.setText("正在导出...")
        self.status_label.setStyleSheet("color: blue;")
        
        # 清空日志区域
        self.log_text.clear()
        self.log("开始ABC导出任务...")
        self.log("Maya文件: %s" % maya_file)
        self.log("输出路径: %s" % subfolder_path)
        
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
            QMessageBox.warning(self, "错误", "请至少选择一个命名空间筛选条件")
            self.export_btn.setEnabled(True)
            self.progress_bar.hide()
            return
            
        self.log("命名空间筛选: %s" % ", ".join(namespaces))
        apply_shader = self.apply_shader_to_faces.isChecked()
        triangulate = self.triangulate_meshes.isChecked()
        self.log("将材质指定到面上: %s" % ("是" if apply_shader else "否"))
        self.log("三角化模型: %s" % ("是" if triangulate else "否"))
        
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
            
            # 确保子文件夹存在
            if not os.path.exists(subfolder_path):
                os.makedirs(subfolder_path)
                self.log("创建子文件夹: %s" % subfolder_path)
            
            # 创建进度文件
            if os.path.exists(progress_file):
                os.remove(progress_file)
            
            # 创建日志文件
            log_file = os.path.join(subfolder_path, "export_log.txt")
            if os.path.exists(log_file):
                os.remove(log_file)
            
            # 使用mayapy执行导出
            mayapy = os.path.join(self.maya_path, "bin", "mayapy.exe")
            self.log("使用Maya路径: %s" % mayapy)
            
            # 添加更多环境变量，确保禁用所有插件
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
            self.log("设置环境变量以禁用插件自动加载")
            
            # 构建命令参数列表
            cmd_args = [
                maya_file,
                output_path,
                ",".join(namespaces),
                str(apply_shader).lower(),
                str(triangulate).lower(),
                str(use_underscore_index)
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
            self.process.finished.connect(self.process_finished)
            
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
            self.process_running = True
            
        except Exception as e:
            self.status_label.setText("导出失败")
            self.status_label.setStyleSheet("color: red;")
            self.log("导出失败: %s" % str(e))
            QMessageBox.critical(self, "错误", str(e))
            
            # 恢复UI状态
            self.export_btn.setEnabled(True)
            self.progress_bar.hide()

    def read_process_output(self):
        """读取进程的标准输出"""
        data = self.process.readAllStandardOutput()
        line_str = bytes(data).decode('utf-8', errors='ignore').strip()
        if line_str:
            self.log("输出: %s" % line_str)
    
    def read_process_error(self):
        """读取进程的错误输出"""
        data = self.process.readAllStandardError()
        line_str = bytes(data).decode('utf-8', errors='ignore').strip()
        if line_str:
            self.log("错误: %s" % line_str)
    
    def check_progress(self, start_time, output_path, progress_file, log_file):
        """检查进度和日志文件"""
        # 检查超时 - 修改为30分钟
        if time.time() - start_time > 1800:  # 30分钟 = 1800秒
            self.log("导出过程超时，中止任务")
            self.process.terminate()
            self.timer.stop()
            self.process_running = False
            self.status_label.setText("导出失败：超时")
            self.status_label.setStyleSheet("color: red;")
            self.export_btn.setEnabled(True)
            self.progress_bar.hide()
            QMessageBox.critical(self, "错误", "导出任务超时（30分钟）")
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
                            self.progress_bar.setValue(progress)
                            self.status_label.setText(message)
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
    
    def process_finished(self, exit_code, exit_status):
        """处理进程结束事件"""
        self.timer.stop()
        self.process_running = False
        
        if exit_code == 0:
            self.progress_bar.setValue(100)
            self.status_label.setText("导出完成！")
            self.status_label.setStyleSheet("color: green;")
            self.log("导出任务成功完成！")
            QMessageBox.information(self, "成功", "ABC导出完成！")
        else:
            self.log("导出进程返回错误代码: %s" % exit_code)
            self.status_label.setText("导出失败")
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.critical(self, "错误", "导出失败，返回代码：" + str(exit_code))
        
        # 清理进度文件
        if hasattr(self, 'progress_file') and os.path.exists(self.progress_file):
            try:
                os.remove(self.progress_file)
                self.log("进度文件已删除")
            except Exception as e:
                self.log("无法删除进度文件: %s" % str(e))
        
        # 恢复UI状态
        self.export_btn.setEnabled(True)
        self.progress_bar.hide()

def main():
    app = QApplication(sys.argv)
    window = ABCExportWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 