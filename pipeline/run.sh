FILE_PATH=./data/my_first_book_for_extraction.json
MODEL="gpt-4o"
DATA_DIR="data_gen"
TASK_TYPE="multi_choice"

python 01_profile_generation.py --file_path $FILE_PATH

python 02_chapter_seg.py --file_path $FILE_PATH

python 03_behavior_ext.py --file_path $FILE_PATH

python 04_behavior_meaningful.py --file_path $FILE_PATH

python 05_context_refined.py --file_path $FILE_PATH

python 06_disturbance_gen.py --file_path $FILE_PATH

python 07_aggregation.py --file_path $FILE_PATH

python 08_evaluation.py --file_path $FILE_PATH --model_name $MODEL --task_type $TASK_TYPE

python 09_calculate_result.py --model_name $MODEL --data_dir $DATA_DIR