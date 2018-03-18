# ==============================================================================
# Copyright (c) Microsoft. All rights reserved.
#
# Licensed under the MIT license. See LICENSE.md file in the project root
# for full license information.
# ==============================================================================

import sys, os, re
from easydict import EasyDict as edict

def verify_files(cfg):
    directories = os.listdir(cfg.DATASETS_PREPARE)
    require = ['ImageSets', 'JPEGImages', 'Annotations', 'pascal_label_map.pbtxt']
    failed = False

    for check in require:
        if not check in directories:
            print('[ERROR] %s" required' % check)
            failed = True

    eva_files = os.listdir(os.path.join(cfg.DATASETS_PREPARE, require[0], "Main"))
    img_files = os.listdir(os.path.join(cfg.DATASETS_PREPARE, require[1]))
    xml_files = os.listdir(os.path.join(cfg.DATASETS_PREPARE, require[2]))
    img_sets, xml_sets, eva_sets, class_sets  = [], [], [], []
   
    label_map = ''
    with open(os.path.join(cfg.DATASETS_PREPARE, 'pascal_label_map.pbtxt'), 'r') as f:
        label_map += f.read()
    class_sets = re.findall(r"'([A-Za-z0-9]+)'", label_map)
    print('[VERBOSE] class loaded: ["%s"]' % '", "'.join(class_sets))

    for classes in class_sets:
        for postfix in ['_train.txt', '_val.txt']:
            if not (classes + postfix) in eva_files:
                failed = True
                print('[ERROR] class: "%s" exists, so "%s" file is requred' % (classes, classes + postfix))
        
    if failed: 
        print('[FAILED] You need to prepare your datasets in specific rule. see https://aka.ms/rod_prepare')
        exit(1)

    for f in img_files:
        if not f.endswith('.jpg'):
            print('[INFO] Ignore not image file "%s"' % f)
            img_files.remove(f)
        else:
            img_sets += [os.path.splitext(f)[0]]

    for f in xml_files:
        if not f.endswith('.xml'):
            print('[INFO] Ignore not xml file "%s"' % f)
            xml_files.remove(f)
        else:
            xml_sets += [os.path.splitext(f)[0]]

    diff_sets = list(set(img_sets) - set(xml_sets)) + list(set(xml_sets) - set(img_sets))
    for diff in diff_sets:
        found, notfound = (diff + '.jpg'), (diff + '.xml')
        if not found in img_files:
            found = found.replace('.jpg', '.xml')
            notfound = notfound.replace('.xml', '.jpg')
        print('[ERROR] files not match: Found "%s" but "%s"' % (found, notfound))
  
    if failed: 
        print('[FAILED] You need to prepare your datasets in specific rule. see https://aka.ms/rod_prepare')
        exit(1)


    for classes in class_sets:
        eva_sets = []
        for postfix in ['_train.txt', '_val.txt']:
            with open(os.path.join(cfg.DATASETS_PREPARE, require[0], "Main", (classes + postfix)), 'r') as f:
                for line in f:
                    if not line.split(' ')[0] in img_sets:
                        print('[ERROR] missing jpg/xml file "%s"' % line.split(' ')[0])
                        failed = True
                    eva_sets += [line.split(' ')[0]]
    
        for diff in list(set(img_sets) - set(eva_sets)):
            print('[ERROR] "%s" file not exist in train/val file' % diff)
            failed = True
        if not failed:
            print('[VERBOSE] class "%s" train/val files verified' % classes) 

    if failed:  
        print('[FAILED] You need to prepare your datasets in specific rule. see https://aka.ms/rod_prepare')
        exit(1)
    print('[SUCCESS] Verification pass')

    cfg.DATASETS = edict()
    cfg.DATASETS.IMAGE_FILES = img_files
    cfg.DATASETS.ANNOTATION_FILES = xml_files
    cfg.DATASETS.IMAGESETS_FILES = eva_files
    cfg.DATASETS.CLASSES = class_sets
    cfg.DATASETS.BASENAMES = xml_sets
    cfg.DATASETS.IMAGESETS_PATH = os.path.join(cfg.DATASETS_PREPARE, require[0], "Main")
    cfg.DATASETS.IMAGES_PATH = os.path.join(cfg.DATASETS_PREPARE, require[1])
    cfg.DATASETS.ANNOTATIONS_PATH = os.path.join(cfg.DATASETS_PREPARE, require[2])

    return cfg

def rename_all(cfg):
    all_steps = 4
    print('[VERBOSE] Renaming (1/%d) image files' % all_steps)
    os.chdir(os.path.join(cfg.PREPARE, cfg.DATASETS.IMAGES_PATH))
    for i, name in enumerate(cfg.DATASETS.BASENAMES):
        os.rename(name + '.jpg', str(i).zfill(5) + '.jpg')
        print('[VERBOSE] Renaming %s to %s' % (name + '.jpg', str(i).zfill(5) + '.jpg'))

    print('[VERBOSE] Rewriting (2/%d) annotation content' % all_steps)
    os.chdir(os.path.join(cfg.PREPARE, cfg.DATASETS.ANNOTATIONS_PATH))
    for i, name in enumerate(cfg.DATASETS.BASENAMES):
        modified = []
        with open(name + '.xml', 'r') as f:
            for line in f:
                for target in ['path', 'filename']:
                    if '<%s>' % target in line:
                        split = re.compile("</?%s>" % target).split(line)
                        line = '%s<%s>%s.xml</%s>%s' % (split[0], target, str(i).zfill(5), target, split[2])
                modified += [line]
        with open(name + '.xml', 'w') as f:
            f.write(''.join(modified))
        print('[VERBOSE] Renaming annotation file %s' % (name + '.xml'))
    print('[VERBOSE] Renaming (3/%d) annotation files' % all_steps)
    os.chdir(os.path.join(cfg.PREPARE, cfg.DATASETS.ANNOTATIONS_PATH))
    for i, name in enumerate(cfg.DATASETS.BASENAMES):
        os.rename(name + '.xml', str(i).zfill(5) + '.xml')
        print('[VERBOSE] Renaming %s to %s' % (name + '.xml', str(i).zfill(5) + '.xml'))

    print('[VERBOSE] Renaming (4/%d) imagessets contents' % all_steps)
    os.chdir(os.path.join(cfg.PREPARE, cfg.DATASETS.IMAGESETS_PATH))
    for imageset in cfg.DATASETS.IMAGESETS_FILES:
        modified = []
        with open(imageset, 'r') as f:
            for line in f:
                name = line.split(' ')[0]
                i = cfg.DATASETS.BASENAMES.index(name)
                if i < 0:
                    print('[ERROR] name "%s" on line %s  is not exist in datasets' % (name, len(modified)))
                    exit(1)
                modified += [line.replace(name, str(i).zfill(5))]
        with open(imageset, 'w') as f:
             f.write(''.join(modified))

def prepare_datasets(cfg):
    cfg = verify_files(cfg)
    rename_all(cfg)
