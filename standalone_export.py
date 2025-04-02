# -*- coding: utf-8 -*-
import os
import sys
import subprocess
from pathlib import Path

class StandaloneExporter:
    def __init__(self):
        self.maya_location = self._get_maya_location()
        self.mayapy = self._get_mayapy_path()
        print("找到Maya路径: {}".format(self.maya_location))
        print("使用mayapy: {}".format(self.mayapy))
        
    def _get_maya_location(self):
        """获取Maya安装路径"""
        # Windows默认路径，可以通过配置文件来设置
        default_paths = [
            r"C:\Program Files\Autodesk\Maya2020",
            r"C:\Program Files\Autodesk\Maya2020-x64"
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                return path
        raise RuntimeError("找不到Maya 2020安装路径，请确保Maya 2020已正确安装")

    def _get_mayapy_path(self):
        """获取mayapy.exe的路径"""
        mayapy = os.path.join(self.maya_location, "bin", "mayapy.exe")
        if not os.path.exists(mayapy):
            raise RuntimeError("找不到mayapy: {}".format(mayapy))
        return mayapy

    def export_abc(self, maya_file, output_path, frame_range=None):
        """导出Alembic文件"""
        if not os.path.exists(maya_file):
            raise RuntimeError("Maya文件不存在: {}".format(maya_file))

        # 创建输出目录
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 设置默认帧范围
        start_frame = frame_range[0] if frame_range else 1
        end_frame = frame_range[1] if frame_range else 1

        # 构建Python命令
        python_cmd = """# -*- coding: utf-8 -*-
import maya.standalone
maya.standalone.initialize()
import maya.cmds as cmds
import os

try:
    # 打开Maya文件
    print("正在打开Maya文件...")
    cmds.file('{maya_file}', open=True, force=True)
    
    # 设置帧范围
    if {frame_range}:
        start_frame, end_frame = {frame_range}
        cmds.playbackOptions(minTime=start_frame, maxTime=end_frame)
    
    # 导出ABC
    print("正在导出ABC文件...")
    cmds.AbcExport(j='-frameRange {start_frame} {end_frame} -uvWrite -worldSpace -writeVisibility -dataFormat ogawa -file {output_path}')
    print("导出完成！")
    
except Exception as e:
    print("错误: " + str(e))
    raise e
finally:
    maya.standalone.uninitialize()
""".format(
            maya_file=maya_file.replace('\\', '/'),
            frame_range=frame_range,
            start_frame=start_frame,
            end_frame=end_frame,
            output_path=output_path.replace('\\', '/')
        )

        # 创建临时Python脚本
        temp_script = "temp_export_script.py"
        with open(temp_script, "w", encoding="utf-8") as f:
            f.write(python_cmd)

        try:
            # 执行导出命令
            cmd = [self.mayapy, temp_script]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
            
            # 打印输出
            if result.stdout:
                print(result.stdout)
            
            # 检查错误
            if result.returncode != 0:
                raise RuntimeError("导出失败: {}".format(result.stderr))
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_script):
                os.remove(temp_script)

    def _create_temp_script(self, maya_file, output_path, export_sets=None, frame_range=None):
        """创建临时的Python脚本文件"""
        temp_script = "temp_export_script.py"
        
        with open(temp_script, "w") as f:
            f.write("""
import maya.cmds as cmds
import singleExport

def main():
    # 设置输出路径
    output_path = '{}'
    
    # 创建导出器
    exporter = singleExport.SingleExport()
    
    # 设置帧范围
    {}
    
    # 设置导出对象
    {}
    
    # 设置输出路径
    exporter.setFilepath(output_path)
    
    # 执行导出
    exporter.duplicateObjects()
    exporter.exportFile()
    exporter.deleteDuplicateObjects()
    exporter.addFrameData()
    
    # 退出Maya
    cmds.quit(force=True)

if __name__ == '__main__':
    main()
""".format(
    output_path,
    f"exporter.setFramerange({frame_range[0]}, {frame_range[1]})" if frame_range else "exporter.setFramerange()",
    "exporter.getExportSets()" if export_sets else "exporter.getSelected()"
))
        
        return temp_script 