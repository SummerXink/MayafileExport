# -*- coding: utf-8 -*-
#setShadersTool.py

"""
Sets shaders to objects' faces for the Unreal Alembic Cache.
"""

import maya.cmds as cmds
import traceback

class SetShader:
    def __init__(self):
        print('Setting shader to face components. . . ')
        cmds.undoInfo(openChunk=1, chunkName='Shader_Set_Action')
        self.getGeometry()
        
        # 收集所有需要处理的几何体和材质
        geometry_shader_pairs = []
        for self.geometry in self.selectedGeometry:
            try:
                self.getShape()
                self.getAssignedShader()
                geometry_shader_pairs.append((self.geometry, self.shader))
                print("成功获取对象 {0} 的材质: {1}".format(self.geometry, self.shader))
            except RuntimeError as e:
                print("警告: {0}".format(str(e)))
                continue
            except Exception as e:
                print("处理对象 {0} 时出错: {1}".format(self.geometry, str(e)))
                print(traceback.format_exc())
                continue
        
        # 批量应用材质
        for geometry, shader in geometry_shader_pairs:
            self.geometry = geometry
            self.shader = shader
            self.applyShaders()
        
        cmds.undoInfo(closeChunk=1, chunkName='Shader_Set_Action')
        print('Shaders set successfully!')


    def getGeometry(self):
        """Get the selected geometry objects"""
        selection = cmds.ls(sl=1, exactType='transform')
        print("选中的几何体: {0}".format(selection))
        if len(selection) < 1:
            cmds.error('请选择一些几何体', noContext=1)

        self.selectedGeometry = selection

    def getShape(self):
        """Get the accompanying shape node to the selected transform."""
        shapes = cmds.listRelatives(self.geometry, shapes=1)
        if not shapes:
            raise RuntimeError("对象 {0} 没有形状节点".format(self.geometry))
        self.shape = shapes[0]
        print("对象 {0} 的形状节点: {1}".format(self.geometry, self.shape))

    def getAssignedShader(self):
        """Get the shader assigned to the given objects using multiple methods."""
        # 尝试多种方法获取材质
        methods = [
            self._getShaderFromFaces,
            self._getShaderFromShape,
            self._getShaderFromHistory,
            self._getDefaultShader
        ]
        
        for method in methods:
            try:
                shader = method()
                if shader:
                    self.shader = shader
                    return
            except Exception as e:
                print("方法 {0} 失败: {1}".format(method.__name__, str(e)))
        
        raise RuntimeError("对象 {0} 没有关联的材质，且无法创建默认材质".format(self.geometry))
    
    def _getShaderFromFaces(self):
        """从面组件获取材质"""
        faces = cmds.polyListComponentConversion(self.geometry, toFace=True)
        if faces:
            face = cmds.ls(faces, flatten=True)[0]
            shadingEngines = cmds.listSets(object=face, type=1)
            if shadingEngines:
                return shadingEngines[0]
        return None
    
    def _getShaderFromShape(self):
        """从形状节点获取材质"""
        shapes = cmds.listRelatives(self.geometry, shapes=True, fullPath=True)
        if shapes:
            shadingEngines = cmds.listConnections(shapes[0], type="shadingEngine")
            if shadingEngines:
                return shadingEngines[0]
        return None
    
    def _getShaderFromHistory(self):
        """从历史记录获取材质"""
        history = cmds.listHistory(self.geometry)
        if history:
            shadingEngines = cmds.listConnections(history, type="shadingEngine")
            if shadingEngines:
                return shadingEngines[0]
        return None
    
    def _getDefaultShader(self):
        """创建并返回默认材质"""
        print("为对象 {0} 创建默认材质".format(self.geometry))
        # 创建标准表面材质
        shader = cmds.shadingNode('standardSurface', asShader=True, name="{0}_defaultShader".format(self.geometry))
        # 创建着色引擎
        shadingEngine = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="{0}_SG".format(shader))
        # 连接材质到着色引擎
        cmds.connectAttr('{0}.outColor'.format(shader), '{0}.surfaceShader'.format(shadingEngine), force=True)
        return shadingEngine

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

    def createNamedFaceSet(self):
        """为对象创建命名面集"""
        try:
            # 获取所有面
            meshFaces = '{0}.f[*]'.format(self.geometry)
            faces = cmds.ls(meshFaces, flatten=True)
            
            if not faces:
                print("警告: 对象 {0} 没有面组件，无法创建面集".format(self.geometry))
                return
                
            # 创建面集名称 - 使用材质名称，移除命名空间前缀
            # 获取短名称（不带命名空间）
            geometry_short_name = cmds.ls(self.geometry, shortNames=True)[0]
            shader_short_name = cmds.ls(self.shader, shortNames=True)[0]
            
            # 创建面集名称，使用短名称
            face_set_name = "{0}_{1}_faceSet".format(geometry_short_name, shader_short_name)
            
            # 创建面集 - 使用Maya 2020兼容的方法
            # 检查面集是否已存在
            existing_sets = cmds.ls(sets=True)
            if face_set_name not in existing_sets:
                # 创建空面集
                cmds.sets(name=face_set_name, empty=True)
                
            # 将面添加到面集 - 使用短名称
            # 获取面的短名称
            short_faces = []
            for face in faces:
                short_face = cmds.ls(face, shortNames=True)[0]
                short_faces.append(short_face)
                
            # 使用短名称添加面到面集
            cmds.sets(short_faces, edit=True, addElement=face_set_name)
            
            print("成功为对象 {0} 创建面集: {1}".format(self.geometry, face_set_name))
        except Exception as e:
            print("创建面集时出错: {0}".format(str(e)))
            print(traceback.format_exc())

    def applyShaders(self):
        """Applies mesh and object shaders with validation and error handling."""
        try:
            # 获取所有面
            meshFaces = '{0}.f[*]'.format(self.geometry)
            faces = cmds.ls(meshFaces, flatten=True)
            
            if not faces:
                print("警告: 对象 {0} 没有面组件".format(self.geometry))
                return
            
            # 两步法应用材质，与旧版本一致：
            # 1. 先将初始着色组应用到整个网格
            self.setInitialShaderToMesh()
            
            # 2. 然后将指定的着色组应用到面
            self.setShaderToFaces()
            
            # 验证材质应用 - 改进的验证方法
            try:
                # 使用listSets命令获取面所属的所有集合
                applied_shaders = cmds.listSets(object=faces[0], type=1)
                if applied_shaders and self.shader not in applied_shaders:
                    print("警告: 材质可能未正确应用到对象 {0} 的面".format(self.geometry))
            except Exception as e:
                print("验证材质应用时出错: {0}".format(str(e)))
            
            # 只在所有对象处理完后刷新一次
            if self.geometry == self.selectedGeometry[-1]:
                cmds.refresh(force=True)
                cmds.ogs(reset=1)
                
            print("成功将材质 {0} 应用到对象 {1} 的 {2} 个面".format(self.shader, self.geometry, len(faces)))
        except Exception as e:
            print("应用材质到对象 {0} 的面时出错: {1}".format(self.geometry, str(e)))
            print(traceback.format_exc())



