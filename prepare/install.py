# Copyright (c) Microsoft. All rights reserved.

# Licensed under the MIT license. See LICENSE.md file in the project root
# for full license information.
# ==============================================================================

from __future__ import print_function
from easydict import EasyDict as edict
import zipfile
import os, sys

def prepare_config():
    base_folder = os.path.dirname(os.path.abspath(__file__))
    cfg = __C = edict()
    __C.DATASET_PREPARE = os.path.join(base_folder, '..', 'DataSets', 'prepare')
    __C.DATASET_BASE = os.path.join(base_folder, '..', 'DataSets')
    __C.PRETRAINED_MODEL = os.path.join(base_folder, '..', 'PretrainedModels')
    __C.SSL_PATH = os.path.join(base_folder, '..', 'web', 'ssl')
    __C.SSL_CERT = os.path.join(__C.SSL_PATH, 'cert.pem')
    __C.SSL_KEY = os.path.join(__C.SSL_PATH, 'key.pem')

    print(__file__, base_folder, cfg.DATASET_PREPARE, cfg.DATASET_BASE, cfg.PRETRAINED_MODEL)
    print(cfg.PRETRAINED_MODEL, os.listdir(cfg.PRETRAINED_MODEL))
    print(cfg.DATASET_BASE, os.listdir(cfg.DATASET_BASE))
    print(cfg.DATASET_PREPARE, os.listdir(cfg.DATASET_PREPARE))

    return cfg

def prepare_datasets(cfg):
    print('[INFO] ===========================')
    print('[INFO] STAGE 3: Preparing Datasets')

def prepare_ssl(cfg):
    from mk_certs import make_certs
    if not os.path.exists(cfg.SSL_PATH):
        os.mkdir(cfg.SSL_PATH)
    print('[INFO] =========================================')
    print('[INFO] STAGE 2: Generate self-signed certificate')
    make_certs(cfg)
    

def prepare_model(cfg):
    from download_model import download_model_by_name
    print('[INFO] ==================================')
    print('[INFO] STAGE 1: Download pretrained model')
    download_model_by_name("VGG16_ImageNet_Caffe", cfg.PRETRAINED_MODEL)


if __name__ == '__main__':
    cfg = prepare_config()
    prepare_model(cfg)
    prepare_ssl(cfg)
    prepare_datasets(cfg)