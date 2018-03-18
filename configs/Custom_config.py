# ==============================================================================
# Copyright (c) Microsoft. All rights reserved.

# Licensed under the MIT license. See LICENSE.md file in the project root
# for full license information.
# ==============================================================================

# `pip install easydict` if you don't have it
from easydict import EasyDict as edict

__C = edict()
__C.DATA = edict()
cfg = __C

# data set config
__C.DATA.DATASET = "Custom"
__C.DATA.MAP_FILE_PATH = "../../DataSets/Custom/mappings"
__C.DATA.CLASS_MAP_FILE = "class_map.txt"
__C.DATA.TRAIN_MAP_FILE = "train_img_file.txt"
__C.DATA.TRAIN_ROI_FILE = "train_roi_file.txt"
__C.DATA.TEST_MAP_FILE = "test_img_file.txt"
__C.DATA.TEST_ROI_FILE = "test_roi_file.txt"
__C.DATA.NUM_TRAIN_IMAGES = 254
__C.DATA.NUM_TEST_IMAGES = 56
__C.DATA.PROPOSAL_LAYER_SCALES = [8, 16, 32]

__C.NUM_CHANNELS = 3
__C.IMAGE_WIDTH = 850
__C.IMAGE_HEIGHT = 850
__C.RESULTS_BGR_PLOT_THRESHOLD = 0.1

__C.NUM_CHANNELS = 3

__C.IMAGE_WIDTH = 850
__C.IMAGE_HEIGHT = 850
__C.RESULTS_BGR_PLOT_THRESHOLD = 0.2

__C.NUM_CHANNELS = 3

__C.IMAGE_WIDTH = 850
__C.IMAGE_HEIGHT = 850
__C.RESULTS_BGR_PLOT_THRESHOLD = 0.2

