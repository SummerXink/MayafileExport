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

class CameraExportWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Maya相机FBX批量导出工具")
        self.maya_path = self._find_maya_path()
        if not self.maya_path:
            QMessageBox.critical(self, "错误", "找不到Maya安装路径！")
            sys.exit(1)
        self.setup_ui()
        self.files_to_export = []  # 存储待导出的文件列表
        self.current_export_index = -1  # 当前正在导出的文件索引
        self.export_running = False  # 是否有导出任务正在运行
        
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
        
        # 输出设置区域
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout()
        
        # 输出路径选择
        output_path_layout = QHBoxLayout()
        self.output_input = QLineEdit()
        output_btn = QPushButton("选择输出路径")
        output_btn.clicked.connect(self.select_output_path)
        output_path_layout.addWidget(QLabel("输出路径:"))
        output_path_layout.addWidget(self.output_input)
        output_path_layout.addWidget(output_btn)
        
        # 添加文件夹分隔设置选项
        folder_option_layout = QHBoxLayout()
        folder_option_layout.addWidget(QLabel("子文件夹命名方式:"))
        
        # 创建单选按钮组
        self.folder_option_group = QButtonGroup()
        self.use_second_underscore = QRadioButton("使用第二个下划线前的字符")
        self.use_third_underscore = QRadioButton("使用第三个下划线前的字符")
        self.use_third_underscore.setChecked(True)  # 默认选中第三个下划线
        
        self.folder_option_group.addButton(self.use_second_underscore)
        self.folder_option_group.addButton(self.use_third_underscore)
        
        folder_option_layout.addWidget(self.use_second_underscore)
        folder_option_layout.addWidget(self.use_third_underscore)
        folder_option_layout.addStretch()
        
        # 添加引用加载选项
        reference_option_layout = QHBoxLayout()
        reference_option_layout.addWidget(QLabel("引用加载:"))
        self.load_references = QCheckBox("加载引用,(当相机被引用约束时使用)")
        self.load_references.setChecked(False)  # 默认不加载引用
        reference_option_layout.addWidget(self.load_references)
        reference_option_layout.addStretch()
        
        output_layout.addLayout(output_path_layout)
        output_layout.addLayout(folder_option_layout)
        output_layout.addLayout(reference_option_layout)  # 添加引用选项布局
        output_group.setLayout(output_layout)
        
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
        
        # 当前任务进度条
        current_task_layout = QHBoxLayout()
        current_task_layout.addWidget(QLabel("当前任务:"))
        self.current_task_label = QLabel("无")
        current_task_layout.addWidget(self.current_task_label)
        current_task_layout.addStretch()
        
        self.task_progress_bar = QProgressBar()
        self.task_progress_bar.setRange(0, 100)
        self.task_progress_bar.setValue(0)
        
        status_layout.addLayout(overall_status_layout)
        status_layout.addWidget(self.overall_progress_bar)
        status_layout.addLayout(current_task_layout)
        status_layout.addWidget(self.task_progress_bar)
        status_group.setLayout(status_layout)
        
        # 日志区域
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
        main_layout.addWidget(output_group)
        main_layout.addWidget(status_group)
        main_layout.addWidget(log_group)
        main_layout.addLayout(action_layout)
        
        # 设置窗口大小
        self.resize(800, 700)
    
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
    
    def select_output_path(self):
        dir_name = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            ""
        )
        if dir_name:
            self.output_input.setText(dir_name)
    
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
        status_item = QTableWidgetItem("正在导出")
        status_item.setForeground(QBrush(QColor("orange")))
        self.file_list.setItem(row, 1, status_item)
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
        
        # 获取是否加载引用的设置
        load_references = self.load_references.isChecked()
        
        # 准备导出过程
        self.log(f"开始导出文件 ({self.current_export_index + 1}/{len(self.files_to_export)}): {os.path.basename(maya_file)}")
        self.export(maya_file, use_underscore_index, load_references)
    
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
                file_info = self.files_to_export[self.current_export_index]
                file_info["status"] = "failed"
                row = file_info["row"]
                status_item = QTableWidgetItem("已中止")
                status_item.setForeground(QBrush(QColor("red")))
                self.file_list.setItem(row, 1, status_item)
    
    def finish_batch_export(self):
        # 计算导出结果统计
        success_count = sum(1 for file in self.files_to_export if file["status"] == "success")
        failed_count = sum(1 for file in self.files_to_export if file["status"] == "failed")
        
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
            self.status_label.setText(f"导出完成 (成功: {success_count}, 失败: {failed_count})")
            self.status_label.setStyleSheet("color: orange;")
            QMessageBox.warning(self, "部分完成", f"导出完成，成功: {success_count}，失败: {failed_count}")
    
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
    
    def export(self, maya_file, use_underscore_index, load_references):
        output_path = self.output_input.text()
        
        if not os.path.exists(maya_file):
            self.log(f"错误: Maya文件不存在: {maya_file}")
            self.update_file_status("failed", "文件不存在")
            self.export_next_file()
            return
        
        # 初始化临时文件路径变量
        temp_script = None
        progress_file = os.path.join(output_path, "export_progress.txt")
        
        try:
            # 获取当前脚本所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.log("当前脚本目录: %s" % current_dir)
            
            # 创建临时Python脚本
            self.log("正在创建临时导出脚本...")
            
            # 使用一种完全避免任何格式化字符冲突的方式
            safe_current_dir = current_dir.replace('\\', '\\\\')  # 确保路径转义正确
            safe_output_path = output_path.replace('\\', '\\\\')
            safe_maya_file = maya_file.replace('\\', '\\\\')
            
            script_content = """# -*- coding: utf-8 -*-
import sys
import os
import time
import traceback

# 确保Python 2.7兼容的Unicode处理
reload(sys)
sys.setdefaultencoding('utf-8')

# 添加当前目录到Python路径
current_dir = r'%s'
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 创建日志文件
log_file = os.path.join(r'%s', 'export_log.txt')
def write_log(message):
    with open(log_file, 'a') as f:
        current_time = time.strftime('%%Y-%%m-%%d %%H:%%M:%%S')
        f.write('[' + current_time + '] ' + message + '\\n')

# 设置使用第几个下划线的选项
use_underscore_index = %d
write_log('开始初始化Maya独立模式...')
write_log('使用第%%d个下划线前的字符作为子文件夹名称' %% use_underscore_index)

try:
    # 初始化Maya独立模式
    import maya.standalone
    # 设置环境变量以禁用自动插件加载
    os.environ['MAYA_DISABLE_PLUGINS'] = '1'
    os.environ['MAYA_DISABLE_CIP'] = '1'  # 禁用客户参与计划
    os.environ['MAYA_DISABLE_CER'] = '1'  # 禁用崩溃报告
    # 禁用插件路径
    os.environ['MAYA_PLUG_IN_PATH'] = ''
    # 初始化Maya
    write_log('使用无UI模式初始化Maya...')
    maya.standalone.initialize(name='python')
    write_log('Maya独立模式初始化完成')

    # 导入Maya命令
    import maya.cmds as cmds
    import maya.mel as mel

    # 不卸载任何插件，避免崩溃
    write_log('检查插件状态...')
    try:
        loaded_plugins = cmds.pluginInfo(query=True, listPlugins=True) or []
        write_log('当前加载的插件: ' + str(loaded_plugins))
        
        # 只确保FBX插件加载
        write_log('加载FBX插件...')
        if 'fbxmaya.mll' not in loaded_plugins:
            cmds.loadPlugin('fbxmaya', quiet=True)
            write_log('FBX插件加载成功')
        else:
            write_log('FBX插件已加载')
    except Exception as e:
        write_log('处理插件时出错: ' + str(e))

    # 禁用所有插件的自动加载
    cmds.optionVar(intValue=['autoLoadPlugins', 0])
    # 设置其他选项以提高稳定性
    cmds.optionVar(intValue=['CIP', 0])  # 禁用客户参与计划
    cmds.optionVar(intValue=['CER', 0])  # 禁用崩溃报告

    # 打开Maya文件
    write_log('打开Maya文件...')
    # 禁用自动加载插件
    cmds.optionVar(intValue=['autoLoadPlugins', 0])
    
    # 创建新的空场景
    write_log('创建新场景...')
    cmds.file(new=True, force=True)
    
    # 禁用渲染器和绘图更新，提高稳定性
    try:
        cmds.optionVar(intValue=('renderSetupEnable', 0))  # 禁用渲染设置
        try:
            cmds.modelEditor('modelPanel4', edit=True, displayAppearance='wireframe') # 使用线框模式
        except:
            pass # 忽略没有UI时的错误
    except Exception as e:
        write_log('设置渲染选项时出错(可忽略): ' + str(e))
    
    # 设置MEL变量以忽略特定类型的插件错误
    mel.eval('global string $gMayaIgnoredWarnings[];')
    mel.eval('$gMayaIgnoredWarnings[size($gMayaIgnoredWarnings)] = \"Unable to dynamically load\";')
    mel.eval('$gMayaIgnoredWarnings[size($gMayaIgnoredWarnings)] = \"Redshift\";')
    mel.eval('$gMayaIgnoredWarnings[size($gMayaIgnoredWarnings)] = \"rsMaterial\";')
    mel.eval('$gMayaIgnoredWarnings[size($gMayaIgnoredWarnings)] = \"The shadingEngine\";')
    
    # 设置更安全的文件加载选项
    file_options = {
        'open': True,
        'force': True,
        'ignoreVersion': True,
        'loadReferenceDepth': 'all' if %s else 'none',  # 根据选项决定是否加载引用
        'prompt': False,
        'loadNoReferences': not %s,  # 根据选项决定是否加载引用
        'returnNewNodes': False
    }

    write_log('尝试打开文件: ' + r'%s')
    # 尝试加载文件, 忽略未知节点错误
    file_open_success = False
    try:
        cmds.file(r'%s', **file_options)
        write_log('Maya文件已成功打开')
        file_open_success = True
    except Exception as e:
        error_msg = str(e)
        write_log('打开文件时出现错误，尝试替代方法: ' + error_msg)
        # 尝试用MEL命令打开
        try:
            write_log('使用MEL命令尝试打开文件...')
            mel.eval('setConstructionHistory(false);')
            if %s:
                mel.eval('file -open -force -ignoreVersion -prompt false \"%s\";')
            else:
                mel.eval('file -open -force -ignoreVersion -prompt false -loadNoReferences \"%s\";')
            write_log('使用MEL命令打开文件成功')
            file_open_success = True
        except Exception as e2:
            write_log('使用MEL命令打开文件失败: ' + str(e2))
            write_log('将继续尝试导出，但可能不成功')
    
    # 如果文件打开失败，尝试创建一个简单的测试场景
    if not file_open_success:
        try:
            write_log('创建测试场景...')
            cmds.camera(name='test_camera_CAM')
            write_log('创建测试相机成功')
        except Exception as e:
            write_log('创建测试相机失败: ' + str(e))
    
    # 检查场景中是否有相机
    write_log('检查场景中的相机...')
    try:
        all_cameras = cmds.ls(type='camera')
        if not all_cameras:
            write_log('警告: 场景中没有找到相机')
        else:
            write_log('场景中找到 ' + str(len(all_cameras)) + ' 个相机')
    except Exception as e:
        write_log('检查相机时出错: ' + str(e))
    
    # 导入并执行导出
    write_log('导入导出模块...')
    from CamFbxExport import export_all_cameras
    
    # 创建进度文件
    progress_file = os.path.join(r'%s', 'export_progress.txt')
    
    # 更新进度函数
    def update_progress(progress, message):
        try:
            with open(progress_file, 'w') as f:
                # 确保message是str类型
                if isinstance(message, unicode):
                    message = message.encode('utf-8')
                f.write(str(int(progress)) + '\\n' + str(message))
            write_log('进度: ' + str(progress) + '%%  - ' + str(message))
        except Exception as e:
            write_log('更新进度出错: ' + str(e))
    
    # 导出相机
    write_log('开始导出相机...')
    update_progress(10, '开始导出相机...')
    export_all_cameras(fbx_directory=r'%s', add_border_keys=True, 
                       maya_file_path=r'%s', use_underscore_index=use_underscore_index)
    update_progress(100, '导出完成')
    write_log('导出任务完成')
    
except Exception as e:
    error_trace = traceback.format_exc()
    write_log('发生错误: ' + str(e) + '\\n' + error_trace)
    sys.stderr.write('错误: ' + str(e) + '\\n' + error_trace + '\\n')
    sys.exit(1)
finally:
    write_log('关闭Maya独立模式...')
    # 关闭Maya
    try:
        maya.standalone.uninitialize()
        write_log('Maya独立模式已关闭')
    except:
        write_log('关闭Maya时出错')
""" % (safe_current_dir, safe_output_path, use_underscore_index, 
       str(load_references), str(load_references),
       safe_maya_file, safe_maya_file,
       str(load_references), safe_maya_file, safe_maya_file,
       safe_output_path, safe_output_path, safe_maya_file)
            
            temp_script = os.path.join(tempfile.gettempdir(), "temp_export_script.py")
            
            # 使用codecs模块打开文件以确保正确的编码处理
            with codecs.open(temp_script, "w", encoding="utf-8") as f:
                f.write(script_content)
            
            self.log("临时脚本创建完成: %s" % temp_script)
            
            # 创建进度文件
            if os.path.exists(progress_file):
                os.remove(progress_file)
                
            # 创建日志文件
            log_file = os.path.join(output_path, "export_log.txt")
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
            
            # 修改命令以更好地处理Unicode
            cmd = [
                mayapy, 
                "-c", 
                """# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.argv = ['mayapy', 'noautoload']

# 执行脚本
with open(r'%s', 'rb') as f:
    script_content = f.read()
    exec(script_content)
""" % temp_script
            ]
            
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
            self.timer.timeout.connect(lambda: self.check_progress(start_time, output_path, progress_file, log_file))
            self.timer.start(1000)  # 每秒检查一次
            
            # 进程信息记录到类变量
            self.temp_script = temp_script
            self.progress_file = progress_file
            
        except Exception as e:
            self.log(f"导出设置失败: {str(e)}")
            self.update_file_status("failed", "设置失败")
            
            # 安全地清理临时文件
            if temp_script and os.path.exists(temp_script):
                try:
                    os.remove(temp_script)
                    self.log("临时脚本已删除")
                except Exception as e:
                    self.log("无法删除临时文件 %s: %s" % (temp_script, str(e)))
            
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
            else:
                status_item = QTableWidgetItem(message)
                status_item.setForeground(QBrush(QColor("blue")))
                
            self.file_list.setItem(row, 1, status_item)
    
    def on_process_finished(self, exit_code, exit_status):
        """处理单个文件导出进程结束事件"""
        self.timer.stop()
        
        if exit_code == 0:
            self.log("文件导出成功")
            self.task_progress_bar.setValue(100)
            self.update_file_status("success")
        else:
            self.log(f"导出进程返回错误代码: {exit_code}")
            self.update_file_status("failed", f"代码: {exit_code}")
        
        # 安全地清理临时文件
        if hasattr(self, 'temp_script') and os.path.exists(self.temp_script):
            try:
                os.remove(self.temp_script)
                self.log("临时脚本已删除")
            except Exception as e:
                self.log(f"无法删除临时文件 {self.temp_script}: {str(e)}")
        
        # 清理进度文件
        if hasattr(self, 'progress_file') and os.path.exists(self.progress_file):
            try:
                os.remove(self.progress_file)
            except:
                pass
        
        # 如果导出过程仍在运行，处理下一个文件
        if self.export_running:
            # 继续处理下一个文件
            QTimer.singleShot(500, self.export_next_file)  # 延迟半秒再处理下一个文件
    
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
        # 检查超时
        if time.time() - start_time > 300:
            self.log("导出过程超时，中止任务")
            self.process.terminate()
            self.timer.stop()
            self.status_label.setText("导出失败：超时")
            self.status_label.setStyleSheet("color: red;")
            self.update_file_status("failed", "超时")
            
            # 继续下一个文件
            QTimer.singleShot(500, self.export_next_file)
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
    window = CameraExportWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
