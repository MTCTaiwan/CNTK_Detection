# Copyright (c) Microsoft. All rights reserved.

# Licensed under the MIT license. See LICENSE.md file in the project root
# for full license information.
# ==============================================================================

import os, sys, io, json, base64, datetime as dt, json, numpy as np
import cntk
from cntk import load_model
abs_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(abs_path, ".."))
from utils.config_helpers import merge_configs
from utils.annotations.annotations_helper import parse_class_map_file
from evaluator import FasterRCNN_Evaluator, compute_test_set_aps
from FasterRCNN_train import prepare

def get_configuration():
    from FasterRCNN_config import cfg as detector_cfg
    from utils.configs.VGG16_config import cfg as network_cfg
    from utils.configs.Custom_config import cfg as dataset_cfg
    return merge_configs([detector_cfg, network_cfg, dataset_cfg])

# trains and evaluates a Fast R-CNN model.
if __name__ == '__main__':

    print('[INFO] Initial')
    cfg = get_configuration()

    print('[INFO] Verbose configuration')
    prepare(cfg, False)
    print(json.dumps(cfg, indent=2, sort_keys=True))

    model_path = cfg['MODEL_PATH']
    if os.path.exists(model_path) == False: 
        print('[ERROR] "faster_rcnn_eval_VGG16_e2e.model" Model not found,\n', \
              'Please put your model file to Output/ directory,\n', \
              'Or run [nvidia-docker-compose up train] to train a new one')
        exit(1)
    model = load_model(model_path)
    evaluator = FasterRCNN_Evaluator(model, cfg) 
    print('[SUCCESS] Model loaded, evalutor prepared')
    eval_results = compute_test_set_aps(model, cfg)

    # write AP results to output
    for class_name in eval_results: print('AP for {:>15} = {:.4f}'.format(class_name, eval_results[class_name]))
    print('[SUCCESS] Testing finished, ', 'Mean AP = {:.4f}'.format(np.nanmean(list(eval_results.values()))))

    from server import Server, ThreadedHTTPServer
    from http.server import HTTPServer
    host, port = '0.0.0.0', 8082
    print("[INFO] Server initial, lisiten at %s port %d"%(host, port))
    httpd = ThreadedHTTPServer((host, port), Server)
    httpd.RequestHandlerClass.bind_evaluator(evaluator, cfg)
    httpd.serve_forever()
