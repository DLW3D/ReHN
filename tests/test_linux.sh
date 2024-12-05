###########
#  Build  #
###########
python -m build

###########
#  Linux  #
###########

# install
pip install -e .

# test ReHN
mkdir samples/outputs -p
python src/rehn/main.py -i "samples/HX_sample_with_ground.ply" -o "samples/outputs/HXs_ReHN.ply" --dem_save_path "samples/outputs/HXs_ReHN.npy" --replace_z True --re_hn_resolution 0.5 --dem_resolution 1 --n_k 10
rehn -i "samples/HX_sample_with_ground.ply" -o "samples/outputs/HXs_ReHN.ply" --dem_save_path "samples/outputs/HXs_ReHN.npy"

# test CSF+ReHN
python src/rehn/main.py -i "samples/HX_sample_with_ground.ply" -o "samples/outputs/HXs_CSF.ply" --dem_save_path "samples/outputs/HXs_CSF.npy" --use_re_h False
rehn -i "samples/HX_sample_with_ground.ply" -o "samples/outputs/HXs_CSF_ReHN.ply" --dem_save_path "samples/outputs/HXs_CSF_ReHN.npy" --ground_feature_name X

# clean
pip uninstall ReHN -y
