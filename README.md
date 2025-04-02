# Maya文件导出工具

这是一个用于Maya的文件导出工具集，支持多种格式的导出功能。

## 功能特点

- FBX导出
- Alembic导出
- 批量导出
- 独立导出工具
- 材质设置工具

## 安装说明

1. 将脚本文件夹复制到Maya的scripts目录下
2. 在Maya的userSetup.py中添加以下代码：
```python
import menuBar
menuBar.create_menu()
```

## 使用方法

1. 启动Maya后，在菜单栏中会出现"Export Tools"选项
2. 选择需要的导出工具
3. 按照界面提示进行操作

## 依赖项

- Maya 2020或更高版本
- Python 2.7或更高版本 