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

def _is_referenced(node):
    """检查节点是否是引用节点
    
    Args:
        node (str): 节点名称
        
    Returns:
        bool: 是否为引用节点
    """
    try:
        return cmds.referenceQuery(node, isNodeReferenced=True)
    except:
        return False

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
        
        # 添加常见的transform属性确保解锁
        transform_attrs = ['translate', 'translateX', 'translateY', 'translateZ', 
                         'rotate', 'rotateX', 'rotateY', 'rotateZ',
                         'scale', 'scaleX', 'scaleY', 'scaleZ',
                         'visibility']
        
        # 确保这些属性也被处理，即使不在keyable列表中
        for attr in transform_attrs:
            if attr not in attrs and cmds.attributeQuery(attr, node=node, exists=True):
                attrs.append(attr)
                
        for attr in attrs:
            try:
                # 先检查属性是否存在
                if not cmds.attributeQuery(attr, node=node, exists=True):
                    continue
                    
                # 检查属性是否被锁定
                try:
                    is_locked = cmds.getAttr('{}.{}'.format(node, attr), lock=True)
                except:
                    continue  # 如果无法获取锁定状态，跳过
                    
                if is_locked:
                    # 解锁属性
                    cmds.setAttr('{}.{}'.format(node, attr), lock=False)
                    print("解锁属性: %s.%s" % (node, attr))
                    
                # 设置为可关键帧
                try:
                    cmds.setAttr('{}.{}'.format(node, attr), keyable=True)
                except:
                    pass  # 忽略设置keyable失败
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
            
            # 检查相机是否为引用节点
            is_ref_cam = _is_referenced(self.tfm) or _is_referenced(self.shp)
            if is_ref_cam:
                print("检测到引用相机，需要特殊处理")
            
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
            # 如果是引用相机，使用不同的复制方法
            if is_ref_cam:
                print("使用特殊方法复制引用相机...")
                try:
                    # 创建一个全新的相机
                    new_cam_shape = cmds.camera()[0]
                    new_cam_tfm = cmds.listRelatives(new_cam_shape, parent=True)[0]
                    
                    # 重命名为与原相机相似的名称
                    new_cam_tfm = cmds.rename(new_cam_tfm, "export_tmp:" + self.tfm.split(":")[-1])
                    new_cam_shape = cmds.listRelatives(new_cam_tfm, shapes=True)[0]
                    
                    _dup = _Camera(new_cam_tfm)
                    print("创建引用相机副本: %s" % _dup.tfm)
                except Exception as e:
                    print("特殊方法创建相机失败，回退到标准方法: %s" % str(e))
                    _dup = _Camera(cmds.duplicate(self.tfm)[0])
            else:
                _dup = _Camera(cmds.duplicate(self.tfm)[0])
                
            print("创建的副本相机: %s" % _dup.tfm)
            if cmds.listRelatives(_dup.tfm, parent=True):
                print("将副本相机移至世界空间...")
                cmds.parent(_dup.tfm, world=True)
            
            # 确保复制的相机也完全解锁
            print("解锁复制相机的属性...")
            self._unlock_attributes(_dup.tfm)
            self._unlock_attributes(_dup.shp)
            
            # 额外解锁可能用于约束的属性
            for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
                try:
                    cmds.setAttr('{}.{}'.format(_dup.tfm, attr), lock=False)
                except Exception as e:
                    print("无法解锁约束所需属性 %s.%s: %s" % (_dup.tfm, attr, str(e)))
                
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
            # 尝试确保不会有连接问题
            try:
                # 检查是否有父级约束
                existing_constraints = cmds.listConnections(_dup.tfm, type="constraint")
                if existing_constraints:
                    print("检测到现有的约束，尝试删除...")
                    cmds.delete(existing_constraints)
                
                # 断开可能阻止约束的连接
                for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
                    connections = cmds.listConnections('{}.{}'.format(_dup.tfm, attr), 
                                                     source=True, destination=False, plugs=True)
                    if connections:
                        for connection in connections:
                            print("断开现有连接: %s -> %s.%s" % (connection, _dup.tfm, attr))
                            cmds.disconnectAttr(connection, '{}.{}'.format(_dup.tfm, attr))
            except Exception as e:
                print("处理现有连接时出错: %s" % str(e))
            
            # 使用try-except来分别创建约束，如果失败可以单独处理
            try:
                _p_cons = cmds.parentConstraint(
                    self.tfm, _dup.tfm, maintainOffset=False)[0]
                print("创建父级约束成功: %s" % _p_cons)
            except Exception as e:
                print("创建父级约束失败，尝试替代方法: %s" % str(e))
                try:
                    # 尝试直接连接位置和旋转属性
                    for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                        src_attr = '{}.{}'.format(self.tfm, attr)
                        dst_attr = '{}.{}'.format(_dup.tfm, attr)
                        if not cmds.isConnected(src_attr, dst_attr):
                            cmds.connectAttr(src_attr, dst_attr, force=True)
                    _p_cons = None
                except Exception as e2:
                    print("替代连接方法也失败: %s" % str(e2))
                    _p_cons = None
            
            try:
                _s_cons = cmds.scaleConstraint(
                    self.tfm, _dup.tfm, maintainOffset=False)[0]
                print("创建缩放约束成功: %s" % _s_cons)
            except Exception as e:
                print("创建缩放约束失败，尝试替代方法: %s" % str(e))
                try:
                    # 尝试直接连接缩放属性
                    for attr in ['sx', 'sy', 'sz']:
                        src_attr = '{}.{}'.format(self.tfm, attr)
                        dst_attr = '{}.{}'.format(_dup.tfm, attr)
                        if not cmds.isConnected(src_attr, dst_attr):
                            cmds.connectAttr(src_attr, dst_attr, force=True)
                    _s_cons = None
                except Exception as e2:
                    print("替代连接方法也失败: %s" % str(e2))
                    _s_cons = None
        
            # Bake anim
            print("烘焙动画，范围: %s - %s..." % (range_[0], range_[1]))
            cmds.bakeResults([_dup.tfm, _dup.shp], time=range_)
         
            print("删除约束...")
            if _p_cons:
                cmds.delete(_p_cons)
            if _s_cons:
                cmds.delete(_s_cons)
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
    
    def export_fbx_simple(self, fbx, range_, add_border_keys=True):
        """使用简化方法导出相机FBX，不使用约束，直接烘焙原始相机的位置。
        
        Args:
            fbx (str): fbx导出路径
            range_ (tuple): 动画范围
            add_border_keys (bool): 是否添加首尾关键帧
        """
        try:
            print("使用简化方法导出相机 %s 到 %s" % (self.name, fbx))
            
            # 创建导出目录
            _dir = os.path.dirname(fbx)
            if not os.path.exists(_dir):
                os.makedirs(_dir)
                
            # 选择原始相机
            cmds.select([self.tfm, self.shp], replace=True)
            print("已选择相机: %s, %s" % (self.tfm, self.shp))
            
            # 直接导出FBX
            _fbx_export_selection(fbx=fbx, range_=range_, add_border_keys=add_border_keys)
            print("简化方法导出完成")
            return True
        except Exception as e:
            print("简化方法导出相机失败: %s" % str(e))
            import traceback
            print(traceback.format_exc())
            return False

def export_all_cameras(fbx_directory, add_border_keys=True, maya_file_path=None, use_underscore_index=2):
    """Export all cameras in the scene to FBX files with the current timeline range.
    
    Args:
        fbx_directory (str): 输出目录路径
        add_border_keys (bool): 是否添加首尾关键帧
        maya_file_path (str): Maya文件路径，用于命名输出文件夹
        use_underscore_index (int): 使用第几个下划线前的字符作为子文件夹名称（默认为2）
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
        
        # 创建子文件夹名称 (使用第N个下划线前的部分)
        parts = scene_name.split('_')
        if len(parts) > use_underscore_index:
            # 有足够的下划线，取到第N个下划线前的部分
            subfolder_name = '_'.join(parts[:use_underscore_index])
        else:
            # 如果下划线不足，使用整个名称
            subfolder_name = scene_name
            
        print("子文件夹名称: %s" % subfolder_name)
        
        # 创建子文件夹路径
        subfolder_path = os.path.join(fbx_directory, subfolder_name)
        if not os.path.exists(subfolder_path):
            os.makedirs(subfolder_path)
        print("创建子文件夹: %s" % subfolder_path)
        
        # 创建子子文件夹路径 (使用完整的文件名)
        export_dir = os.path.join(subfolder_path, scene_name)
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        print("创建子子文件夹: %s" % export_dir)
        
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
            # 首先尝试标准导出方法
            try:
                cam.export_fbx_in_world_space(fbx=fbx_filepath, range_=range_, add_border_keys=add_border_keys)
                print("标准方法导出相机成功: %s" % camera_name)
            except Exception as e:
                print("标准方法导出相机 %s 失败: %s" % (camera_name, str(e)))
                print("尝试使用简化方法导出...")
                # 尝试使用简化方法导出
                if cam.export_fbx_simple(fbx=fbx_filepath, range_=range_, add_border_keys=add_border_keys):
                    print("简化方法导出相机成功: %s" % camera_name)
                else:
                    print("所有导出方法都失败，无法导出相机: %s" % camera_name)
            
            print("已导出相机: %s" % camera_name)
        
        print("\n所有相机导出完成!")
    except Exception as e:
        print("导出相机时发生错误: %s" % str(e))
        import traceback
        print(traceback.format_exc())
        raise



