# -*- coding: utf-8 -*-
#
#
#
#
#
#single

import os
from maya import cmds, mel
import constants
import alembicExport

exportVars = constants.getConstants()
EXPORT_SET_NAME = exportVars['exportSetName']
DUPLICATE_OBJECT_NAME = exportVars['duplicateObjectName']
DEFAULT_ABC_ARGS = exportVars['defaultArgList']

class SingleExport(alembicExport.BaseExport):
    def __init__(self):
        # 修改super调用方式，适配Python 2.7
        alembicExport.BaseExport.__init__(self)
    
    def setFramerange(self, min=None, max=None):
        """Sets and returns the framerange."""
        return super(SingleExport, self).setFramerange(min, max)
    
    def getExportSets(self):
        """Returns the found export sets. Errors if none found."""
        sets = cmds.ls('::*{0}*'.format(EXPORT_SET_NAME), sets=1)
        
        if not sets:
            cmds.error('No valid sets were found. Sets with the phrase {0} are needed.'.format(EXPORT_SET_NAME), noContext=1)
    
        self.objectsForExport = sets
        
        return self.objectsForExport
    
    def getSelected(self):
        """Returns the selection."""
        selection = cmds.ls(sl=1)
        if not selection:
            cmds.error('Nothing is selected for export.', noContext=1)
        if cmds.filterExpand(selection, selectionMask=31):
            cmds.error('Selecting components is forbidden.', noContext=1)
            
        self.objectsForExport = selection
        
        return self.objectsForExport
    
    def setFilepath(self, filepath):
        """Returns the set filepath."""
        return super(SingleExport, self).setFilepath(filepath)
    
    def duplicateObjects(self):
        """Duplicate objects are used for the export.
        This prevents export failure due to identical object names, as namespaces are also removed.
        When importing to Unreal, the objects will appear named as the DUPLICATE_OBJECT_NAME constant followed by a number.
        This is a negligible edit and does not affect anything other than the name.
        """
        super(SingleExport, self).duplicateObjects()
    
    def exportFile(self): 
        """Creates the export string.
        Exports all objects found in each export set into one file.
        Runs the export as a mel command.
        """
        objects = ['-root {0}'.format(obj) for obj in self.exportObjects]
        root = ' '.join(objects)
        job = '{0} -framerange {1} {2} -file {3}'.format(root, self.framerange, DEFAULT_ABC_ARGS, self.filepath)
        
        exportCommand = 'AbcExport -j "{0}"'.format(job)
        mel.eval(exportCommand)
        
    def deleteDuplicateObjects(self):
        """Deletes the duplicate objects."""
        super(SingleExport, self).deleteDuplicateObjects()
        
    def addFrameData(self):
        """Adds the start frame data to the alembic file for Unreal to read when importing."""
        # 如果实现了addFrameData方法，则调用父类方法
        super(SingleExport, self).addFrameData()
    
    @classmethod
    def exportSelection(cls, filepath, startFrame=None, endFrame=None):
        """Exports all selected objects to given filepath."""
        try:
            exporter = cls()
            exporter.setFramerange(startFrame, endFrame)
            exporter.getSelected()
            exporter.setFilepath(filepath)
            exporter.duplicateObjects()
            exporter.exportFile()
            exporter.deleteDuplicateObjects()
            exporter.addFrameData()
            print('Export Completed')
            
            return exporter
        except Exception as e:
            # 添加错误处理
            import traceback
            print("导出错误: " + str(e))
            print(traceback.format_exc())
            raise
        
    @classmethod
    def exportSelectionSets(cls, filepath, startFrame=None, endFrame=None):
        """Exports all objects within the selection sets to the given filepath."""
        try:
            exporter = cls()
            exporter.setFramerange(startFrame, endFrame)
            exporter.getExportSets()
            exporter.setFilepath(filepath)
            exporter.duplicateObjects()
            exporter.exportFile()
            exporter.deleteDuplicateObjects()
            exporter.addFrameData()
            print('Export Completed')
            
            return exporter
        except Exception as e:
            # 添加错误处理
            import traceback
            print("导出错误: " + str(e))
            print(traceback.format_exc())
            raise

