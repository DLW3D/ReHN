ReHN: Point Cloud _Re_-Height Normalization
=======================
<div>
    <img src="https://github.com/DLW3D/ReHN/blob/main/samples/images/pc_rgb.jpg" width = "250" /><img src="https://github.com/DLW3D/ReHN/blob/main/samples/images/pc_z.jpg" width = "250" /><img src="https://github.com/DLW3D/ReHN/blob/main/samples/images/pc_norm_z.jpg" width = "250" />
</div>

## Introduction
This repository contains the python implementation of point cloud _Re_-Height Normalization (ReHN). The code is based on the paper:

Fu, B., Deng, L., Sun, W., He, H., Li, H., Wang, Y., Wang, Y., 2024. Quantifying vegetation species functional traits along hydrologic gradients in karst wetland based on 3D mapping with UAV hyperspectral point cloud. Remote Sens. Environ. 307, 114160. 10.1016/j.rse.2024.114160.
https://www.sciencedirect.com/science/article/pii/S0034425724001718

### What it contains?
- A python package `rehn`
- A command line tool `rehn`
- A sample point cloud data `samples/HX_sample_with_ground.ply`, from Guilin University of Technology, Fu Bolin's team. 

You can simply use the command line tool for point cloud height normalization, or use the python package to integrate the height normalization into your own code.


## Installation
### Install from PyPI
```bash
pip install rehn
```

### Install from source
#### Windows or Linux
```bash
git clone https://github.com/DLW3D/ReHN.git
cd ReHN
pip install -e .
# pip install -e . -i https://pypi.mirrors.ustc.edu.cn/simple
```

## Usage

### Use as a command line tool
Make sure you have add the **python bin path** to the system environment variable PATH.
you can find it by Windows:`where.exe python`, Linux:`which python`.

The python bin path may look like: 
- Windows: `C:\Users\username\AppData\Local\Programs\Python\Python39\Scripts`
- Linux: `/etc/miniconda3/envs/env_name/bin`

Run the following command to normalize the point cloud:
```bash
rehn -i samples/HX_sample_with_ground.ply -o samples/outputs/HXs_ReHN.ply -n samples/outputs/HXs_ReHN.npy
```

#### Options
- `-i` or `--pc_path`: **Required:** Path to the input point cloud (PLY format) 
- `-o` or `--save_path`: **Required:** Path to save the output point cloud (PLY format)
- `-m` or `--dem_save_path`: Path to save the DEM (npy format), default=`None`
- `-mr` or `--dem_resolution`: Resolution of the DEM, default=`0.2` meters
- `-f` or `--ground_feature_name`: Name of the ground point feature in the point cloud, default=`scalar_is_ground`
- See more options by `rehn -h`

### Use as a Python package

```python
from rehn import height_norm_f
height_norm_f('samples/HX_sample_with_ground.ply', 
              'samples/outputs/HXs_ReHN.ply', 
              'samples/outputs/HXs_ReHN.npy',)
```
or
```python
from rehn import height_norm, count_dem
xyz = ...  # Load point cloud data
ground_mask = ...  # Load basic ground mask
norm_z, ground_mask = height_norm(xyz, ground_mask)
dem = count_dem(xyz, ground_mask)
```

## Requirements
- pykdtree
- cloth-simulation-filter  (CSF) (**Optional**: you need it if you don't have potential ground labels）
- numpy < 2  (if you don't need CSF, free to use numpy >= 2)


## Citation
If you find this work useful, please consider citing the following paper:
```
@article{FU2024114160,
author = {Bolin Fu and Liwei Deng and Weiwei Sun and Hongchang He and Huajian Li and Yong Wang and Yeqiao Wang},
title = {Quantifying vegetation species functional traits along hydrologic gradients in karst wetland based on 3D mapping with UAV hyperspectral point cloud},
journal = {Remote Sensing of Environment},
year = {2024},
}
```
