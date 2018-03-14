# Copyright (c) Microsoft. All rights reserved.

# Licensed under the MIT license. See LICENSE.md file in the project root
# for full license information.
# ==============================================================================
import os, sys
import numpy as np
import cntk
from FasterRCNN_train import prepare, train_faster_rcnn, store_eval_model_with_native_udf
from evaluator import compute_test_set_aps, FasterRCNN_Evaluator

abs_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(abs_path, ".."))
from utils.config_helpers import merge_configs
from utils.plot_helpers import plot_test_set_results

def get_configuration():
    # load configs for detector, base network and data set
    from FasterRCNN_config import cfg as detector_cfg
    from utils.configs.VGG16_config import cfg as network_cfg
    from utils.configs.Custom_config import cfg as dataset_cfg
    # for VGG16 base model use:         from utils.configs.VGG16_config import cfg as network_cfg
    # for AlexNet base model use:       from utils.configs.AlexNet_config import cfg as network_cfg
    # for Pascal VOC 2007 data set use: from utils.configs.Pascal_config import cfg as dataset_cfg
    # from utils.configs.Pascal_config import cfg as dataset_cfg
    # for the Grocery data set use:     from utils.configs.Grocery_config import cfg as dataset_cfg
    return merge_configs([detector_cfg, network_cfg, dataset_cfg])

# trains and evaluates a Fast R-CNN model.
if __name__ == '__main__':
    cfg = get_configuration()
    prepare(cfg, False)

    # GPU Devices Support
    cntk.device.try_set_default_device(cntk.device.gpu(cfg.GPU_ID))
    # CPU Only
    # cntk.device.try_set_default_device(cntk.device.cpu())

    # train and test
    trained_model = train_faster_rcnn(cfg)
    eval_results = compute_test_set_aps(trained_model, cfg)

    # write AP results to output
    for class_name in eval_results: print('[VERBOSE] AP for {:>15} = {:.4f}'.format(class_name, eval_results[class_name]))
    print('[SUCCESS] Mean AP = {:.4f}'.format(np.nanmean(list(eval_results.values()))))

    print('[SUCCESS] Training task finished') 
