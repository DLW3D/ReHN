ReHN: Point Cloud _Re_-Height Normalization
=======================
<div>
    <img src="https://github.com/DLW3D/ReHN/blob/main/samples/images/pc_rgb.jpg" width = "250" /><img src="https://github.com/DLW3D/ReHN/blob/main/samples/images/pc_z.jpg" width = "250" /><img src="https://github.com/DLW3D/ReHN/blob/main/samples/images/pc_norm_z.jpg" width = "250" />
</div>

**English** | [中文](https://github.com/DLW3D/ReHN/blob/main/README_zh.md)

### What it contains?
- A python package `rehn`
- A command line tool `rehn`
- A sample point cloud data `samples/HX_sample_with_ground.ply`, from Guilin University of Technology, Fu Bolin's team. 

You can simply use the command line tool for point cloud height normalization, or use the python package to integrate the height normalization into your own code.


## Installation
### Install from PyPI
If you have the ground point information of the point cloud, you can install it directly by:
```bash
pip install rehn
```
If you don't have the ground point information of the point cloud, you need to install the CSF dependency together:
```bash
pip install rehn[csf]
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
#### Add the python bin path to PATH
Make sure you have add the **python bin path** to the system environment variable PATH.
you can find it by: 
- Windows: `where.exe python`
- Linux: `which python`

The python bin path may look like: 
- Windows: `C:\Users\username\AppData\Local\Programs\Python\Python39\Scripts`
- Linux: `/etc/miniconda3/envs/env_name/bin`

Run the following command to temporarily add the python bin path to PATH:
- Windows: `set PATH=%PATH%;C:\Users\username\AppData\Local\Programs\Python\Python39\Scripts`
- Linux: `export PATH=$PATH:/etc/miniconda3/envs/env_name/bin`

Replace the path according to your actual situation

#### Run the rehn command
Run the following command to normalize the point cloud:
```bash
rehn -i samples/HX_sample_with_ground.ply -o samples/outputs/HXs_ReHN.ply -n samples/outputs/HXs_ReHN.npy
```

#### Optional arguments
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
- cloth-simulation-filter  (**Optional**: CSF algorithm. You need it if you don't have potential ground labels）
- numpy  (If you need CSF, `numpy < 2` is required)

