import numpy as np
import os
from os.path import join, exists
from rehn import height_norm_f, height_norm, count_dem
from rehn.utils.ply import read_ply


if __name__ == '__main__':
    pc_path = 'samples/HX_sample_with_ground.ply'
    save_path = 'samples/outputs'
    if not exists(save_path):
        os.makedirs(save_path)

    height_norm_f(pc_path, join(save_path, 'HXs_ReHN.ply'), join(save_path, 'HXs_ReHN.npy'))
    height_norm_f(pc_path, join(save_path, 'HXs_CSF.ply'), join(save_path, 'HXs_CSF.npy'), use_re_hn=False)
    height_norm_f(pc_path, join(save_path, 'HXs_CSF_ReHN.ply'), join(save_path, 'HXs_CSF_ReHN.npy'),
                  ground_feature_name='X')

    pc_data = read_ply(pc_path)
    xyz = np.vstack([pc_data['x'], pc_data['y'], pc_data['z']]).T
    norm_z, ground_mask = height_norm(xyz, None)
    dem = count_dem(xyz, ground_mask)
    print('Pass!')
