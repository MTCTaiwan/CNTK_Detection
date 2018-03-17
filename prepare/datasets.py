import sys, os




def prepare_datasets(cfg):
    print(os.listdir(cfg.DATASETS_BASE))
    print(os.listdir(cfg.DATASETS_PREPARE))
