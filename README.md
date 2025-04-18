# Maya工具集

这是一个为Maya 2020和Python 2.7环境开发的综合工具集，主要用于Alembic导出、相机FBX导出以及材质处理。

## 主要功能

### Alembic导出工具

- **alembicExport.py**: 提供基础的Alembic导出功能。
- **singleExport.py**: 用于单个选择集的Alembic导出。
- **multiExport.py**: 支持多个选择集的批量Alembic导出。
- **multiABCExportStandalone.py**: 独立运行的Alembic导出工具，支持批量导出，不需要打开Maya界面。

### 相机FBX导出工具

- **CamFbxExport.py**: 导出Maya场景中的相机到FBX格式，支持世界空间导出。
- **multiCamFbxExportUI.py**: 提供相机FBX导出的图形界面工具，支持批量导出，不需要打开Maya界面。

### 材质处理工具

- **setShadersTool.py**: 为Unreal Alembic缓存设置材质到对象的面，使用Maya的两步法创建面集。
- **renameShadingGroup.py**: 将着色组重命名为其连接的材质名称。

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

直接运行`multiABCExportStandalone.py`启动独立的Alembic导出工具，可以不打开Maya界面进行批量导出。

### 相机FBX导出

#### 脚本方式

```python
from CamFbxExport import export_all_cameras

# 导出所有相机
export_all_cameras("C:/output/cameras", add_border_keys=True)
```

#### 图形界面方式

运行`multiCamFbxExportUI.py`启动图形界面，选择Maya文件和输出目录，点击导出按钮进行导出。

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

## 环境要求

- Maya 2020
- Python 2.7
- PySide2 (用于图形界面工具)

## 注意事项

- 所有工具都基于Maya 2020和Python 2.7开发，不保证在其他版本中正常工作。
- `setShadersTool.py`使用Maya标准的两步法创建面集，确保导出的Alembic文件在Unreal中有正确的材质分配。
- 导出工具会使用`constants.json`中定义的参数，可根据需要修改。
- 独立导出工具需要找到正确的Maya路径才能运行。

## 项目结构

- **基础功能模块**: alembicExport.py, constants.py
- **Alembic导出工具**: singleExport.py, multiExport.py, multiABCExportStandalone.py
- **相机导出工具**: CamFbxExport.py, multiCamFbxExportUI.py
- **材质处理工具**: setShadersTool.py, renameShadingGroup.py
- **配置文件**: constants.json
