# -*- coding: utf-8 -*-
from PySide2.QtWidgets import *
from PySide2.QtCore import *
import sys
import os
import subprocess
import tempfile
import time
import codecs

class CameraExportWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Maya相机FBX导出工具")
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
        
        # 输出路径选择
        output_layout = QHBoxLayout()
        self.output_input = QLineEdit()
        output_btn = QPushButton("选择输出路径")
        output_btn.clicked.connect(self.select_output_path)
        output_layout.addWidget(QLabel("输出路径:"))
        output_layout.addWidget(self.output_input)
        output_layout.addWidget(output_btn)
        
        # 添加文件夹分隔设置选项
        folder_option_group = QGroupBox("子文件夹命名方式")
        folder_layout = QVBoxLayout()
        
        # 创建单选按钮组
        self.use_second_underscore = QRadioButton("使用第二个下划线前的字符")
        self.use_third_underscore = QRadioButton("使用第三个下划线前的字符")
        self.use_second_underscore.setChecked(True)  # 默认选中第二个下划线
        
        folder_layout.addWidget(self.use_second_underscore)
        folder_layout.addWidget(self.use_third_underscore)
        folder_option_group.setLayout(folder_layout)
        
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
        self.export_btn = QPushButton("导出相机")
        self.export_btn.clicked.connect(self.export)
        
        # 添加所有控件到主布局
        layout.addLayout(maya_file_layout)
        layout.addLayout(output_layout)
        layout.addWidget(folder_option_group)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(QLabel("操作日志:"))
        layout.addWidget(self.log_text)
        layout.addWidget(self.export_btn)
        
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
        
    def export(self):
        maya_file = self.maya_file_input.text()
        output_path = self.output_input.text()
        
        if not maya_file or not output_path:
            QMessageBox.warning(self, "错误", "请选择Maya文件和输出路径")
            return
            
        if not os.path.exists(maya_file):
            QMessageBox.warning(self, "错误", "Maya文件不存在")
            return
            
        # 获取选择的文件夹选项
        use_underscore_index = 2 if self.use_second_underscore.isChecked() else 3
        
        # 禁用导出按钮并显示进度条
        self.export_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.status_label.setText("正在导出...")
        self.status_label.setStyleSheet("color: blue;")
        
        # 清空日志区域
        self.log_text.clear()
        self.log("开始导出任务...")
        self.log("Maya文件: %s" % maya_file)
        self.log("输出路径: %s" % output_path)
        self.log("使用第%d个下划线前的字符作为子文件夹名称" % use_underscore_index)
        
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
        'loadReferenceDepth': 'none',  # 不加载引用
        'prompt': False,
        'loadNoReferences': True,      # 跳过所有引用
        'returnNewNodes': False        # 不返回新节点列表，提高性能
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
       safe_maya_file, safe_maya_file, safe_maya_file.replace('\\', '\\\\'),
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
            self.timer.timeout.connect(lambda: self.check_progress(start_time, output_path, progress_file, log_file))
            self.timer.start(1000)  # 每秒检查一次
            
            # 进程信息记录到类变量
            self.temp_script = temp_script
            self.progress_file = progress_file
            self.process_running = True
            
        except Exception as e:
            self.status_label.setText("导出失败")
            self.status_label.setStyleSheet("color: red;")
            self.log("导出失败: %s" % str(e))
            QMessageBox.critical(self, "错误", str(e))
            
            # 安全地清理临时文件
            if temp_script and os.path.exists(temp_script):
                try:
                    os.remove(temp_script)
                    self.log("临时脚本已删除")
                except Exception as e:
                    self.log("无法删除临时文件 %s: %s" % (temp_script, str(e)))
            
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
        # 检查超时
        if time.time() - start_time > 300:
            self.log("导出过程超时，中止任务")
            self.process.terminate()
            self.timer.stop()
            self.process_running = False
            self.status_label.setText("导出失败：超时")
            self.status_label.setStyleSheet("color: red;")
            self.export_btn.setEnabled(True)
            self.progress_bar.hide()
            QMessageBox.critical(self, "错误", "导出任务超时（5分钟）")
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
            QMessageBox.information(self, "成功", "相机导出完成！")
        else:
            self.log("导出进程返回错误代码: %s" % exit_code)
            self.status_label.setText("导出失败")
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.critical(self, "错误", "导出失败，返回代码：" + str(exit_code))
        
        # 安全地清理临时文件
        if hasattr(self, 'temp_script') and os.path.exists(self.temp_script):
            try:
                os.remove(self.temp_script)
                self.log("临时脚本已删除")
            except Exception as e:
                self.log("无法删除临时文件 %s: %s" % (self.temp_script, str(e)))
        
        # 清理进度文件
        if hasattr(self, 'progress_file') and os.path.exists(self.progress_file):
            try:
                os.remove(self.progress_file)
                self.log("进度文件已删除")
            except:
                pass
        
        # 恢复UI状态
        self.export_btn.setEnabled(True)
        self.progress_bar.hide()

def main():
    app = QApplication(sys.argv)
    window = CameraExportWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
