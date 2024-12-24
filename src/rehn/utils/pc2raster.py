"""
Projection of point cloud to raster
part of ReHN
github.com/DLW3D
2022/12/19
"""


import numpy as np


def fnv_hash_vec(arr):
    """
    FNV64-1A
    """
    assert arr.ndim == 2
    # Floor first for negative coordinates
    arr = arr.copy()
    arr = arr.astype(np.uint64, copy=False)
    hashed_arr = np.uint64(14695981039346656037) * \
                 np.ones(arr.shape[0], dtype=np.uint64)
    for j in range(arr.shape[1]):
        hashed_arr *= np.uint64(1099511628211)
        hashed_arr = np.bitwise_xor(hashed_arr, arr[:, j])
    return hashed_arr


def index_rasterize(coord, raster_size, center_boundary=True):
    """
    Construct raster index from point cloud (used for rasterizing point cloud)
    :param coord: 2d array (N, 1~2) Coordinates
    :param raster_size: float Size of the raster
    :param center_boundary: bool True: Align the edge of the point cloud to the center of the raster; False: Align the edge of the point cloud to the edge of the raster
    :return: raster_num: int Number of rasters (excluding empty rasters)
             raster_shape: array(2 * int) Shape of the raster
             idx_sort: 1d array Sorted indices of the point cloud
             idx_select: 1d array Starting index of each raster (for the sorted point cloud)
             raster_count: 1d array Number of points in each raster
             raster_pos: tuple(2 * 1d array) Coordinate indices i, j of each raster
    --------
    sample:
        pc = load_pc(pc_path)   # N, 3
        raster_num, raster_shape, idx_sort, idx_select, raster_count, raster_pos = index_rasterize(pc[:, :2], raster_size=0.2)
        pc = pc[idx_sort]  # Sort the point cloud according to the raster index (to make points in the same raster adjacent)
        features = np.zeros((raster_num, 1), dtype=np.float32)  # Create a new 1d raster feature
        for i in range(raster_num):
            pc_in_cell = pc[idx_select[i]: idx_select[i] + raster_count[i]]  # Index points in each raster
            features[i] = pc_in_cell[:, 2].max()  # Calculate the maximum Z value for each raster <--- Your requirement
        raster = np.zeros((*raster_shape, 1), dtype=np.float32) * np.nan  # 2d raster
        raster[raster_pos] = features  # Convert to 2d based on the index
        idx_sort_reverse = np.argsort(idx_sort)  # Reverse sorting index
        pc = pc[idx_sort_reverse]  # Restore the original order of the point cloud
    """
    coord = coord - coord.min(axis=0, keepdims=True)  # Align the origin of the coordinates to the minimum coordinate
    if center_boundary:
        # Point cloud 00 coordinate corresponds to the center of raster 00
        discrete_coord = np.round(coord / np.array(raster_size))  # Discretize coordinates
        raster_shape = (np.round(coord.max(0) / raster_size + 1)).astype(np.int32)  # Calculate the number of rasters
    else:
        # Point cloud 00 coordinate corresponds to the bottom-left corner of raster 00
        discrete_coord = coord // np.array(raster_size)  # Discretize coordinates
        raster_shape = (np.ceil(coord.max(0) / raster_size)).astype(np.int32)  # Calculate the number of rasters
    if discrete_coord.ndim == 1:
        key = discrete_coord.astype(np.uint64)  # Calculate hash values to convert coordinates to indices
    else:
        key = fnv_hash_vec(discrete_coord)  # Calculate hash values to convert coordinates to indices
    idx_sort = np.argsort(key)  # Sort indices of the point cloud based on coordinates
    key_sort = key[idx_sort]  # Sorted hash values
    _, raster_idx, raster_count = np.unique(key_sort, return_counts=True, return_inverse=True)  # Calculate raster indices and the number of points in each raster (excluding empty rasters)
    raster_count = raster_count.astype(np.int32)  # Number of points in each raster
    raster_num = len(raster_count)  # Number of rasters
    idx_select = np.cumsum(np.insert(raster_count, 0, 0)[0:-1]).astype(np.int32)  # Calculate the starting index of each raster
    idx_unique = idx_sort[idx_select]
    raster_pos = discrete_coord[idx_unique].astype(np.int32).T  # Coordinate positions of each raster
    return raster_num, raster_shape, idx_sort, idx_select, raster_count, tuple(raster_pos)
