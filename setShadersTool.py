# -*- coding: utf-8 -*-
#setShadersTool.py

"""
Sets shaders to objects' faces for the Unreal Alembic Cache.
"""

import maya.cmds as cmds

class SetShader:
    def __init__(self):
        print('Setting shader to face components. . . ')
        cmds.undoInfo(openChunk=1, chunkName='Shader_Set_Action')
        self.getGeometry()
        for self.geometry in self.selectedGeometry:
            self.getShape()
            
            try:
                self.getAssignedShader()
            except RuntimeError as e:
                print(e)
                continue
            except Exception as e:
                print("获取材质时出错: " + str(e))
                continue
            
            self.applyShaders()
        cmds.undoInfo(closeChunk=1, chunkName='Shader_Set_Action')
        print('Shaders set successfully!')


    def getGeometry(self):
        """Get the selected geometry objects"""
        selection = cmds.ls(sl=1, exactType='transform')
        print(selection)
        if len(selection) <1:
            cmds.error('Select some geometry', noContext=1)

        self.selectedGeometry = selection

    def getShape(self):
        """Get the accompanying shape node to the selected transform."""
        shapes = cmds.listRelatives(self.geometry, shapes=1)
        if not shapes:
            raise RuntimeError("对象 {0} 没有形状节点".format(self.geometry))
        self.shape = shapes[0]

    def getAssignedShader(self):
        """Get the shader assigned to the given objects."""
        shaders = []
        faces = cmds.polyListComponentConversion(self.geometry, toFace=True)
        if faces:
            face = cmds.ls(faces, flatten=True)[0]
            shadingEngines = cmds.listSets(object=face, type=1)
            if shadingEngines:
                self.shader = shadingEngines[0]
                return
        
        # 备用方法
        shapes = cmds.listRelatives(self.geometry, shapes=True, fullPath=True)
        if shapes:
            shadingEngines = cmds.listConnections(shapes[0], type="shadingEngine")
            if shadingEngines:
                self.shader = shadingEngines[0]
                return
        
        raise RuntimeError("对象 {0} 没有关联的材质".format(self.geometry))

    def setInitialShaderToMesh(self):
        """To set the shader to the faces, we need an alternate shader on the mesh.
        The default standardSurface is assigned."""
        cmds.select(self.geometry, r=1)
        cmds.sets(e=1, forceElement='initialShadingGroup')
        print('SET INITIAL!\n'+self.geometry)


    def setShaderToFaces(self):
        """Set a shader to the faces of a mesh object."""
        # 确保转换为面组件
        faces = cmds.polyListComponentConversion(self.geometry, toFace=True)
        if faces:
            faces = cmds.ls(faces, flatten=True)
            cmds.select(faces, r=1)
            cmds.sets(e=1, forceElement=self.shader)
            print('SET MATERIAL!\n' + str(faces))

    def applyShaders(self):
        """Applies mesh and object shaders. Must be in the afformentioned order.
        Must also do a viepowt refresh."""
        meshFaces = '{0}.f[*]'.format(self.geometry)
        cmds.select(meshFaces, r=1)
        cmds.sets(e=1, forceElement=self.shader)
        # 强制刷新
        cmds.refresh(force=True)
        cmds.ogs(reset=1)



