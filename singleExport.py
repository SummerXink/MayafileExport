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
        super(SingleExport, self).__init__()
    
    def setFramerange(self, min=None, max=None):
        """Sets and returns the framerange."""
        return super().setFramerange(min, max)
    
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
        return super().setFilepath(filepath)
    
    def duplicateObjects(self):
        """Duplicate objects are used for the export.
        This prevents export failure due to identical object names, as namespaces are also removed.
        When importing to Unreal, the objects will appear named as the DUPLICATE_OBJECT_NAME constant followed by a number.
        This is a negligible edit and does not affect anything other than the name.
        """
        super().duplicateObjects()
    
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
        super().deleteDuplicateObjects()
        
    def addFrameData(self):
        """Adds the start frame data to the alembic file for Unreal to read when importing."""
        super().addFrameData()
    
    @classmethod
    def exportSelection(cls, filepath, startFrame=None, endFrame=None):
        """Exports all selected objects to given filepath."""
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
        
    @classmethod
    def exportSelectionSets(cls, filepath, startFrame=None, endFrame=None):
        """Exports all objects within the selection sets to the given filepath."""
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

