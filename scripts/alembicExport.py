# -*- coding: utf-8 -*-
"""
This file contains the base export functionality for Alembic files in Maya.
It includes methods for setting the frame range, setting the file path, duplicating objects,
deleting duplicate objects, and adding frame data to the Alembic file for Unreal Engine.
"""


import os
from maya import cmds, mel
import constants

exportVars = constants.getConstants()
EXPORT_SET_NAME = exportVars['exportSetName']
# 定义默认值，避免KeyError
DUPLICATE_OBJECT_NAME = 'original'  # 使用原始对象，不重命名
DEFAULT_ABC_ARGS = exportVars['defaultArgList']

class BaseExport(object):
    def __init__(self):
        pass
    
    def setFramerange(self, min=None, max=None):
        """Sets and returns the framerange."""
        if min or max is None:
            min = cmds.playbackOptions(q=1, min=1)
            max = cmds.playbackOptions(q=1, max=1)
            self.framerange = '{0} {1}'.format(min, max)
        else:
            self.framerange = '{0} {1}'.format(min, max)
        
        return self.framerange
    
    def setFilepath(self, filepath):
        """Returns the set filepath."""
        path = os.path.normpath(filepath)
        fixedPath = path.replace('\\', '/')
        self.filepath = fixedPath
        
        return self.filepath
    
    def duplicateObjects(self):
        """直接使用原始对象导出，不进行复制"""
        self.exportObjects = self.objectsForExport
    
    def deleteDuplicateObjects(self):
        """由于不再复制对象，此方法无需执行任何操作"""
        pass
    
    def addFrameData(self):
        """添加帧数据到Alembic文件，供Unreal引擎使用"""
        # 如果需要实现该方法，可以在此添加代码
        pass
