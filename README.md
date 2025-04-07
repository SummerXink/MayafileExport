# Maya工具集

这是一个为Maya 2020和Python 2.7环境开发的工具集，主要用于Alembic导出、相机FBX导出以及材质处理。

## 主要功能

### Alembic导出工具

- **alembicExport.py**: 基础Alembic导出功能，包含设置帧范围、文件路径、对象复制等功能
- **singleExport.py**: 单个选择集的Alembic导出工具
- **multiExport.py**: 多个选择集的批量Alembic导出工具

### 相机FBX导出工具

- **camFbxExport.py**: 用于导出Maya场景中的相机到FBX格式，支持世界空间导出

### 材质处理工具

- **setShadersTool.py**: 为Unreal Alembic缓存设置材质到对象的面
- **renameShadingGroup.py**: 将选定的着色组重命名为连接的材质名称

### 配置管理

- **constants.py**: 管理导出设置、对象命名和默认参数等常量
- **constants.json**: 存储常量的JSON配置文件

## 使用方法

### Alembic导出

1. 在Maya中创建选择集，命名应符合`constants.json`中定义的`exportSetName`格式
2. 使用`singleExport.py`或`multiExport.py`中的方法进行导出

```python
# 单个选择集导出
from singleExport import SingleExport
SingleExport.exportSelection("输出路径.abc", 开始帧, 结束帧)

# 多个选择集批量导出
from multiExport import MultiExport
MultiExport.exportSelectionSets(导出集输出字典, 开始帧, 结束帧)
```

### 相机FBX导出

```python
from camFbxExport import export_all_cameras
export_all_cameras("输出目录路径", add_border_keys=True)
```

### 材质处理

```python
# 设置材质到面
from setShadersTool import SetShader
SetShader()

# 重命名着色组
from renameShadingGroup import run
run()
```

## 环境要求

- Maya 2020
- Python 2.7

## 注意事项

- 所有工具都基于Maya 2020和Python 2.7开发，不保证在其他版本中正常工作
- 导出Alembic时，对象会被复制并重命名，以防止因命名空间导致的导出失败
- 导出完成后，复制的对象会被自动删除 