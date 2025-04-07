# -*- coding: utf-8 -*-

import functools
import os
import re
import tempfile
import sys

# 确保Python 2.7兼容的Unicode处理
try:
    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass

from maya import cmds, mel

def _find_cams(default=False):
    """Find cameras in the scene.

    Args:
        default (bool): show default cameras

    Returns:
        (Camera list): cameras
    """
    _cams = []
    try:
        all_cameras = cmds.ls(type='camera') or []
        print("查找到的相机数量: %d" % len(all_cameras))
        
        for _shp in all_cameras:
            try:
                # 防止listRelatives返回None
                _relatives = cmds.listRelatives(_shp, parent=True)
                if not _relatives:
                    print("相机 %s 没有父级节点，跳过" % _shp)
                    continue
                    
                _tfm = _relatives[0]
                if not default and _tfm in ['persp', 'top', 'front', 'side']:
                    continue
                _cam = _Camera(_tfm)
                _cams.append(_cam)
                print("添加相机: %s (形状节点: %s)" % (_tfm, _shp))
            except Exception as e:
                print("处理相机 %s 时出错: %s" % (_shp, str(e)))
                import traceback
                print(traceback.format_exc())
                continue
    except Exception as e:
        print("查找相机时出错: %s" % str(e))
        import traceback
        print(traceback.format_exc())
        
    return _cams

def _set_namespace(namespace, clean=False):
    """Set current namespace, creating it if required.

    Args:
        namespace (str): namespace to apply
        clean (bool): delete all nodes in this namespace
    """
    _namespace = namespace
    assert _namespace.startswith(':')

    if clean:
        _nodes = cmds.ls(_namespace+":*")
        if _nodes:
            cmds.delete(_nodes)

    if not cmds.namespace(exists=_namespace):
        cmds.namespace(addNamespace=_namespace)
    cmds.namespace(setNamespace=_namespace)
    
def _fbx_export_selection(fbx, range_, add_border_keys=True):
    """Execute fbx export of selected nodes.

    Args:
        fbx (str): path to export to
        range_ (tuple): export start/end range
        add_border_keys (bool): add start/end frame keys
    """
    _nodes = cmds.ls(selection=True)
    _start, _end = range_

    if add_border_keys:
        # 使用Python命令替代MEL命令
        for _node in _nodes:
            _attrs = cmds.listAttr(_node, keyable=True) or []
            for _attr in _attrs:
                if '.' in _attr:
                    continue
                _chan = '{}.{}'.format(_node, _attr)
                if not cmds.listConnections(
                        _chan, type='animCurve', destination=False):
                    continue
                cmds.setKeyframe(_chan, time=_start, insert=True)
                cmds.setKeyframe(_chan, time=_end, insert=True)

    _dir = os.path.dirname(fbx)
    if not os.path.exists(_dir):
        os.makedirs(_dir)

    # 使用Python命令设置FBX导出选项
    cmds.loadPlugin('fbxmaya', quiet=True)
    
    # 设置FBX导出选项
    cmds.file(fbx, force=True, options="v=0;", typ="FBX export", preserveReferences=True, exportSelected=True)
    
class _Exportable(object):
    """Base class for any exportable."""

    def export_fbx(self, fbx, range_, nodes=None, add_border_keys=True):
        """Export fbx to file.

        Args:
            fbx (str): path to export to
            range_ (tuple): start/end frames
            nodes (str list): override list of nodes to export
            add_border_keys (bool): add start/end frame keys
        """
        _nodes = nodes or self.find_nodes()
        cmds.select(_nodes)
        _fbx_export_selection(
            fbx=fbx, range_=range_, add_border_keys=add_border_keys)

    def __repr__(self):
        return '<{}:{}>'.format(type(self).__name__.strip('_'), self.name)
    
class _Camera(_Exportable):
    """Represents a camera in the current scene."""

    def __init__(self, tfm):
        """Constructor.

        Args:
            tfm (str): camera transform
        """
        self.tfm = tfm
        self.shp = cmds.listRelatives(self.tfm, shapes=True)[0]

    @property
    def name(self):
        """Get this cam's display name."""
        if ':' in self.tfm:
            return self.tfm.split(':')[0]
        return self.tfm

    def _unlock_attributes(self, node):
        """解锁节点的所有属性。

        Args:
            node (str): 节点名称
        """
        print("解锁节点属性: %s" % node)
        # 获取所有属性
        attrs = cmds.listAttr(node, keyable=True) or []
        print("找到 %d 个属性需要解锁" % len(attrs))
        for attr in attrs:
            try:
                # 检查属性是否被锁定
                if cmds.getAttr('{}.{}'.format(node, attr), lock=True):
                    # 解锁属性
                    cmds.setAttr('{}.{}'.format(node, attr), lock=False)
                # 设置为可关键帧
                cmds.setAttr('{}.{}'.format(node, attr), keyable=True)
            except Exception as e:
                print("无法解锁属性 %s.%s: %s" % (node, attr, str(e)))
                continue  # 忽略无法修改的属性

    def export_fbx_in_world_space(
        self, fbx, range_, add_border_keys=True, cleanup=True):
        """Export fbx of this canera in world space.

        Args:
            fbx (str): fbx path
            range_ (tuple): start/end frames
            add_border_keys (bool): add start/end frame keys
            cleanup (bool): clean tmp nodes
        """
        try:
            print("开始导出相机 %s 到 %s" % (self.name, fbx))
            print("设置临时命名空间...")
            _set_namespace(':export_tmp', clean=True)
            
            # 解锁相机和其形状节点的所有属性
            print("解锁相机属性...")
            self._unlock_attributes(self.tfm)
            self._unlock_attributes(self.shp)
            
            # 特别处理center of interest
            try:
                print("处理centerOfInterest属性...")
                if cmds.getAttr('{}.centerOfInterest'.format(self.shp), lock=True):
                    cmds.setAttr('{}.centerOfInterest'.format(self.shp), lock=False)
            except Exception as e:
                print("无法解锁centerOfInterest属性: %s" % str(e))

            # Create duplicate cam in world
            print("创建相机副本...")
            _dup = _Camera(cmds.duplicate(self.tfm)[0])
            print("创建的副本相机: %s" % _dup.tfm)
            if cmds.listRelatives(_dup.tfm, parent=True):
                print("将副本相机移至世界空间...")
                cmds.parent(_dup.tfm, world=True)
                
            # Drive dup cam by orig
            print("连接相机属性...")
            for _attr in cmds.listAttr(self.shp, keyable=True):
                _type = cmds.attributeQuery(
                    _attr, node=self.shp, attributeType=True)
                if _type in ['message']:
                    continue
                try:
                    cmds.connectAttr('{}.{}'.format(self.shp, _attr),
                                    '{}.{}'.format(_dup.shp, _attr))
                except Exception as e:
                    print("无法连接属性 %s.%s 到 %s.%s: %s" % (self.shp, _attr, _dup.shp, _attr, str(e)))
            
            print("创建约束...")
            _p_cons = cmds.parentConstraint(
                self.tfm, _dup.tfm, maintainOffset=False)[0]
            _s_cons = cmds.scaleConstraint(
                self.tfm, _dup.tfm, maintainOffset=False)[0]
        
            # Bake anim
            print("烘焙动画，范围: %s - %s..." % (range_[0], range_[1]))
            cmds.bakeResults([_dup.tfm, _dup.shp], time=range_)
         
            print("删除约束...")
            cmds.delete(_p_cons, _s_cons)
            print("导出FBX...")
            _dup.export_fbx(
                fbx=fbx, range_=range_, add_border_keys=add_border_keys)
            if cleanup:
                print("清理临时命名空间...")
                _set_namespace(':export_tmp', clean=True)
            _set_namespace(':')
            print("相机 %s 导出完成" % self.name)
        except Exception as e:
            print("导出相机 %s 时发生错误: %s" % (self.name, str(e)))
            import traceback
            print(traceback.format_exc())
            # 确保清理临时命名空间
            try:
                _set_namespace(':export_tmp', clean=True)
                _set_namespace(':')
            except:
                pass
            raise
    
    def find_nodes(self):
        """Get nodes in this camera.

        Returns:
            (str list): list of nodes
        """
        return [self.tfm, self.shp]
    
def export_all_cameras(fbx_directory, add_border_keys=True, maya_file_path=None):
    """Export all cameras in the scene to FBX files with the current timeline range.
    
    Args:
        fbx_directory (str): 输出目录路径
        add_border_keys (bool): 是否添加首尾关键帧
        maya_file_path (str): Maya文件路径，用于命名输出文件夹
    """
    
    try:
        # 获取Maya文件名用于命名文件夹
        if maya_file_path:
            # 使用传入的Maya文件路径
            scene_name = os.path.splitext(os.path.basename(maya_file_path))[0]
            print("使用输入文件名: %s" % scene_name)
        else:
            # 尝试从当前场景获取名称
            scene_path = cmds.file(q=True, sceneName=True)
            if scene_path:
                scene_name = os.path.splitext(os.path.basename(scene_path))[0]
            else:
                # 如果都失败，使用时间戳
                import datetime
                scene_name = "export_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                print("场景未命名，使用时间戳: %s" % scene_name)
        
        print("导出文件夹将使用名称: %s" % scene_name)
        
        # 创建以文件名命名的目录
        export_dir = os.path.join(fbx_directory, scene_name)
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        print("创建导出目录: %s" % export_dir)
        
        # 获取当前时间轴的起始和结束帧
        start_frame = cmds.playbackOptions(q=True, min=True)
        end_frame = cmds.playbackOptions(q=True, max=True)
        range_ = (start_frame, end_frame)
        print("导出帧范围: %s - %s" % (start_frame, end_frame))
        
        # 获取所有相机
        print("开始查找场景中的相机...")
        _cams = _find_cams(default=False)
        print("找到 %d 个非默认相机" % len(_cams))
        
        if not _cams:
            print("未找到非默认相机，尝试包含默认相机...")
            _cams = _find_cams(default=True)
            print("包含默认相机后找到 %d 个相机" % len(_cams))
            
        if not _cams:
            print("未找到任何相机，创建默认测试相机...")
            try:
                # 创建一个测试相机
                cam_name = "export_test_CAM"
                cam_transform = cmds.camera(name=cam_name)[0]
                print("创建测试相机: %s" % cam_transform)
                _cams = [_Camera(cam_transform)]
            except Exception as e:
                print("创建测试相机失败: %s" % str(e))
                print("无法继续导出")
                return
        
        # 计算需要导出的相机数量
        # 首先查找以_CAM结尾的相机
        cam_suffix = '_CAM'
        exportable_cams = [cam for cam in _cams if cam.name.endswith(cam_suffix)]
        
        # 如果没有找到以_CAM结尾的相机，尝试导出所有非默认相机
        if not exportable_cams:
            print("未找到以'%s'结尾的相机，尝试导出所有非默认相机" % cam_suffix)
            exportable_cams = [cam for cam in _cams if cam.name not in ['persp', 'top', 'front', 'side']]
        
        # 如果仍然没有，就导出所有相机包括默认相机
        if not exportable_cams:
            print("未找到任何非默认相机，导出所有相机包括默认相机")
            exportable_cams = _cams
        
        total_cams = len(exportable_cams)
        print("找到 %d 个可导出的相机" % total_cams)
        
        if total_cams == 0:
            print("未找到可导出的相机")
            return
        
        # 对指定相机进行导出
        for i, cam in enumerate(exportable_cams):
            # 获取相机的名称
            camera_name = cam.name
            print("\n正在处理相机 (%d/%d): %s" % (i+1, total_cams, camera_name))
            
            # 更新进度
            progress = 10 + int(80 * (i / total_cams))  # 10-90%的进度
            progress_file = os.path.join(fbx_directory, "export_progress.txt")
            try:
                with open(progress_file, 'w') as f:
                    message = "正在导出相机: " + camera_name
                    # 确保message是str类型
                    if isinstance(message, unicode):
                        message = message.encode('utf-8')
                    f.write(str(int(progress)) + "\n" + message)
                print("更新进度: %s%% - %s" % (progress, message))
            except Exception as e:
                print("更新进度文件时出错: %s" % str(e))
            
            # 定义导出文件路径（直接在以当前文件名命名的目录中）
            fbx_filepath = os.path.join(export_dir, "{}.fbx".format(camera_name))
            fbx_filepath = fbx_filepath.replace("\\", "/")  # 替换为正斜杠
            print("导出路径: %s" % fbx_filepath)

            # 调用相机的导出函数
            print("开始导出相机 %s 到 %s" % (camera_name, fbx_filepath))
            cam.export_fbx_in_world_space(fbx=fbx_filepath, range_=range_, add_border_keys=add_border_keys)
            
            print("已导出相机: %s" % camera_name)
        
        print("\n所有相机导出完成!")
    except Exception as e:
        print("导出相机时发生错误: %s" % str(e))
        import traceback
        print(traceback.format_exc())
        raise



