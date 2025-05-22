# -*- coding: utf-8 -*-
"""
ABC导出脚本 - 可独立执行
用于从Maya文件中导出ABC缓存，支持命名空间筛选和材质应用

此脚本设计为可以从Maya外部调用或在独立Maya会话中运行
"""

import sys 
import os
import time
import traceback

# 确保Python 2.7兼容的Unicode处理
reload(sys)
sys.setdefaultencoding('utf-8')

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 命令行参数支持
if len(sys.argv) > 1:
    # 如果提供了参数，则解析这些参数
    # 支持的参数: maya_file, output_path, namespaces, apply_shader, triangulate, use_underscore_index, enable_smooth, smooth_divisions
    maya_file = sys.argv[1] if len(sys.argv) > 1 else ""
    output_path = sys.argv[2] if len(sys.argv) > 2 else "."
    namespaces_str = sys.argv[3] if len(sys.argv) > 3 else "tbx_chr,tbx_prp"
    apply_shader = True if len(sys.argv) <= 4 or sys.argv[4].lower() == "true" else False
    triangulate = True if len(sys.argv) > 5 and sys.argv[5].lower() == "true" else False
    use_underscore_index = int(sys.argv[6]) if len(sys.argv) > 6 else 3
    enable_smooth = True if len(sys.argv) > 7 and sys.argv[7].lower() == "true" else False
    smooth_divisions = int(sys.argv[8]) if len(sys.argv) > 8 else 1
else:
    # 默认值
    maya_file = ""
    output_path = "."
    namespaces_str = "tbx_chr,tbx_prp"
    apply_shader = True
    triangulate = False
    use_underscore_index = 3
    enable_smooth = False
    smooth_divisions = 1

# 解析命名空间
namespaces = [ns.strip() for ns in namespaces_str.split(",")]

# 提取文件名
if maya_file:
    maya_file_name = os.path.splitext(os.path.basename(maya_file))[0]
else:
    maya_file_name = "untitled"

# 创建子文件夹名称 (使用第N个下划线前的部分)
parts = maya_file_name.split('_')
if len(parts) > use_underscore_index:
    # 有足够的下划线，取到第N个下划线前的部分
    subfolder_name = '_'.join(parts[:use_underscore_index])
else:
    # 如果下划线不足，使用整个名称
    subfolder_name = maya_file_name

# 创建子文件夹路径
project_folder_path = os.path.join(output_path, subfolder_name)
if not os.path.exists(project_folder_path):
    os.makedirs(project_folder_path)

# 创建子子文件夹路径（使用完整Maya文件名）
subfolder_path = os.path.join(project_folder_path, maya_file_name)
if not os.path.exists(subfolder_path):
    os.makedirs(subfolder_path)

# 创建日志文件
log_file = os.path.join(subfolder_path, 'export_log.txt')
def write_log(message):
    with open(log_file, 'a') as f:
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        f.write('[' + current_time + '] ' + message + '\n')

write_log('开始初始化Maya独立模式...')
write_log('使用第%d个下划线前的字符作为子文件夹名称' % use_underscore_index)
write_log('子文件夹名称: ' + subfolder_name)
write_log('子子文件夹名称: ' + maya_file_name)
write_log('将导出到路径: ' + subfolder_path)

# 创建进度文件
progress_file = os.path.join(output_path, 'export_progress.txt')

try:
    # 初始化Maya独立模式
    import maya.standalone
    # 设置环境变量以禁用自动插件加载
    import os
    os.environ['MAYA_DISABLE_PLUGINS'] = '1'
    os.environ['MAYA_DISABLE_CIP'] = '1'  # 禁用客户参与计划
    os.environ['MAYA_DISABLE_CER'] = '1'  # 禁用崩溃报告
    # 禁用插件路径
    os.environ['MAYA_PLUG_IN_PATH'] = ''
    # 初始化Maya
    write_log('使用无UI模式初始化Maya...')
    maya.standalone.initialize(name='python')
    write_log('Maya独立模式初始化完成')

    # 导入Maya命令
    import maya.cmds as cmds
    import maya.mel as mel

    # 加载必要的插件
    write_log('检查插件状态...')
    try:
        loaded_plugins = cmds.pluginInfo(query=True, listPlugins=True) or []
        write_log('当前加载的插件: ' + str(loaded_plugins))
        
        # 确保AbcExport插件加载
        write_log('加载AbcExport插件...')
        if not 'AbcExport.mll' in loaded_plugins:
            cmds.loadPlugin('AbcExport', quiet=True)
            write_log('AbcExport插件加载成功')
        else:
            write_log('AbcExport插件已加载')
    except Exception as e:
        write_log('处理插件时出错: ' + str(e))

    # 禁用所有插件的自动加载
    cmds.optionVar(intValue=['autoLoadPlugins', 0])
    # 设置其他选项以提高稳定性
    cmds.optionVar(intValue=['CIP', 0])  # 禁用客户参与计划
    cmds.optionVar(intValue=['CER', 0])  # 禁用崩溃报告

    # 打开Maya文件
    write_log('打开Maya文件...')
    # 禁用自动加载插件
    cmds.optionVar(intValue=['autoLoadPlugins', 0])
    
    # 创建新的空场景
    write_log('创建新场景...')
    cmds.file(new=True, force=True)
    
    # 禁用渲染器和绘图更新，提高稳定性
    try:
        cmds.optionVar(intValue=('renderSetupEnable', 0))  # 禁用渲染设置
        try:
            cmds.modelEditor('modelPanel4', edit=True, displayAppearance='wireframe') # 使用线框模式
        except:
            pass # 忽略没有UI时的错误
    except Exception as e:
        write_log('设置渲染选项时出错(可忽略): ' + str(e))
    
    # 设置MEL变量以忽略特定类型的插件错误
    mel.eval('global string $gMayaIgnoredWarnings[];')
    mel.eval('$gMayaIgnoredWarnings[size($gMayaIgnoredWarnings)] = "Unable to dynamically load";')
    mel.eval('$gMayaIgnoredWarnings[size($gMayaIgnoredWarnings)] = "Redshift";')
    mel.eval('$gMayaIgnoredWarnings[size($gMayaIgnoredWarnings)] = "rsMaterial";')
    mel.eval('$gMayaIgnoredWarnings[size($gMayaIgnoredWarnings)] = "The shadingEngine";')
    
    # 设置更安全的文件加载选项
    file_options = {
        'open': True,
        'force': True,
        'ignoreVersion': True,
        #'loadReferenceDepth': 'all',  # 加载所有引用
        'prompt': False,
        'loadNoReferences': False,    # 允许加载引用
        'returnNewNodes': False       # 不返回新节点列表，提高性能
    }

    write_log('尝试打开文件: ' + maya_file)
    # 尝试加载文件, 忽略未知节点错误
    file_open_success = False
    try:
        cmds.file(maya_file, **file_options)
        write_log('Maya文件已成功打开')
        file_open_success = True
    except Exception as e:
        error_msg = str(e)
        write_log('打开文件时出现错误，尝试替代方法: ' + error_msg)
        # 尝试用MEL命令打开
        try:
            write_log('使用MEL命令尝试打开文件...')
            # 不使用setConstructionHistory命令，直接使用file命令打开
            mel.eval('file -open -force -ignoreVersion -prompt false "' + maya_file.replace('\\', '\\\\') + '";')
            write_log('使用MEL命令打开文件成功')
            file_open_success = True
        except Exception as e2:
            write_log('使用MEL命令打开文件失败: ' + str(e2))
            write_log('将继续尝试导出，但可能不成功')
    
    # 导入引用文件
    file_open_success = True
    if file_open_success:
        write_log('开始导入引用文件...')
        try:
            # 获取所有引用
            references = cmds.file(query=True, reference=True) or []
            write_log('找到 %d 个引用文件' % len(references))
            
            # 逐个处理引用
            for ref in references:
                try:
                    ref_node = cmds.referenceQuery(ref, referenceNode=True)
                    ref_file = cmds.referenceQuery(ref_node, filename=True)
                    
                    # 检查引用是否已卸载
                    is_loaded = cmds.referenceQuery(ref_node, isLoaded=True)
                    if not is_loaded:
                        # 如果引用已卸载，先移除
                        write_log('发现已卸载的引用: %s，正在移除...' % ref_file)
                        cmds.file(referenceNode=ref_node, removeReference=True)
                        write_log('成功移除已卸载的引用: %s' % ref_file)
                        continue
                        
                    write_log('正在导入引用: %s' % ref_file)
                    
                    # 导入引用
                    cmds.file(ref_file, importReference=True)
                    write_log('成功导入引用: %s' % ref_file)
                    
                except Exception as ref_error:
                    write_log('处理引用 %s 时出错: %s' % (ref, str(ref_error)))
                    write_log(traceback.format_exc())
            
            write_log('所有引用文件处理完成')
        except Exception as ref_import_error:
            write_log('处理引用过程中出错: %s' % str(ref_import_error))
            write_log(traceback.format_exc())

    # 更新进度函数
    def update_progress(progress, message):
        try:
            with open(progress_file, 'w') as f:
                # 确保message是str类型
                if isinstance(message, unicode):
                    message = message.encode('utf-8')
                f.write(str(int(progress)) + '\n' + str(message))
            write_log('进度: ' + str(progress) + '% - ' + str(message))
        except Exception as e:
            write_log('更新进度出错: ' + str(e))

    # 优化后的可见性检查函数
    def is_object_visible(obj_path):
        # 检查对象是否存在
        if not cmds.objExists(obj_path):
            write_log('警告: 对象不存在 ' + obj_path)
            return False

        # 检查visibility属性 - 基本的可见性检查
        if cmds.attributeQuery('visibility', node=obj_path, exists=True):
            if not cmds.getAttr(obj_path + '.visibility'):
                write_log('对象不可见: ' + obj_path)
                return False

        # 检查overrideEnabled和overrideVisibility
        if cmds.attributeQuery('overrideEnabled', node=obj_path, exists=True):
            if cmds.getAttr(obj_path + '.overrideEnabled'):
                if cmds.attributeQuery('overrideVisibility', node=obj_path, exists=True):
                    if not cmds.getAttr(obj_path + '.overrideVisibility'):
                        write_log('覆盖可见性设置导致不可见: ' + obj_path)
                        return False

        # 递归检查父级可见性
        parents = cmds.listRelatives(obj_path, parent=True, fullPath=True)
        if parents:
            return is_object_visible(parents[0])  # 只检查直接父级

        return True

    # 查找所有有效形状节点
    def get_valid_shapes(obj_path):
        shapes = cmds.listRelatives(obj_path, shapes=True, fullPath=True) or []
        valid_shapes = []
        for shape in shapes:
            if not cmds.attributeQuery('intermediateObject', node=shape, exists=True) or not cmds.getAttr(shape + '.intermediateObject'):
                valid_shapes.append(shape)
        return valid_shapes

    # 检查对象是否有非中间形状节点
    def has_valid_shapes(obj_path):
        return len(get_valid_shapes(obj_path)) > 0

    # 导入模块
    try:
        write_log('导入导出相关模块...')
        import renameShadingGroup
        import setShadersTool
        import singleExport
        import alembicExport
        write_log('模块导入成功')
    except Exception as e:
        write_log('导入模块失败: ' + str(e))
        raise

    # 开始导出过程
    update_progress(10, '开始筛选场景对象...')

    # 获取命名空间过滤条件
    write_log('使用命名空间筛选: ' + str(namespaces))

    # 筛选场景中符合条件的对象
    all_objects = cmds.ls(long=True)
    filtered_namespaces = set()

    # 筛选命名空间
    for obj in all_objects:
        if ':' in obj:
            ns = obj.split(':')[0]
            for filter_ns in namespaces:
                if filter_ns in ns:
                    filtered_namespaces.add(ns)
                    break
            ns_1 = obj.split(':')[1]
            for filter_ns1 in namespaces:
                if filter_ns1 in ns_1:
                    filtered_namespaces.add(ns_1)
                    break

    write_log('找到匹配的命名空间: ' + str(list(filtered_namespaces)))

    # 按命名空间查找cache组
    found_cache_groups = {}
    for ns in filtered_namespaces:
        cache_path = ns + ':cache'
        if cmds.objExists(cache_path):
            write_log('找到cache组: ' + cache_path)
            
            # 检查cache组是否可见
            if not is_object_visible(cache_path):
                write_log('警告: cache组 ' + cache_path + ' 不可见，将跳过')
                continue
                
            # 获取cache下所有模型（包括深层级），直接找有形状节点的模型对象
            mesh_objects = []  # 只包含有效形状节点的对象
            hidden_objects = []
            skipped_objects = []
            try:
                # 获取cache下所有后代对象
                all_descendants = cmds.listRelatives(cache_path, allDescendents=True, fullPath=True, type='transform') or []
                write_log('cache组 ' + cache_path + ' 下有 ' + str(len(all_descendants)) + ' 个后代对象')

                # 查找所有可见且有形状节点的模型
                for obj in all_descendants:
                    # 检查可见性
                    if not is_object_visible(obj):
                        hidden_objects.append(obj)
                        continue

                    # 检查是否有有效形状节点
                    valid_shapes = get_valid_shapes(obj)
                    if valid_shapes:
                        mesh_objects.append(obj)
                        write_log('找到可见模型: ' + obj + ' (有效形状节点: ' + str(len(valid_shapes)) + '个)')
                    else:
                        skipped_objects.append(obj)

                write_log('筛选结果: 找到 ' + str(len(mesh_objects)) + ' 个有效模型, ' +
                         str(len(hidden_objects)) + ' 个不可见对象, ' +
                         str(len(skipped_objects)) + ' 个没有形状节点的对象')

            except Exception as e:
                write_log('处理对象时出错: ' + str(e))
                write_log(traceback.format_exc())

            if mesh_objects:
                found_cache_groups[ns] = {
                    'cache_path': cache_path,
                    'mesh_objects': mesh_objects
                }
                write_log('命名空间 ' + ns + ' 下找到 ' + str(len(mesh_objects)) + ' 个可导出模型')

    if not found_cache_groups:
        write_log('未找到符合条件的cache组！')
        update_progress(100, '未找到符合条件的对象，导出终止')
        sys.exit(1)

    write_log('找到 ' + str(len(found_cache_groups)) + ' 个符合条件的cache组')
    update_progress(20, '找到 ' + str(len(found_cache_groups)) + ' 个符合条件的cache组')

    # 获取当前时间轴范围
    start_frame = cmds.playbackOptions(q=True, min=True)
    end_frame = cmds.playbackOptions(q=True, max=True)
    write_log('帧范围: ' + str(start_frame) + ' - ' + str(end_frame))
    
    # 解锁initialShadingGroup节点，防止"Destination is locked"错误
    write_log('解锁initialShadingGroup节点...')
    try:
        cmds.lockNode('initialShadingGroup', l=0, lockUnpublished=0)
        write_log('initialShadingGroup节点解锁成功')
    except Exception as lock_err:
        write_log('解锁initialShadingGroup时出错: ' + str(lock_err))

    # 遍历每个cache组进行导出
    total_groups = len(found_cache_groups)
    current_group = 0
    total_exported_objects = 0

    for ns, data in found_cache_groups.items():
        current_group += 1
        group_progress = 20 + (current_group * 80 / total_groups)
        update_progress(group_progress, '正在处理 (' + str(current_group) + '/' + str(total_groups) + '): ' + ns)
        write_log('开始处理: ' + ns)

        try:
            cache_path = data['cache_path']
            mesh_objects = data['mesh_objects']

            if not mesh_objects:
                write_log('警告: ' + cache_path + ' 下没有可导出模型，跳过')
                continue

            # 将材质指定到面上
            if apply_shader:
                write_log('正在将材质指定到面上...')
                try:
                    if not mesh_objects:
                        write_log('警告: 没有找到有形状节点的模型对象，跳过材质应用')
                    else:
                        
                            
                        # 只对实际的模型对象应用材质
                        write_log('对 ' + str(len(mesh_objects)) + ' 个模型对象应用材质')
                        cmds.select(mesh_objects, replace=True)
                        # 使用setShadersTool将材质指定到面上
                        setShadersTool.SetShader()
                        write_log('材质指定到面上成功')
                except Exception as e:
                    write_log('将材质指定到面上时出错: ' + str(e))
                    write_log(traceback.format_exc())

            # 如果需要，应用多边形光滑
            if enable_smooth and smooth_divisions > 0:
                write_log('正在应用多边形光滑(层数: %d)...' % smooth_divisions)
                try:
                    smoothed_count = 0
                    for mesh in mesh_objects:
                        # 获取形状节点
                        shapes = cmds.listRelatives(mesh, shapes=True, fullPath=True) or []
                        for shape in shapes:
                            if cmds.nodeType(shape) == 'mesh':
                                # 确保形状节点不是中间对象
                                if not cmds.getAttr(shape + '.intermediateObject'):
                                    # 应用多边形光滑
                                    cmds.polySmooth(mesh, 
                                                   divisions=smooth_divisions,
                                                   keepBorder=True,  # 保持边界
                                                   keepHardEdge=False,  # 保持硬边
                                                   keepMapBorders=True,  # 保持UV边界
                                                   ch=True)  # 不保留历史记录
                                    smoothed_count += 1
                    write_log('成功光滑处理 %d 个模型' % smoothed_count)
                except Exception as e:
                    write_log('应用多边形光滑时出错: ' + str(e))
                    write_log(traceback.format_exc())

            # 如果需要，将模型三角化
            if triangulate:
                write_log('正在将模型转换为三角面...')
                try:
                    original_meshes = mesh_objects[:]
                    triangulated_count = 0
                    for mesh in original_meshes:
                        # 获取形状节点
                        shapes = cmds.listRelatives(mesh, shapes=Tue, fullPath=True) or []
                        for shape in shapes:
                            if cmds.nodeType(shape) == 'mesh':
                                # 确保形状节点不是中间对象
                                if not cmds.getAttr(shape + '.intermediateObject'):
                                    # 使用polyTriangulate命令三角化
                                    cmds.polyTriangulate(mesh, ch=False)
                                    triangulated_count += 1
                    write_log('成功三角化 %d 个模型' % triangulated_count)
                except Exception as e:
                    write_log('三角化模型时出错: ' + str(e))
                    write_log(traceback.format_exc())
                    
            # 创建输出文件路径到子文件夹
            file_name = ns.replace(':', '_') + '.abc'
            abc_file_path = os.path.join(subfolder_path, file_name)

            # 导出ABC
            write_log('正在导出: ' + abc_file_path)
            try:
                # 直接选择所有模型对象
                cmds.select(mesh_objects, replace=True)
                # 使用singleExport导出，保持原始名称
                singleExport.SingleExport.exportSelection(abc_file_path, start_frame, end_frame)
                write_log('导出成功: ' + abc_file_path)
                total_exported_objects += len(mesh_objects)
            except Exception as e:
                write_log('导出ABC时出错: ' + str(e))
                write_log(traceback.format_exc())

        except Exception as e:
            write_log('处理 ' + ns + ' 时出错: ' + str(e))
            write_log(traceback.format_exc())

    write_log('导出统计：总共导出 ' + str(total_exported_objects) + ' 个对象，共 ' + str(len(found_cache_groups)) + ' 个命名空间')
    update_progress(100, '所有ABC导出完成！')
    write_log('所有ABC导出完成！')

except Exception as e:
    error_trace = traceback.format_exc()
    write_log('发生错误: ' + str(e) + '\n' + error_trace)
    sys.stderr.write('错误: ' + str(e) + '\n' + error_trace + '\n')
    sys.exit(1)
finally:
    write_log('关闭Maya独立模式...')
    # 关闭Maya
    try:
        maya.standalone.uninitialize()
        write_log('Maya独立模式已关闭')
    except:
        write_log('关闭Maya时出错') 