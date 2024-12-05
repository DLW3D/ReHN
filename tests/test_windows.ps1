###########
#  Build  #
###########
conda activate py
python -m build

###########
# Windows #
###########
# env
conda create -n rehn_test python -y
conda activate rehn_test

# install
pip install -e .

# test ReHN
mkdir samples/outputs -Force
python src/rehn/main.py -i "samples/HX_sample_with_ground.ply" -o "samples/outputs/HXs_ReHN.ply" --dem_save_path "samples/outputs/HXs_ReHN.npy" --replace_z True --re_hn_resolution 0.5 --dem_resolution 1 --n_k 10
rehn -i "samples/HX_sample_with_ground.ply" -o "samples/outputs/HXs_ReHN.ply" -m "samples/outputs/HXs_ReHN.npy"

# test CSF+ReHN
pip install -r requirements.txt
python src/rehn/main.py -i "samples/HX_sample_with_ground.ply" -o "samples/outputs/HXs_CSF.ply" --dem_save_path "samples/outputs/HXs_CSF.npy" --use_re_h False
rehn -i "samples/HX_sample_with_ground.ply" -o "samples/outputs/HXs_CSF_ReHN.ply" --dem_save_path "samples/outputs/HXs_CSF_ReHN.npy" --ground_feature_name X

# clean
pip freeze > temp_pakeges.txt
pip uninstall -r temp_pakeges.txt -y
rm temp_pakeges.txt

# remove env
conda deactivate
conda remove -n rehn_test --all -y


