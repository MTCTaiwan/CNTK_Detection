# ==============================================================================
# Copyright (c) Microsoft. All rights reserved.

# Licensed under the MIT license. See LICENSE.md file in the project root
# for full license information.
# ==============================================================================

from __future__ import print_function
from easydict import EasyDict as edict
import zipfile
import os, sys
import docker

def prepare_config():
    base_folder = os.path.dirname(os.path.abspath(__file__))
    cfg = __C = edict()
    __C.PREPARE = '/data/prepare'
    __C.DATASETS_PREPARE = os.path.join(base_folder, '..', 'DataSets', 'prepare')
    __C.DATASETS_BASE = os.path.join(base_folder, '..', 'DataSets')
    __C.PRETRAINED_MODEL = os.path.join(base_folder, '..', 'PretrainedModels')
    __C.SSL_PATH = os.path.join(base_folder, '..', 'web', 'ssl')
    __C.SSL_CERT = os.path.join(__C.SSL_PATH, 'cert.pem')
    __C.SSL_KEY = os.path.join(__C.SSL_PATH, 'key.pem')
    if not os.path.exists(cfg.DATASETS_PREPARE):
        os.mkdir(cfg.DATASETS_PREPARE)
    if not os.path.exists(cfg.SSL_PATH):
        os.mkdir(cfg.SSL_PATH)
    if not os.path.exists(cfg.PRETRAINED_MODEL):
        os.mkdir(cfg.PRETRAINED_MODEL)
    return cfg

def prepare_datasets(cfg):
    from datasets import prepare_datasets
    print('[INFO] ===========================')
    print('[INFO] STAGE 4: Preparing Datasets')
    prepare_datasets(cfg)

def prepare_pull_images():
    images = [
        "starcaspar/rod:latest",
        "tutum/haproxy:latest",
        "node:8"
    ]
    print('[INFO] ===========================')
    print('[INFO] STAGE 3: Preparing Docker Images')
    daemon = docker.from_env()
    for image in images:
        print('[INFO] Docker pulling "%s"' % image)
        daemon.images.pull(image)

def prepare_ssl(cfg):
    from mk_certs import make_certs
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
#    prepare_model(cfg)
#    prepare_ssl(cfg)
#    prepare_pull_images()
    prepare_datasets(cfg)
