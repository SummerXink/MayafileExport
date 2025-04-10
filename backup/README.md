# Maya工具集

这是一个为Maya 2020和Python 2.7环境开发的综合工具集，主要用于Alembic导出、相机FBX导出以及材质处理。

## 主要功能

### Alembic导出工具

- **alembicExport.py**: 基础Alembic导出功能的实现
- **singleExport.py**: 单个选择集的Alembic导出工具
- **multiExport.py**: 多个选择集的批量Alembic导出工具
- **ABCExportStandalone.py**: 独立运行的Alembic导出工具，不需要打开Maya界面

### 相机FBX导出工具

- **CamFbxExport.py**: 用于导出Maya场景中的相机到FBX格式，支持世界空间导出
- **CamFbxExportUI.py**: 相机FBX导出的图形界面工具，支持批量导出

### 材质处理工具

- **setShadersTool.py**: 为Unreal Alembic缓存设置材质到对象的面，使用Maya的两步法创建面集
- **renameShadingGroup.py**: 将着色组重命名为其连接的材质名称

### 配置管理

- **constants.py**: 管理导出设置、对象命名和默认参数等常量
- **constants.json**: 存储常量的JSON配置文件

## 使用方法

### Alembic导出

#### 单个选择集导出

```python
from singleExport import SingleExport

# 导出选中对象
SingleExport.exportSelection("C:/output/model.abc", 1, 24)  # 开始帧1，结束帧24

# 导出所有带有EXPORT_SET名称的选择集
SingleExport.exportSelectionSets("C:/output/model.abc", 1, 24)
```

#### 多个选择集批量导出

```python
from multiExport import MultiExport

# 自动查找并导出所有选择集
MultiExport.exportDefaultSelectionSets("C:/output/", 1, 24)

# 自定义导出选择集和路径
export_dict = {
    "characterExport_SET": "C:/output/character.abc",
    "propsExport_SET": "C:/output/props.abc"
}
MultiExport.exportSelectionSets(export_dict, 1, 24)
```

#### 独立导出工具

直接运行`ABCExportStandalone.py`启动独立的Alembic导出工具，可以不打开Maya界面进行批量导出。

### 相机FBX导出

#### 脚本方式

```python
from CamFbxExport import export_all_cameras

# 导出所有相机
export_all_cameras("C:/output/cameras", add_border_keys=True)
```

#### 图形界面方式

运行`CamFbxExportUI.py`启动图形界面，选择Maya文件和输出目录，点击导出按钮进行导出。

### 材质处理

#### 设置材质到面

```python
from setShadersTool import SetShader

# 选择几何体后运行
SetShader()
```

#### 重命名着色组

```python
from renameShadingGroup import run

# 选择材质或带有材质的对象后运行
run()
```

## 工具详解

### Alembic导出工具

- 支持指定帧范围导出
- 提供导出前处理和后处理功能
- 可批量导出多个选择集
- 自动处理命名空间和重名问题
- 可以作为独立程序运行，无需打开Maya界面

### 相机FBX导出工具

- 支持世界空间导出，确保相机位置正确
- 自动添加首尾关键帧，提高导入稳定性
- 可以批量导出场景中所有相机
- 提供独立的图形界面，支持离线处理
- 自动处理相机约束和动画

### 材质处理工具

- 使用Maya标准的两步法应用材质：
  1. 先将默认材质应用到整个对象
  2. 再将特定材质应用到面
- 自动创建面集，确保与Unreal引擎兼容
- 提供多种材质获取方法，提高适用性
- 处理命名空间和命名冲突

## 环境要求

- Maya 2020
- Python 2.7
- PySide2 (用于图形界面工具)

## 注意事项

- 所有工具都基于Maya 2020和Python 2.7开发，不保证在其他版本中正常工作
- `setShadersTool.py`使用Maya标准的两步法创建面集，确保导出的Alembic文件在Unreal中有正确的材质分配
- 导出工具会使用`constants.json`中定义的参数，可根据需要修改
- 独立导出工具需要找到正确的Maya路径才能运行

## 项目结构

- **基础功能模块**: alembicExport.py, constants.py
- **Alembic导出工具**: singleExport.py, multiExport.py, ABCExportStandalone.py
- **相机导出工具**: CamFbxExport.py, CamFbxExportUI.py
- **材质处理工具**: setShadersTool.py, renameShadingGroup.py
- **配置文件**: constants.json