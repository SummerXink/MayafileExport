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
        layout.addWidget(self.apply_shader_to_faces)
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
            
        # 获取Maya文件名作为子文件夹名称（不含路径和扩展名）
        maya_file_basename = os.path.basename(maya_file)
        maya_file_name = os.path.splitext(maya_file_basename)[0]
        subfolder_path = os.path.join(output_path, maya_file_name)
        
        self.log("Maya文件名: %s" % maya_file_basename)
        self.log("将创建子文件夹: %s" % subfolder_path)
        
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
        self.log("将材质指定到面上: %s" % ("是" if apply_shader else "否"))
        
        # 初始化临时文件路径变量
        temp_script = None
        progress_file = os.path.join(subfolder_path, "export_progress.txt")
        
        try:
            # 获取当前脚本所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.log("当前脚本目录: %s" % current_dir)
            
            # 创建临时Python脚本
            self.log("正在创建临时导出脚本...")
            
            # 使用一种完全避免任何格式化字符冲突的方式
            safe_current_dir = current_dir.replace('\\', '\\\\')  # 确保路径转义正确
            safe_output_path = output_path.replace('\\', '\\\\')
            safe_subfolder_path = subfolder_path.replace('\\', '\\\\')
            safe_maya_file = maya_file.replace('\\', '\\\\')
            safe_maya_file_name = maya_file_name.replace('\\', '\\\\')
            namespaces_str = ",".join(namespaces)
            safe_namespaces = namespaces_str.replace('\\', '\\\\')
            
            script_lines = [
                "# -*- coding: utf-8 -*-",
                "import sys",
                "import os",
                "import time",
                "import traceback",
                "",
                "# 确保Python 2.7兼容的Unicode处理",
                "reload(sys)",
                "sys.setdefaultencoding('utf-8')",
                "",
                "# 添加当前目录到Python路径",
                "current_dir = r'" + safe_current_dir + "'",
                "if current_dir not in sys.path:",
                "    sys.path.append(current_dir)",
                "",
                "# 创建子文件夹",
                "subfolder_path = os.path.join(r'" + safe_output_path + "', r'" + safe_maya_file_name + "')",
                "if not os.path.exists(subfolder_path):",
                "    os.makedirs(subfolder_path)",
                "",
                "# 创建日志文件",
                "log_file = os.path.join(subfolder_path, 'export_log.txt')",
                "def write_log(message):",
                "    with open(log_file, 'a') as f:",
                "        current_time = time.strftime('%Y-%m-%d %H:%M:%S')",
                "        f.write('[' + current_time + '] ' + message + '\\n')",
                "",
                "write_log('开始初始化Maya独立模式...')",
                "write_log('将导出到子文件夹: ' + subfolder_path)",
                "",
                "try:",
                "    # 初始化Maya独立模式",
                "    import maya.standalone",
                "    # 设置环境变量以禁用自动插件加载",
                "    import os",
                "    os.environ['MAYA_DISABLE_PLUGINS'] = '1'",
                "    os.environ['MAYA_DISABLE_CIP'] = '1'  # 禁用客户参与计划",
                "    os.environ['MAYA_DISABLE_CER'] = '1'  # 禁用崩溃报告",
                "    # 禁用插件路径",
                "    os.environ['MAYA_PLUG_IN_PATH'] = ''",
                "    # 初始化Maya",
                "    write_log('使用无UI模式初始化Maya...')",
                "    maya.standalone.initialize(name='python')",
                "    write_log('Maya独立模式初始化完成')",
                "",
                "    # 导入Maya命令",
                "    import maya.cmds as cmds",
                "    import maya.mel as mel",
                "",
                "    # 加载必要的插件",
                "    write_log('检查插件状态...')",
                "    try:",
                "        loaded_plugins = cmds.pluginInfo(query=True, listPlugins=True) or []",
                "        write_log('当前加载的插件: ' + str(loaded_plugins))",
                "        ",
                "        # 确保AbcExport插件加载",
                "        write_log('加载AbcExport插件...')",
                "        if not 'AbcExport.mll' in loaded_plugins:",
                "            cmds.loadPlugin('AbcExport', quiet=True)",
                "            write_log('AbcExport插件加载成功')",
                "        else:",
                "            write_log('AbcExport插件已加载')",
                "    except Exception as e:",
                "        write_log('处理插件时出错: ' + str(e))",
                "",
                "    # 禁用所有插件的自动加载",
                "    cmds.optionVar(intValue=['autoLoadPlugins', 0])",
                "    # 设置其他选项以提高稳定性",
                "    cmds.optionVar(intValue=['CIP', 0])  # 禁用客户参与计划",
                "    cmds.optionVar(intValue=['CER', 0])  # 禁用崩溃报告",
                "",
                "    # 打开Maya文件",
                "    write_log('打开Maya文件...')",
                "    # 禁用自动加载插件",
                "    cmds.optionVar(intValue=['autoLoadPlugins', 0])",
                "    ",
                "    # 创建新的空场景",
                "    write_log('创建新场景...')",
                "    cmds.file(new=True, force=True)",
                "    ",
                "    # 禁用渲染器和绘图更新，提高稳定性",
                "    try:",
                "        cmds.optionVar(intValue=('renderSetupEnable', 0))  # 禁用渲染设置",
                "        try:",
                "            cmds.modelEditor('modelPanel4', edit=True, displayAppearance='wireframe') # 使用线框模式",
                "        except:",
                "            pass # 忽略没有UI时的错误",
                "    except Exception as e:",
                "        write_log('设置渲染选项时出错(可忽略): ' + str(e))",
                "    ",
                "    # 设置MEL变量以忽略特定类型的插件错误",
                "    mel.eval('global string $gMayaIgnoredWarnings[];')",
                "    mel.eval('$gMayaIgnoredWarnings[size($gMayaIgnoredWarnings)] = \"Unable to dynamically load\";')", 
                "    mel.eval('$gMayaIgnoredWarnings[size($gMayaIgnoredWarnings)] = \"Redshift\";')",
                "    mel.eval('$gMayaIgnoredWarnings[size($gMayaIgnoredWarnings)] = \"rsMaterial\";')",
                "    mel.eval('$gMayaIgnoredWarnings[size($gMayaIgnoredWarnings)] = \"The shadingEngine\";')",
                "    ",
                "    # 设置更安全的文件加载选项",
                "    file_options = {",
                "        'open': True,",
                "        'force': True,",
                "        'ignoreVersion': True,",
                "        'loadReferenceDepth': 'none',  # 不加载引用",
                "        'prompt': False,",
                "        'loadNoReferences': True,      # 跳过所有引用",
                "        'returnNewNodes': False        # 不返回新节点列表，提高性能",
                "    }",
                "",
                "    write_log('尝试打开文件: ' + r'" + safe_maya_file + "')",
                "    # 尝试加载文件, 忽略未知节点错误",
                "    file_open_success = False",
                "    try:",
                "        cmds.file(r'" + safe_maya_file + "', **file_options)",
                "        write_log('Maya文件已成功打开')",
                "        file_open_success = True",
                "    except Exception as e:",
                "        error_msg = str(e)",
                "        write_log('打开文件时出现错误，尝试替代方法: ' + error_msg)",
                "        # 尝试用MEL命令打开",
                "        try:",
                "            write_log('使用MEL命令尝试打开文件...')",
                "            mel.eval('setConstructionHistory(false);')",
                "            mel.eval('file -open -force -ignoreVersion -prompt false -loadNoReferences \"' + r'" + safe_maya_file.replace('\\', '\\\\') + "' + '\";')",
                "            write_log('使用MEL命令打开文件成功')",
                "            file_open_success = True",
                "        except Exception as e2:",
                "            write_log('使用MEL命令打开文件失败: ' + str(e2))",
                "            write_log('将继续尝试导出，但可能不成功')",
                "",
                "    # 创建进度文件",
                "    progress_file = os.path.join(subfolder_path, 'export_progress.txt')",
                "    ",
                "    # 更新进度函数",
                "    def update_progress(progress, message):",
                "        try:",
                "            with open(progress_file, 'w') as f:",
                "                # 确保message是str类型",
                "                if isinstance(message, unicode):",
                "                    message = message.encode('utf-8')",
                "                f.write(str(int(progress)) + '\\n' + str(message))",
                "            write_log('进度: ' + str(progress) + '% - ' + str(message))",
                "        except Exception as e:",
                "            write_log('更新进度出错: ' + str(e))",
                "",
                "    # 辅助函数：检查对象是否可见（包括父级层次）",
                "    def is_object_visible(obj_path):",
                "        # 检查自身可见性",
                "        if not cmds.objExists(obj_path + '.visibility'):",
                "            return True  # 如果没有visibility属性，默认为可见",
                "        ",
                "        if not cmds.getAttr(obj_path + '.visibility'):",
                "            return False",
                "        ",
                "        # 检查父级可见性",
                "        parent = cmds.listRelatives(obj_path, parent=True, fullPath=True)",
                "        if parent:",
                "            return is_object_visible(parent[0])",
                "        return True",
                "",
                "    # 导入模块",
                "    try:",
                "        write_log('导入导出相关模块...')",
                "        import renameShadingGroup",
                "        import setShadersTool",
                "        import singleExport",
                "        import alembicExport",
                "        write_log('模块导入成功')",
                "    except Exception as e:",
                "        write_log('导入模块失败: ' + str(e))",
                "        raise",
                "",
                "    # 开始导出过程",
                "    update_progress(10, '开始筛选场景对象...')",
                "",
                "    # 获取命名空间过滤条件",
                "    namespaces = ['" + "', '".join(namespaces) + "']",
                "    write_log('使用命名空间筛选: ' + str(namespaces))",
                "",
                "    # 筛选场景中符合条件的对象",
                "    all_objects = cmds.ls(long=True)",
                "    filtered_namespaces = set()",
                "",
                "    # 筛选命名空间",
                "    for obj in all_objects:",
                "        if ':' in obj:",
                "            ns = obj.split(':')[0]",
                "            for filter_ns in namespaces:",
                "                if filter_ns in ns:",
                "                    filtered_namespaces.add(ns)",
                "                    break",
                "",
                "    write_log('找到匹配的命名空间: ' + str(list(filtered_namespaces)))",
                "",
                "    # 按命名空间查找cache组",
                "    found_cache_groups = {}",
                "    for ns in filtered_namespaces:",
                "        cache_path = ns + ':cache'",
                "        if cmds.objExists(cache_path):",
                "            write_log('找到cache组: ' + cache_path)",
                "            ",
                "            # 检查cache组是否可见",
                "            if not is_object_visible(cache_path):",
                "                write_log('警告: cache组 ' + cache_path + ' 不可见，将跳过')",
                "                continue",
                "                ",
                "            # 获取cache下的子对象（仅非隐藏的）",
                "            children = []",
                "            hidden_children = []",
                "            try:",
                "                children_list = cmds.listRelatives(cache_path, children=True, fullPath=True) or []",
                "                write_log('cache组 ' + cache_path + ' 下有 ' + str(len(children_list)) + ' 个子对象')",
                "                ",
                "                for child in children_list:",
                "                    # 检查对象是否是变换节点",
                "                    if cmds.objectType(child) != 'transform':",
                "                        continue",
                "                        ",
                "                    # 递归检查对象及其父级的可见性",
                "                    if is_object_visible(child):",
                "                        children.append(child)",
                "                        write_log('添加可见对象: ' + child)",
                "                    else:",
                "                        hidden_children.append(child)",
                "                        write_log('跳过隐藏对象: ' + child)",
                "            except Exception as e:",
                "                write_log('获取子对象时出错: ' + str(e))",
                "",
                "            if children:",
                "                found_cache_groups[ns] = {",
                "                    'cache_path': cache_path,",
                "                    'children': children",
                "                }",
                "                write_log('命名空间 ' + ns + ' 下找到 ' + str(len(children)) + ' 个可见对象, 跳过 ' + str(len(hidden_children)) + ' 个隐藏对象')",
                "            else:",
                "                write_log('命名空间 ' + ns + ' 下没有可见对象，将跳过')",
                "",
                "    if not found_cache_groups:",
                "        write_log('未找到符合条件的cache组！')",
                "        update_progress(100, '未找到符合条件的对象，导出终止')",
                "        sys.exit(1)",
                "",
                "    write_log('找到 ' + str(len(found_cache_groups)) + ' 个符合条件的cache组')",
                "    update_progress(20, '找到 ' + str(len(found_cache_groups)) + ' 个符合条件的cache组')",
                "",
                "    # 获取当前时间轴范围",
                "    start_frame = cmds.playbackOptions(q=True, min=True)",
                "    end_frame = cmds.playbackOptions(q=True, max=True)",
                "    write_log('帧范围: ' + str(start_frame) + ' - ' + str(end_frame))",
                "",
                "    # 遍历每个cache组进行导出",
                "    total_groups = len(found_cache_groups)",
                "    current_group = 0",
                "    total_exported_objects = 0",
                "",
                "    for ns, data in found_cache_groups.items():",
                "        current_group += 1",
                "        group_progress = 20 + (current_group * 80 / total_groups)",
                "        update_progress(group_progress, '正在处理 (' + str(current_group) + '/' + str(total_groups) + '): ' + ns)",
                "        write_log('开始处理: ' + ns)",
                "",
                "        try:",
                "            cache_path = data['cache_path']",
                "            children = data['children']",
                "",
                "            if not children:",
                "                write_log('警告: ' + cache_path + ' 下没有可见子对象，跳过')",
                "                continue",
                "",
                "            # 将材质指定到面上",
                "            if " + ("True" if apply_shader else "False") + ":",
                "                write_log('正在将材质指定到面上...')",
                "                try:",
                "                    # 选择所有子对象",
                "                    cmds.select(children, replace=True)",
                "                    # 使用setShadersTool将材质指定到面上",
                "                    setShadersTool.SetShader()",
                "                    write_log('材质指定到面上成功')",
                "                except Exception as e:",
                "                    write_log('将材质指定到面上时出错: ' + str(e))",
                "",
                "            # 创建输出文件路径到子文件夹",
                "            file_name = ns.replace(':', '_') + '.abc'",
                "            abc_file_path = os.path.join(subfolder_path, file_name)",
                "",
                "            # 导出ABC",
                "            write_log('正在导出: ' + abc_file_path)",
                "            try:",
                "                # 选择所有子对象",
                "                cmds.select(children, replace=True)",
                "                # 使用singleExport导出",
                "                singleExport.SingleExport.exportSelection(abc_file_path, start_frame, end_frame)",
                "                write_log('导出成功: ' + abc_file_path)",
                "                total_exported_objects += len(children)",
                "            except Exception as e:",
                "                write_log('导出ABC时出错: ' + str(e))",
                "                write_log(traceback.format_exc())",
                "",
                "        except Exception as e:",
                "            write_log('处理 ' + ns + ' 时出错: ' + str(e))",
                "            write_log(traceback.format_exc())",
                "",
                "    write_log('导出统计：总共导出 ' + str(total_exported_objects) + ' 个对象，共 ' + str(len(found_cache_groups)) + ' 个命名空间')",
                "    update_progress(100, '所有ABC导出完成！')",
                "    write_log('所有ABC导出完成！')",
                "",
                "except Exception as e:",
                "    error_trace = traceback.format_exc()",
                "    write_log('发生错误: ' + str(e) + '\\n' + error_trace)",
                "    sys.stderr.write('错误: ' + str(e) + '\\n' + error_trace + '\\n')",
                "    sys.exit(1)",
                "finally:",
                "    write_log('关闭Maya独立模式...')",
                "    # 关闭Maya",
                "    try:",
                "        maya.standalone.uninitialize()",
                "        write_log('Maya独立模式已关闭')",
                "    except:",
                "        write_log('关闭Maya时出错')"
            ]
            
            script_content = "\n".join(script_lines)
            
            temp_script = os.path.join(tempfile.gettempdir(), "temp_abc_export_script.py")
            
            # 使用codecs模块打开文件以确保正确的编码处理
            with codecs.open(temp_script, "w", encoding="utf-8") as f:
                f.write(script_content)
            
            self.log("临时脚本创建完成: %s" % temp_script)
            
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
            
            # 修改命令以更好地处理Unicode
            cmd = [
                mayapy, 
                "-c", 
                "# -*- coding: utf-8 -*-\n"
                "import sys\n"
                "reload(sys)\n"
                "sys.setdefaultencoding('utf-8')\n"
                "sys.argv = ['mayapy', 'noautoload']\n"
                "exec(open(r'%s', 'rb').read())" % temp_script
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
            self.timer.timeout.connect(lambda: self.check_progress(start_time, subfolder_path, progress_file, log_file))
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
    window = ABCExportWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 