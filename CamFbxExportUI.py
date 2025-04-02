# -*- coding: utf-8 -*-
from PySide2.QtWidgets import *
from PySide2.QtCore import *
import sys
import os
import subprocess
import tempfile

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
        
        # 状态显示
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: green;")
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 设置为循环模式
        self.progress_bar.hide()
        
        # 信息显示区域
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMinimumHeight(100)
        self.info_text.hide()
        
        # 导出按钮
        self.export_btn = QPushButton("导出相机")
        self.export_btn.clicked.connect(self.export)
        
        # 添加所有控件到主布局
        layout.addLayout(maya_file_layout)
        layout.addLayout(output_layout)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.info_text)
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
            
    def show_info(self, message, is_error=False):
        """显示信息"""
        self.info_text.setPlainText(message)
        if is_error:
            self.info_text.setStyleSheet("color: black;")
        else:
            self.info_text.setStyleSheet("color: black;")
        self.info_text.show()
        self.info_text.verticalScrollBar().setValue(
            self.info_text.verticalScrollBar().maximum()
        )
            
    def export(self):
        maya_file = self.maya_file_input.text()
        output_path = self.output_input.text()
        
        if not maya_file or not output_path:
            QMessageBox.warning(self, "错误", "请选择Maya文件和输出路径")
            return
            
        if not os.path.exists(maya_file):
            QMessageBox.warning(self, "错误", "Maya文件不存在")
            return
            
        # 禁用导出按钮并显示进度条
        self.export_btn.setEnabled(False)
        self.progress_bar.show()
        self.status_label.setText("正在导出...")
        self.status_label.setStyleSheet("color: blue;")
        self.info_text.hide()
        
        try:
            # 获取当前脚本所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 创建临时Python脚本
            script_content = """# -*- coding: utf-8 -*-
import sys
import os

# 添加当前目录到Python路径
current_dir = r'%s'
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 设置Maya环境变量
os.environ['MAYA_SCRIPT_PATH'] = r'%s/scripts'
os.environ['MAYA_PLUG_IN_PATH'] = r'%s/plug-ins'
os.environ['MAYA_PREFERRED_PYTHON'] = '2.7'

# 初始化Maya独立模式
import maya.standalone
maya.standalone.initialize()

try:
    # 导入Maya命令
    import maya.cmds as cmds
    
    # 加载FBX插件
    if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
        cmds.loadPlugin('fbxmaya', quiet=True)
    
    # 打开Maya文件
    cmds.file(r'%s', open=True, force=True)
    
    # 导入并执行导出
    from CamFbxExport import export_all_cameras
    export_all_cameras(fbx_directory=r'%s', add_border_keys=True)
    
except Exception as e:
    sys.stderr.write("错误: " + str(e) + "\\n")
    sys.exit(1)
finally:
    # 关闭Maya
    maya.standalone.uninitialize()
""" % (current_dir, self.maya_path, self.maya_path, maya_file, output_path)
            
            temp_script = os.path.join(tempfile.gettempdir(), "temp_export_script.py")
            with open(temp_script, "w", encoding="utf-8") as f:
                f.write(script_content)
            
            # 使用mayapy执行导出
            mayapy = os.path.join(self.maya_path, "bin", "mayapy.exe")
            cmd = [mayapy, temp_script]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8"
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.status_label.setText("导出完成！")
                self.status_label.setStyleSheet("color: green;")
                success_msg = f"导出成功！\n\nMaya文件：{maya_file}\n输出路径：{output_path}\n\n详细信息：\n{stdout}"
                self.show_info(success_msg)
                QMessageBox.information(self, "成功", "相机导出完成！")
            else:
                error_msg = f"导出失败！\n\nMaya文件：{maya_file}\n输出路径：{output_path}\n\n错误信息：\n{stderr}"
                self.show_info(error_msg, True)
                self.status_label.setText("导出失败")
                self.status_label.setStyleSheet("color: red;")
                
        except Exception as e:
            error_msg = f"发生错误！\n\nMaya文件：{maya_file}\n输出路径：{output_path}\n\n错误信息：\n{str(e)}"
            self.show_info(error_msg, True)
            self.status_label.setText("导出失败")
            self.status_label.setStyleSheet("color: red;")
        finally:
            # 清理临时文件
            if os.path.exists(temp_script):
                os.remove(temp_script)
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