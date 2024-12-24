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

# install rehn
pip install -e .

# test ReHN
mkdir samples/outputs -Force
python src/rehn/main.py -i "samples/HX_sample_with_ground.ply" -o "samples/outputs/HXs_ReHN.ply" --dem_save_path "samples/outputs/HXs_ReHN.npy" --replace_z True --export_ground False --re_hn_resolution 0.5 --dem_resolution 1 --n_k 10
rehn -i "samples/HX_sample_with_ground.ply" -o "samples/outputs/HXs_ReHN.ply" -m "samples/outputs/HXs_ReHN.npy"

# clean
pip freeze > temp_pakeges.txt
pip uninstall -r temp_pakeges.txt -y
rm temp_pakeges.txt

# install rehn[csf]
pip install -e .[csf]

# test CSF+ReHN
python src/rehn/main.py -i "samples/HX_sample_with_ground.ply" -o "samples/outputs/HXs_CSF.ply" --dem_save_path "samples/outputs/HXs_CSF.npy" --use_re_h False
rehn -i "samples/HX_sample_with_ground.ply" -o "samples/outputs/HXs_CSF_ReHN.ply" --dem_save_path "samples/outputs/HXs_CSF_ReHN.npy" --ground_feature_name X

# remove env
conda deactivate
conda remove -n rehn_test --all -y


