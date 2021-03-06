#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) IBM Corporation 2018
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This script runs test.py on the output of batch_train.

The input is a list of directories for each problem/model e.g.
experiments/serial_recall/dnc  and executes on every run of the model in
that directory. I.e. if you tell it to run on serial_recall/dnc, it will
process every time you have ever run serial_recall with the DNC. This
should be fixed later.

"""


import os
import sys
import yaml
from multiprocessing.pool import ThreadPool
import subprocess
import numpy as np
from glob import glob
import pandas as pd


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx], idx


def main():
    batch_file = sys.argv[1]
    assert os.path.isfile(batch_file)

    # Load the list of yaml files to run
    with open(batch_file, 'r') as f:
        directory_checkpoints = [l.strip() for l in f.readlines()]
        for foldername in directory_checkpoints:
            assert os.path.isdir(foldername), foldername + " is not a file"

    experiments_list = []
    for elem in directory_checkpoints:
        list_path = os.walk(elem)
        _, subdir, _ = next(list_path)
        for sub in subdir:
            checkpoints = os.path.join(elem, sub)
            experiments_list.append(checkpoints)

    # Keep only the folders that contain validation.csv and training.csv
    experiments_list = [elem for elem in experiments_list if os.path.isfile(
        elem + '/validation.csv') and os.path.isfile(elem + '/training.csv')]
    # check if the files are empty except for the first line
    experiments_list = [elem for elem in experiments_list if os.stat(
        elem + '/validation.csv').st_size > 24 and os.stat(elem + '/training.csv').st_size > 24]

    # Run in as many threads as there are CPUs available to the script
    with ThreadPool(processes=len(os.sched_getaffinity(0))) as pool:
        pool.map(run_experiment, experiments_list)


def run_experiment(path: str):

    # Load yaml file. To get model name and problem name.
    with open(path + '/train_settings.yaml', 'r') as yaml_file:
        params = yaml.load(yaml_file)

    # print path
    print(path)

    valid_csv = pd.read_csv(path + '/validation.csv', delimiter=',', header=0)
    train_csv = pd.read_csv(path + '/training.csv', delimiter=',', header=0)

    # best train point
    index_val_loss = pd.Series.idxmin(train_csv.loss)
    train_episodes = train_csv.episode.values.astype(
        int)  # best train loss argument
    best_train_ep = train_episodes[index_val_loss]  # best train loss argument
    best_train_loss = train_csv.loss[index_val_loss]

    # best valid point
    index_val_loss = pd.Series.idxmin(valid_csv.loss)
    valid_episodes = valid_csv.episode.values.astype(
        int)  # best train loss argument
    best_valid_ep = valid_episodes[index_val_loss]  # best train loss argument
    best_valid_loss = valid_csv.loss[index_val_loss]

    ### Find the best model ###
    models_list3 = glob(path + '/models/model_episode*')
    models_list2 = [os.path.basename(os.path.normpath(e))
                    for e in models_list3]
    models_list = [int(e.split('_')[-1].split('.')[0]) for e in models_list2]

    # check if models list is empty
    if models_list:
        # select the best model
        best_num_model, idx_best = find_nearest(models_list, best_valid_ep)

        last_model, idx_last = find_nearest(models_list, valid_episodes[-1])

        # Run the test
        command_str = "cuda-gpupick -n0 python3 test.py --model {0}".format(
            models_list3[idx_best]).split()
        with open(os.devnull, 'w') as devnull:
            result = subprocess.run(command_str, stdout=devnull)
        if result.returncode != 0:
            print("Testing exited with code:", result.returncode)

    else:
        print('There is no model in checkpoint {} '.format(path))


if __name__ == '__main__':
    main()
