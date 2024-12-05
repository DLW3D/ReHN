"""
Re-height normalization (ReHN) algorithm for point cloud height normalization
https://doi.org/10.1016/j.rse.2024.114160
Usage:
    python ReHN.py -i point_cloud.ply -o point_cloud_norm.ply -m dem.npy
Author:
    github.com/DLW3D
    2024/12/1
"""

import argparse
import numpy as np
from pykdtree.kdtree import KDTree
from rehn.utils.ply import read_ply, write_ply
from rehn.utils.pc2raster import index_rasterize


def height_norm_f(pc_path,
                  save_path,
                  dem_save_path: str = None,
                  ground_feature_name: str = 'scalar_is_ground',
                  ground_mask_path: str = None,
                  dem_resolution: float = 0.2,
                  n_k: int = 300,
                  export_ground: bool = True,
                  replace_z: bool = False,
                  **kwargs):
    """
    Wrapper for height_norm for command line calls
    :param pc_path: Path to the point cloud file to be normalized (PLY format)
    :param save_path: Path to save the normalized point cloud file (PLY format)
    :param dem_save_path: Path to save the DEM file (npy format)
    :param ground_feature_name: Name of the ground point feature in the point cloud
    :param ground_mask_path: If ground points are not included and CSF is not used, provide the path to the file saving the ground point features (binary 1D-Array npy format)
    :param dem_resolution: DEM resolution
    :param n_k: Number of neighboring points used for inverse distance weighted interpolation
    :param export_ground: Whether to output ground point information as a feature
    :param replace_z: Whether to replace the original z value with the normalized height value
    """
    print('Loading data...')
    pc_data = read_ply(pc_path)
    xyz = np.vstack([pc_data['x'], pc_data['y'], pc_data['z']]).T

    # Try to get the ground point mask
    ground_mask = None
    if ground_feature_name in pc_data.dtype.names:
        ground_mask = pc_data[ground_feature_name].astype(np.bool_)
    elif ground_mask_path:
        ground_mask = np.load(ground_mask_path).astype(np.bool_)
        assert len(ground_mask) == len(xyz), 'The number of ground point features does not match the number of points in the point cloud!'

    print('Starting height normalization...')
    norm_z, ground_mask = height_norm(xyz, ground_mask, n_k=n_k, **kwargs)

    if dem_save_path:
        print('Calculating DEM...')
        dem = count_dem(xyz, ground_mask, dem_resolution, n_k)
        np.save(dem_save_path, dem)


    print('Saving results...')
    # Organize additional features
    other_feature = []
    other_feature_name = []
    if export_ground:
        other_feature.append(ground_mask.astype(np.uint8))
        other_feature_name.append(ground_feature_name)
    # Save results
    if replace_z:
        write_ply(save_path,
                  [norm_z if n == 'z' else pc_data[n] for n in pc_data.dtype.names[:-1] if n not in other_feature_name] + [pc_data['z']] + other_feature,
                  [n for n in pc_data.dtype.names[:-1] if n not in other_feature_name] + ['original_z'] + other_feature_name)
    else:
        write_ply(save_path,
                  [pc_data[n] for n in pc_data.dtype.names if n not in other_feature_name] + [norm_z] + other_feature,
                  [n for n in pc_data.dtype.names if n not in other_feature_name] + ['norm_z'] + other_feature_name)
    return


def height_norm(xyz: np.ndarray,
                ground_mask: np.ndarray = None,
                use_re_hn=True,
                re_hn_resolution=0.2,
                zoom_resolution=7,
                n_k=300,
                bSloopSmooth=True,
                cloth_resolution=0.5,
                rigidness=2,
                time_step=0.65,
                interations=500,
                class_threshold=0.1,
                ):
    """
    Point cloud height nromalization using the Re-height normalization algorithm (ReHN)
    :param xyz: np.array2d (N, 3) Point cloud coordinates
    :param ground_mask: np.array1d (N,) Binary feature: whether it is a ground point, if not provided, CSF is used to calculate
    :param use_re_hn: Whether to use ReHN to re-interpolate ground points
    :param re_hn_resolution: ReHN grid resolution
    :param zoom_resolution: ReHN resolution zoom times
    :param n_k: Number of neighboring points used for inverse distance weighted interpolation
    :param bSloopSmooth: Whether CSF performs slope smoothing
    :param cloth_resolution: CSF grid resolution
    :param rigidness: CSF grid rigidity
    :param time_step: CSF step size per iteration
    :param interations: CSF number of iterations
    :param class_threshold: CSF classification threshold
    :return: None
    """
    if ground_mask is None:
        print('CSF ground point filtering...')
        ground_mask = run_csf(xyz, bSloopSmooth, cloth_resolution, rigidness, time_step, interations, class_threshold)

    if use_re_hn:
        print('Executing ReHN algorithm...')
        xyz, ground_mask = run_re_hn(xyz, ground_mask, re_hn_resolution, zoom_resolution)

    print('Performing inverse distance weighted interpolation...')
    ground_xy = xyz[ground_mask, :2]  # Ground point xy coordinates
    ground_z = xyz[ground_mask, 2]  # Ground height value
    all_ground_z = inv_dis_interpolation(ground_xy, ground_z, xyz[:, :2], n_k)  # Calculate the height of the ground point corresponding to all points
    norm_z = xyz[:, 2] - all_ground_z  # Normalized height
    norm_z = np.clip(norm_z, 0, None)  # Clip negative values to 0

    return norm_z, ground_mask


def run_re_hn(xyz, ground_mask, re_hn_resolution, zoom_resolution):
    """
    Re-height normalization (ReHN)
    Implementation of the Re-height normalization (ReHN) method from the paper [1].
    [1] https://doi.org/10.1016/j.rse.2024.114160
    :param xyz: np.array2d (N, 3) Point cloud coordinates
    :param ground_mask: np.array1d (N,) Binary feature: whether it is a ground point
    :param re_hn_resolution: float Grid resolution (recommended to be the same as the minimum point spacing in the point cloud, larger values can reduce computation but may result in points below the ground)
    :param zoom_resolution: int Resolution zoom times (initial resolution = resolution * 2^zoom_times, this mechanism is used to improve computational efficiency)
    """
    ### ReHN Step (1): Divide the grid and take the lowest point in each grid as the initial ground point
    ground_resolution = re_hn_resolution  # 初始化栅格采样分辨率
    # Index point cloud
    raster_num, raster_shape, idx_sort, idx_select, raster_count, raster_pos = \
        index_rasterize(xyz[:, :2], ground_resolution, center_boundary=False)
    idx_sort_rev = np.argsort(idx_sort)
    # Sort point cloud
    xyz = xyz[idx_sort]
    ground_mask = ground_mask[idx_sort]
    # Grid filtering, only take the lowest point in each grid as the ground point
    new_ground_mask = np.zeros_like(ground_mask)
    for cls in range(raster_num):
        vox_ground = ground_mask[idx_select[cls]: idx_select[cls] + raster_count[cls]]
        if 1 in vox_ground:
            vox_z = xyz[idx_select[cls]: idx_select[cls] + raster_count[cls], 2]
            new_ground_mask[idx_select[cls] + np.argmin(vox_z)] = True
    ground_mask = new_ground_mask
    del new_ground_mask
    # Restore original point cloud order
    xyz = xyz[idx_sort_rev]
    ground_mask = ground_mask[idx_sort_rev]
    print(f'Initialized {np.sum(ground_mask)} ground points, starting iteration for supplement ignored ground points...')

    ### ReHN Step (2)-(3): Iteratively calculate ignored ground points (points lower than the interpolated plane),
    ### then re-interpolate to obtain accurate height normalization values
    min_resolution = re_hn_resolution  # Final grid resolution
    cur_resolution = min_resolution * 2 ** zoom_resolution  # Initial grid resolution
    idx_sort_rev = None
    while True:
        # Inverse distance weighted interpolation
        ground_z = inv_dis_interpolation(xyz[ground_mask, :2], xyz[ground_mask, 2], xyz[:, :2], n_k=5, snap_dist=1e-3)
        # Check if there are ignored ground points (points lower than the interpolated plane)
        ext_grounds = ground_z > xyz[:, 2]  # Possible ground points
        print(f'Found {np.sum(ext_grounds)} possible ground points')
        if not np.any(ext_grounds):
            print('No ignored ground points, iteration ends!')
            break
        # Add only the lowest ground point in each grid
        if cur_resolution > min_resolution:
            # Restore original point cloud order before next sorting
            if idx_sort_rev is not None:
                xyz = xyz[idx_sort_rev]
                ground_mask = ground_mask[idx_sort_rev]
                ext_grounds = ext_grounds[idx_sort_rev]
            # Decrease resolution to make low points smoother
            cur_resolution /= 2
            if cur_resolution < min_resolution:
                cur_resolution = min_resolution
            print(f'Current resolution: {cur_resolution}')
            # Index point cloud
            raster_num, raster_shape, idx_sort, idx_select, raster_count, raster_pos = \
                index_rasterize(xyz[:, :2], cur_resolution, center_boundary=False)
            idx_sort_rev = np.argsort(idx_sort)
            # Sort point cloud
            xyz = xyz[idx_sort]
            ground_mask = ground_mask[idx_sort]
            ext_grounds = ext_grounds[idx_sort]
        # Find the lowest point in each grid of possible ground points as additional ground points
        for cls in np.arange(raster_num)[raster_count > 1]:
            vox_ext = ext_grounds[idx_select[cls]: idx_select[cls] + raster_count[cls]]
            if np.sum(vox_ext) < 2:
                continue  # No conflict
            vox_z = xyz[idx_select[cls]: idx_select[cls] + raster_count[cls], 2]
            min_idx = np.where(vox_z == np.min(vox_z[vox_ext]))[0]
            ext_grounds[idx_select[cls]: idx_select[cls] + raster_count[cls]] = False
            ext_grounds[idx_select[cls] + min_idx] = True
        print(f'Added {np.sum(ext_grounds)} additional ground points')
        ground_mask[ext_grounds] = True  # Add ignored ground points to ground points
    # Restore original point cloud order
    if idx_sort_rev is not None:
        xyz = xyz[idx_sort_rev]
        ground_mask = ground_mask[idx_sort_rev]
    return xyz, ground_mask


def run_csf(xyz, bSloopSmooth, cloth_resolution, rigidness, time_step, interations, class_threshold):
    """
    Detated ground points using cloth simulation filtering algorithm (CSF)[2]
    [2] https://doi.org/10.3390/rs8060501
    """
    import CSF
    csf = CSF.CSF()
    csf.setPointCloud(xyz.astype(np.float64))
    # CSF parameters
    csf.params.bSloopSmooth = bSloopSmooth    # Whether to perform slope smoothing
    csf.params.cloth_resolution = cloth_resolution  # Grid resolution (meters)
    csf.params.rigidness = rigidness  # Grid rigidity
    # The following three are best kept as default
    csf.params.time_step = time_step  # Step size per iteration
    csf.params.interations = interations  # Number of iterations
    csf.params.class_threshold = class_threshold  # Classification threshold

    ground_idx = CSF.VecInt()   # Ground point index
    non_ground_idx = CSF.VecInt()   # Non-ground point index
    csf.do_filtering(ground_idx, non_ground_idx)  # Perform ground filtering
    ground_idx = np.array(ground_idx)  # Ground point index
    assert len(ground_idx) > 1, 'CSF error, no ground points found!'
    ground_mask = np.zeros(len(xyz), dtype=np.bool_)  # Feature: whether it is a ground point
    ground_mask[ground_idx] = True
    return ground_mask


def inv_dis_interpolation(base_xy, base_v, inter_xy, n_k=10, snap_dist=None, solve_conflict=True, solve_type='min'):
    """
    Inverse Distance Weighted Interpolation
    :param base_xy: np.array2d (n, 2) Coordinates of the base points
    :param base_v: np.array (n,) Values of the base points
    :param inter_xy: np.array2d (m, 2) Coordinates of the points to be interpolated
    :param n_k: int Number of neighboring points used for interpolation
    :param snap_dist: float If a point is closer than this distance, it will be snapped to the nearest point
    :param solve_conflict: bool Whether to resolve conflicts (multiple points being the closest), should be disabled for better performance if not needed
    :param solve_type: 'max' or 'min' When resolving conflicts, choose the maximum or minimum value
    :return: np.array (m,) Interpolated results
    """
    kdtree = KDTree(base_xy)
    dist, idx = kdtree.query(inter_xy, k=n_k)
    if n_k == 1:
        result = base_v[idx].squeeze()
    else:
        if snap_dist is None:
            weight = 1 / (dist + 1e-6)
            result = np.sum(weight * base_v[idx], axis=1) / np.sum(weight, axis=1)
        else:
            shape = [*base_v.shape]
            shape[0] = len(idx)
            result = np.zeros(shape, dtype=base_v.dtype)
            snap = dist < snap_dist  # Points to be snapped (point-target matrix)
            snap_point_m = np.any(snap, axis=-1)  # Mask of points to be snapped
            # Resolve conflicts (multiple points being the closest)
            if solve_conflict:
                max_conflict = np.sum(snap, axis=1).max()  # Maximum number of conflicts for a single point
                while max_conflict > 1:
                    conflict_m = snap[:, max_conflict - 1]  # Mask of points with the maximum conflicts
                    conflict_i = idx[conflict_m, :max_conflict]  # Indices of conflicting points
                    conflict_v = base_v[conflict_i]  # Values of conflicting points
                    # Resolve conflicts (construct the correct mask to cover the conflict mask)
                    conflict_choice_i = np.argmax(conflict_v, axis=1) if solve_type == 'max' else np.argmin(conflict_v, axis=1)
                    conflict_resolved_m = np.zeros(conflict_i.shape, dtype=np.bool_)
                    conflict_resolved_m[np.arange(len(conflict_choice_i)), conflict_choice_i] = True
                    snap[conflict_m, :max_conflict] = conflict_resolved_m
                    # Recalculate conflicts
                    max_conflict = np.sum(snap, axis=1).max()
                result[snap_point_m] = base_v[idx[snap]]  # Snap to the nearest point
            else:
                result[snap_point_m] = base_v[idx[snap_point_m, 0]]
            weight = 1 / (dist[~snap_point_m] + 1e-6)
            result[~snap_point_m] = np.sum(weight * base_v[idx[~snap_point_m]], axis=1) / np.sum(weight, axis=1)
    return result


def count_dem(xyz, ground_mask, raster_size=0.2, n_k=300):
    """
    Calculate DEM (Digital Elevation Model)
    :param xyz: np.array2d (N, 3) Point cloud coordinates
    :param ground_mask: np.array1d (N,) Binary feature: whether it is a ground point
    :param dem_save_path: str Path to save the DEM file (npy format)
    :param raster_size: float Size of the raster
    :param n_k: int Number of neighboring points used for inverse distance weighted interpolation
    """
    raster_num, raster_shape, idx_sort, idx_select, raster_count, raster_pos = \
        index_rasterize(xyz[:, :2], raster_size, center_boundary=True)
    # Sort the point cloud
    xyz = xyz[idx_sort]
    ground_mask = ground_mask[idx_sort]
    # Raster inverse distance weighted interpolation
    dem = inv_dis_interpolation((xyz[ground_mask, :2] - xyz[:, :2].min(0, keepdims=True)) / raster_size,
                                xyz[ground_mask, 2], np.indices(raster_shape).reshape(2, -1).T.astype(np.float32),
                                n_k=n_k, snap_dist=1e-3)
    dem = dem.reshape(raster_shape)
    # If the lowest point in the raster is lower, use the lowest point in the raster
    for cls in range(raster_num):
        lowest_z = xyz[idx_select[cls]: idx_select[cls] + raster_count[cls], 2].min()
        if lowest_z < dem[raster_pos[0][cls], raster_pos[1][cls]]:
            dem[raster_pos[0][cls], raster_pos[1][cls]] = lowest_z
    return dem.T[::-1]


def main():
    # Command line arguments
    parser = argparse.ArgumentParser(
        prog='ReHN',
        description='Height normalization of point cloud using Re-height normalization (ReHN) algorithm '
                    'https://doi.org/10.1016/j.rse.2024.114160'
    )

    arg1 = parser.add_argument_group('BASE', 'Basic parameters')
    arg1.add_argument('-i', '--pc_path', type=str, required=True,
                      help='Path to the input point cloud (PLY format)')
    arg1.add_argument('-o', '--save_path', type=str, required=True,
                      help='Path to save the output point cloud (PLY format)')
    arg1.add_argument('-m', '--dem_save_path', type=str, default=None,
                      help='Path to save the DEM (npy format)')
    arg1.add_argument('-mr', '--dem_resolution', type=float, default=0.2,
                      help='DEM resolution')
    arg1.add_argument('-f', '--ground_feature_name', type=str, default='scalar_is_ground',
                      help='Name of the ground point feature in the point cloud')
    arg1.add_argument('-g', '--ground_mask_path', type=str, default=None,
                     help='If the point cloud does not contain ground point features, provide the path to the file saving the ground point features (binary 1D-Array npy format), otherwise use CSF to calculate')
    arg1.add_argument('-r', '--use_re_hn', type=bool, default=True,
                      help='Whether to use Re-height normalization')
    arg1.add_argument('-z', '--replace_z', type=bool, default=False,
                      help='Whether to replace the original z value with the normalized height value (otherwise store as a new feature norm_z)')
    arg1.add_argument('-n', '--n_k', type=int, default=300, help='Number of neighboring points used for inverse distance weighted interpolation')
    arg1.add_argument('-e', '--export_ground', type=bool, default=True,
                      help='Whether to output ground point information as a feature')

    arg2 = parser.add_argument_group('CSF', 'CSF algorithm parameters')
    arg2.add_argument('--bSloopSmooth', type=bool, default=True, help='Whether CSF performs slope smoothing (True)')
    arg2.add_argument('--cloth_resolution', type=float, default=0.5, help='CSF grid resolution (recommended to be fixed at 0.5)')
    arg2.add_argument('--rigidness', type=int, default=2, help='CSF grid rigidity (choose one of 1, 2, 3)')
    arg2.add_argument('--time_step', type=float, default=0.65, help='CSF step size per iteration (recommended to be fixed at 0.65)')
    arg2.add_argument('--interations', type=int, default=500, help='Number of CSF iterations (recommended 500)')
    arg2.add_argument('--class_threshold', type=float, default=0.1, help='CSF classification threshold (recommended 0.5)')

    arg3 = parser.add_argument_group('ReHN', 'ReHN algorithm parameters')
    arg3.add_argument('--re_hn_resolution', type=float, default=0.2,
                      help='ReHN grid resolution (meters), recommended to be the same as the minimum point spacing in the point cloud, larger values can reduce computation but may result in points below the ground')
    arg3.add_argument('--zoom_resolution', type=int, default=7,
                      help='ReHN resolution zoom times, initial resolution = grid resolution * 2^zoom_times (depends on the point cloud area, used to improve computational efficiency)')

    args = parser.parse_args()

    height_norm_f(**vars(args))

    print(f'DONE! CSF normalization completed, results saved to {args.save_path}')


if __name__ == '__main__':
    main()