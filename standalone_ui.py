# -*- coding: utf-8 -*-
from PySide2.QtWidgets import *
from PySide2.QtCore import *
import sys
from standalone_export import StandaloneExporter

class ExportWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Maya ABC导出工具")
        self.setup_ui()
        
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
        
        # 帧范围设置
        frame_range_layout = QHBoxLayout()
        self.start_frame = QSpinBox()
        self.end_frame = QSpinBox()
        self.start_frame.setRange(-999999, 999999)
        self.end_frame.setRange(-999999, 999999)
        frame_range_layout.addWidget(QLabel("开始帧:"))
        frame_range_layout.addWidget(self.start_frame)
        frame_range_layout.addWidget(QLabel("结束帧:"))
        frame_range_layout.addWidget(self.end_frame)
        
        # 状态显示
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: green;")
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 设置为循环模式
        self.progress_bar.hide()
        
        # 导出按钮
        self.export_btn = QPushButton("导出")
        self.export_btn.clicked.connect(self.export)
        
        # 添加所有控件到主布局
        layout.addLayout(maya_file_layout)
        layout.addLayout(output_layout)
        layout.addLayout(frame_range_layout)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
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
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "选择输出路径",
            "",
            "Alembic Files (*.abc)"
        )
        if file_name:
            if not file_name.lower().endswith('.abc'):
                file_name += '.abc'
            self.output_input.setText(file_name)
            
    def export(self):
        maya_file = self.maya_file_input.text()
        output_path = self.output_input.text()
        
        if not maya_file or not output_path:
            QMessageBox.warning(self, "错误", "请选择Maya文件和输出路径")
            return
            
        # 禁用导出按钮并显示进度条
        self.export_btn.setEnabled(False)
        self.progress_bar.show()
        self.status_label.setText("正在导出...")
        self.status_label.setStyleSheet("color: blue;")
        
        try:
            exporter = StandaloneExporter()
            exporter.export_abc(
                maya_file,
                output_path,
                frame_range=(self.start_frame.value(), self.end_frame.value())
            )
            self.status_label.setText("导出完成！")
            self.status_label.setStyleSheet("color: green;")
            QMessageBox.information(self, "成功", "导出完成！")
        except Exception as e:
            self.status_label.setText("导出失败")
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.critical(self, "错误", f"导出失败：{str(e)}")
        finally:
            # 恢复UI状态
            self.export_btn.setEnabled(True)
            self.progress_bar.hide()

def main():
    app = QApplication(sys.argv)
    window = ExportWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 