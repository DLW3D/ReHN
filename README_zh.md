点云重高程归一化算法 (ReHN: Point Cloud _Re_-Height Normalization) 
=======================
<div>
    <img src="https://github.com/DLW3D/ReHN/blob/main/samples/images/pc_rgb.jpg" width = "250" /><img src="https://github.com/DLW3D/ReHN/blob/main/samples/images/pc_z.jpg" width = "250" /><img src="https://github.com/DLW3D/ReHN/blob/main/samples/images/pc_norm_z.jpg" width = "250" />
</div>

[English](https://github.com/DLW3D/ReHN/blob/main/README.md) | **中文**

## 简介
本仓库包含了点云重高度归一化（ReHN）的 Python 实现。代码基于论文：

Fu, B., Deng, L., Sun, W., He, H., Li, H., Wang, Y., Wang, Y., 2024. Quantifying vegetation species functional traits along hydrologic gradients in karst wetland based on 3D mapping with UAV hyperspectral point cloud. Remote Sens. Environ. 307, 114160. doi:10.1016/j.rse.2024.114160.
https://www.sciencedirect.com/science/article/pii/S0034425724001718

### 包含内容
- 一个 Python 包 `rehn`
- 一个命令行工具 `rehn`
- 一个示例点云数据 `samples/HX_sample_with_ground.ply`，来自桂林理工大学付波霖教授团队

您可以简单地使用命令行工具进行点云高度归一化，或者通过导入 Python 包将高度归一化集成到您自己的代码中。

## 安装
### 从 PyPI 安装
如果已有点云的地面点信息，直接使用以下命令安装：
```bash
pip install rehn
```
如果您没有点云的地面点信息，则需要一并安装CSF依赖：
```bash
pip install rehn[csf]
```

### 从源代码安装
#### Windows or Linux
```bash
git clone https://github.com/DLW3D/ReHN.git
cd ReHN
pip install -e .
# 如果需要，可以使用国内镜像源下载安装依赖
# pip install -e . -i https://pypi.mirrors.ustc.edu.cn/simple
```

## 使用方法

### 作为命令行工具使用
#### 将Python二进制目录添加到PATH
确保已将 **python 的二进制目录** 添加到系统环境变量 PATH 中。 您可以通过以下命令找到 Python 的二进制目录路径：
- Windows: `where.exe python`
- Linux: `which python`

Python 的二进制目录路径应该类似于：
- Windows: `C:\Users\username\AppData\Local\Programs\Python\Python39\Scripts`
- Linux: `/etc/miniconda3/envs/env_name/bin`

在命令行中运行以下命令来将 Python 的二进制目录路径临时添加到 PATH：
- Windows: `set PATH=%PATH%;C:\Users\username\AppData\Local\Programs\Python\Python39\Scripts`
- Linux: `export PATH=$PATH:/etc/miniconda3/envs/env_name/bin`

请根据实际情况替换路径

#### 执行rehn命令
运行以下命令来归一化点云：
```bash
rehn -i samples/HX_sample_with_ground.ply -o samples/outputs/HXs_ReHN.ply -n samples/outputs/HXs_ReHN.npy
```

#### 可选参数
- `-i` 或 `--pc_path`: **必需：** 输入点云文件的路径（PLY 格式）
- `-o` 或 `--save_path`: **必需：** 保存输出点云文件的路径（PLY 格式）
- `-m` 或 `--dem_save_path`: 可选：保存数字高程模型（DEM）的路径（npy 格式），默认为`None`
- `-mr` 或 `--dem_resolution`: 可选：数字高程模型的分辨率，默认为`0.2`米
- `-f` 或 `--ground_feature_name`: 可选：点云中地面点特征的名称，默认为`scalar_is_ground`
- 查看更多选项，请使用 `rehn -h`

### 作为 Python 包使用

```python
from rehn import height_norm_f
height_norm_f('samples/HX_sample_with_ground.ply',  # 输入点云文件
              'samples/outputs/HXs_ReHN.ply',       # 输出点云文件
              'samples/outputs/HXs_ReHN.npy',)      # 输出DEM文件
```
或者
```python
from rehn import height_norm, count_dem
xyz = ...  # 加载点云数据
ground_mask = ...  # 加载粗地面点掩模
norm_z, ground_mask = height_norm(xyz, ground_mask)  # 执行高度归一化
dem = count_dem(xyz, ground_mask)  # 计算DEM
```

## 依赖
- pykdtree
- cloth-simulation-filter  (**可选：** CSF算法。如果您没有地面标签，则需要此工具估算地面点)
- numpy  (如需要使用CSF，则要求 `numpy < 2`)


## 引用
如果您觉得这个工作有帮助，请考虑引用以下论文：
```
@article{FU2024114160,
author = {Bolin Fu and Liwei Deng and Weiwei Sun and Hongchang He and Huajian Li and Yong Wang and Yeqiao Wang},
title = {Quantifying vegetation species functional traits along hydrologic gradients in karst wetland based on 3D mapping with UAV hyperspectral point cloud},
journal = {Remote Sensing of Environment},
year = {2024},
}
```
