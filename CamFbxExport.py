# -*- coding: utf-8 -*-

import functools
import os
import re
import tempfile

from maya import cmds, mel
from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtCore import Qt

OutputPath = 'P:/projects/TBX2/person/zwx/temp/01'


def _find_cams(default=False):
    """Find cameras in the scene.

    Args:
        default (bool): show default cameras

    Returns:
        (Camera list): cameras
    """
    _cams = []
    for _shp in cmds.ls(type='camera'):
        _tfm = cmds.listRelatives(_shp, parent=True)[0]
        if not default and _tfm in ['persp', 'top', 'front', 'side']:
            continue
        _cam = _Camera(_tfm)
        _cams.append(_cam)

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
    #print 'FBX EXPORT SELECTION'
    _nodes = cmds.ls(selection=True)
    #print ' - NODES', _nodes
    _start, _end = range_
    #print ' - EXPORT RANGE', range_

    if add_border_keys:
        mel.eval('DeleteAllStaticChannels')
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

    _mel = '\n'.join([
        'FBXResetExport;',
        'FBXExportFileVersion -v "FBX201400";',
        'FBXExportSmoothingGroups -v true;',
        'FBXExportShapes -v true;',
        'FBXExportSkins -v true;',
        'FBXExportTangents -v true;',
        'FBXExportSmoothMesh -v false;',
        'FBXExportBakeComplexAnimation -v true;',
        'FBXExport -f "{fbx}" -s;',
    ]).format(end=_start, start=_end, fbx=fbx)
    #print _mel
    #print cmds.ls(selection=True)
    cmds.loadPlugin('fbxmaya', quiet=True)
    mel.eval(_mel)
    
    
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

    def export_fbx_in_world_space(
        self, fbx, range_, add_border_keys=True, cleanup=True):
        """Export fbx of this canera in world space.

        Args:
            fbx (str): fbx path
            range_ (tuple): start/end frames
            add_border_keys (bool): add start/end frame keys
            cleanup (bool): clean tmp nodes
        """
        # print "EXPORT CAM IN WORLD SPACE"
        _set_namespace(':export_tmp', clean=True)
        
        # 解锁目标物体的属性&设置为可关键帧
        for attr in ['translate', 'rotate', 'scale']:
            for axis in ['X', 'Y', 'Z']:
                try:
                    cmds.setAttr('{}.{}{}'.format(self.tfm, attr, axis), lock=False)
                    cmds.setAttr('{}.{}{}'.format(self.tfm, attr, axis), keyable=True)
                except:
                    pass  # 忽略锁定失败的属性

        # Create duplicate cam in world
        _dup = _Camera(cmds.duplicate(self.tfm)[0])
        if cmds.listRelatives(_dup.tfm, parent=True):
            cmds.parent(_dup.tfm, world=True)
            

        # Drive dup cam by orig
        for _attr in cmds.listAttr(self.shp, keyable=True):
            _type = cmds.attributeQuery(
                _attr, node=self.shp, attributeType=True)
            if _type in ['message']:
                continue
            cmds.connectAttr('{}.{}'.format(self.shp, _attr),
                             '{}.{}'.format(_dup.shp, _attr))
        _p_cons = cmds.parentConstraint(
            self.tfm, _dup.tfm, maintainOffset=False)[0]
        _s_cons = cmds.scaleConstraint(
            self.tfm, _dup.tfm, maintainOffset=False)[0]
    
        # Bake anim
        # print ' - RANGE', range_
        cmds.bakeResults([_dup.tfm, _dup.shp], time=range_)
     
        cmds.delete(_p_cons, _s_cons)
        mel.eval('DeleteAllStaticChannels')
        _dup.export_fbx(
            fbx=fbx, range_=range_, add_border_keys=add_border_keys)
        if cleanup:
            _set_namespace(':export_tmp', clean=True)
        _set_namespace(':')
    

    def find_nodes(self):
        """Get nodes in this camera.

        Returns:
            (str list): list of nodes
        """
        return [self.tfm, self.shp]
    
   
    
def export_all_cameras(fbx_directory, add_border_keys=True):
    """Export all cameras in the scene to FBX files with the current timeline range."""
    
    # 获取当前 Maya 文件的文件名
    scene_path = cmds.file(q=True, sceneName=True)
    scene_name = os.path.splitext(os.path.basename(scene_path))[0]  # 去掉文件扩展名
    
    # 创建以当前文件名命名的目录
    export_dir = os.path.join(fbx_directory, scene_name)
    if not os.path.exists(export_dir):
        # print "Creating directory: {}".format(export_dir)
        os.makedirs(export_dir)
    
    # 获取当前时间轴的起始和结束帧
    start_frame = cmds.playbackOptions(q=True, min=True)
    end_frame = cmds.playbackOptions(q=True, max=True)
    range_ = (start_frame, end_frame)
    
    # 获取所有相机
    _cams = _find_cams(default=False)
    
    if not _cams:
        # print "No cameras found in the scene."
        return
    
    # print "Exporting {} cameras from frame {} to {}...".format(len(_cams), start_frame, end_frame)

    # 对指定相机进行导出
    for cam in _cams:
    # 获取相机的名称
        camera_name = cam.name
        # print "Exporting camera: {}".format(camera_name)

        # 检查相机名称是否以 '_cam' 结尾
        if camera_name.endswith('_CAM'):
            # 定义导出文件路径（直接在以当前文件名命名的目录中）
            fbx_filepath = os.path.join(export_dir, "{}.fbx".format(camera_name))
            fbx_filepath = fbx_filepath.replace("\\", "/")  # 替换为正斜杠
    

            # 调用相机的导出函数
            cam.export_fbx_in_world_space(fbx=fbx_filepath, range_=range_, add_border_keys=add_border_keys)
        else:
            
            print("Skipping camera: {}".format(camera_name))  # 如果名称不以'_cam'结尾，跳过导出


    print("All cameras exported successfully to {}".format(export_dir))


# 示例调用：导出所有相机到指定目录
export_all_cameras(fbx_directory=OutputPath, add_border_keys=True)
