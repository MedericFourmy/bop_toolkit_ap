#!/usr/bin/env python
import os
import re
import subprocess
import argparse
from tqdm import tqdm

from bop_toolkit_lib import config


# PARAMETERS (some can be overwritten by the command line arguments below).
################################################################################
p = {
    "renderer_type": "vispy",  # Options: 'vispy', 'cpp', 'python'.
    "targets_filename": "test_targets_bop19.json",
    "use_gpu": config.use_gpu,  # Use torch for the calculation of errors.
    "num_workers": config.num_workers,  # Number of parallel workers for the calculation of errors.
}

parser = argparse.ArgumentParser()
parser.add_argument("--renderer_type", default=p["renderer_type"])
parser.add_argument("--targets_filename", default=p["targets_filename"])
parser.add_argument("--num_workers", default=p["num_workers"])
parser.add_argument("--use_gpu", action="store_true", default=p["use_gpu"])
args = parser.parse_args()

p["renderer_type"] = str(args.renderer_type)
p["targets_filename"] = str(args.targets_filename)
p["num_workers"] = int(args.num_workers)
p["use_gpu"] = bool(args.use_gpu)


# Define the input directory
INPUT_DIR = "./bop_toolkit_lib/tests/data/"

# Define the output directory
OUTPUT_DIR = "./bop_toolkit_lib/tests/logs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

log_file_tpath = "{}/eval_bop19_pose_test_{}.txt"


# Define the dataset dictionary
FILE_DICTIONARY = {
    "lmo_megaPose": "cnos-fastsammegapose_lmo-test_16ab01bd-f020-4194-9750-d42fc7f875d2.csv",
    # "icbin_megaPose": "cnos-fastsammegapose_icbin-test_7c9f443f-b900-41bb-af01-09b8eddfc2c4.csv",
    # "tudl_megaPose": "cnos-fastsammegapose_tudl-test_1328490c-bf88-46ce-a12c-a5e5a7712220.csv",
    # "ycbv_megaPose": "cnos-fastsammegapose_ycbv-test_8fe0af14-16e3-431a-83e7-df00e93828a6.csv",
    "tless_megaPose": "cnos-fastsammegapose_tless-test_94e046a0-42af-495f-8a35-11ce8ee6f217.csv",
}

# Note that the expected output of unittests using GT in case of 6D localization can be different than 1.0 due to matching stage
# TODO: split in EXPECTED_OUTPUT_CPU and EXPECTED_OUTPUT_GPU to merge the test files
EXPECTED_OUTPUT = {
    "lmo_megaPose": {
        "bop19_average_recall_vsd": 0.3976885813148789,
        "bop19_average_recall_mssd": 0.49411764705882344,
        "bop19_average_recall_mspd": 0.6067128027681661,
        "bop19_average_recall": 0.49950634371395614,
    },
    "tless_megaPose": {
        "bop19_average_recall_vsd": 0.4574871555347968,
        "bop19_average_recall_mssd": 0.45304374902693445,
        "bop19_average_recall_mspd": 0.5210493538844776,
        "bop19_average_recall": 0.47719341948206956,
    },
}

# Loop through each entry in the dictionary and execute the command
for dataset_method_name, file_name in tqdm(
    FILE_DICTIONARY.items(), desc="Executing..."
):
    log_file_path = log_file_tpath.format(OUTPUT_DIR, dataset_method_name)
    command = [
        "python",
        "scripts/eval_bop19_pose.py",
        "--renderer_type",
        p["renderer_type"],
        "--results_path",
        INPUT_DIR,
        "--eval_path",
        INPUT_DIR,
        "--result_filenames",
        file_name,
        "--num_worker",
        "{}".format(p["num_workers"])
    ]
    if p["use_gpu"]:
        command.append("--use_gpu")
    command_ = " ".join(command)
    print(f"Executing: {command_}")
    with open(log_file_path, "a") as output_file:
        subprocess.run(command, stdout=output_file, stderr=subprocess.STDOUT)
print("Script executed successfully.")


# Check scores for each dataset
for dataset_method_name, _ in tqdm(FILE_DICTIONARY.items(), desc="Verifying..."):
    log_file_path = log_file_tpath.format(OUTPUT_DIR, dataset_method_name)

    # Read the content of the log file
    with open(log_file_path, "r") as log_file:
        last_lines = log_file.readlines()[-7:]

    # Combine the last lines into a single string
    log_content = "".join(last_lines)

    # Extract scores using regular expressions
    scores = {
        key: float(value) for key, value in re.findall(r"- (\S+): (\S+)", log_content)
    }

    # Compare the extracted scores with the expected scores
    for key, expected_value in EXPECTED_OUTPUT[dataset_method_name].items():
        actual_value = scores.get(key)
        if actual_value is not None:
            if actual_value == expected_value:
                print(f"{dataset_method_name}: {key}: {actual_value} - PASSED")
            else:
                print(
                    f"{dataset_method_name}: {key} - FAILED. Expected: {expected_value}, Actual: {actual_value}"
                )
        else:
            print(f"{dataset_method_name}: {key} - NOT FOUND")

print("Verification completed.")
