# ==============================================================================
# Copyright (c) Microsoft. All rights reserved.
#
# Licensed under the MIT license. See LICENSE.md file in the project root
# for full license information.
# ==============================================================================

import sys, os, re
import numpy as np
import scipy.io as sio
import xml.etree.ElementTree
from xml.etree import ElementTree
from enum import Enum
from PIL import Image

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
    cfg.DATASETS.CLASSES = ['__background__'] + class_sets
    cfg.DATASETS.BASENAMES = xml_sets
    cfg.DATASETS.IMAGESETS_PATH = os.path.join(cfg.DATASETS_PREPARE, require[0], "Main")
    cfg.DATASETS.IMAGES_PATH = os.path.join(cfg.DATASETS_PREPARE, require[1])
    cfg.DATASETS.ANNOTATIONS_PATH = os.path.join(cfg.DATASETS_PREPARE, require[2])
    cfg.DATASETS.PADS = 5

def rename_all(cfg):
    all_steps = 4
    print('[VERBOSE] Renaming (1/%d) image files' % all_steps)
    os.chdir(os.path.join(cfg.PREPARE, cfg.DATASETS.IMAGES_PATH))
    for i, name in enumerate(cfg.DATASETS.BASENAMES):
        os.rename(name + '.jpg', str(i).zfill(cfg.DATASETS.PADS) + '.jpg')
        print('[VERBOSE] Renaming %s to %s' % (name + '.jpg', str(i).zfill(cfg.DATASETS.PADS) + '.jpg'))

    print('[VERBOSE] Rewriting (2/%d) annotation content' % all_steps)
    os.chdir(os.path.join(cfg.PREPARE, cfg.DATASETS.ANNOTATIONS_PATH))
    for i, name in enumerate(cfg.DATASETS.BASENAMES):
        modified = []
        with open(name + '.xml', 'r') as f:
            for line in f:
                for target in ['path', 'filename']:
                    if '<%s>' % target in line:
                        split = re.compile("</?%s>" % target).split(line)
                        line = '%s<%s>%s.xml</%s>%s' % (split[0], target, str(i).zfill(cfg.DATASETS.PADS), target, split[2])
                modified += [line]
        with open(name + '.xml', 'w') as f:
            f.write(''.join(modified))
        print('[VERBOSE] Renaming annotation file %s' % (name + '.xml'))
    print('[VERBOSE] Renaming (3/%d) annotation files' % all_steps)
    os.chdir(os.path.join(cfg.PREPARE, cfg.DATASETS.ANNOTATIONS_PATH))
    for i, name in enumerate(cfg.DATASETS.BASENAMES):
        os.rename(name + '.xml', str(i).zfill(cfg.DATASETS.PADS) + '.xml')
        print('[VERBOSE] Renaming %s to %s' % (name + '.xml', str(i).zfill(cfg.DATASETS.PADS) + '.xml'))

    print('[VERBOSE] Renaming (4/%d) imagessets contents' % all_steps)
    os.chdir(os.path.join(cfg.PREPARE, cfg.DATASETS.IMAGESETS_PATH))

    train_sets = []
    test_sets = []
    for imageset in cfg.DATASETS.IMAGESETS_FILES:
        modified = []
        with open(imageset, 'r') as f:
            for line in f:
                name = line.split(' ')[0]
                i = cfg.DATASETS.BASENAMES.index(name)
                if i < 0:
                    print('[ERROR] name "%s" on line %s  is not exist in datasets' % (name, len(modified)))
                    exit(1)
                modified += [line.replace(name, str(i).zfill(cfg.DATASETS.PADS))]
                if imageset.endswith('train.txt'):
                    train_sets += [str(i).zfill(cfg.DATASETS.PADS)]
                else:
                    test_sets += [str(i).zfill(cfg.DATASETS.PADS)]
        with open(imageset, 'w') as f:
            f.write(''.join(modified))

    for trainval in ['train', 'test']:
        with open('%s.txt' % trainval, 'w') as f:
            f.write('\n'.join(list(set(train_sets if trainval == 'train' else test_sets)))+ '\n')
    os.chdir(cfg.DATASETS_PREPARE)
    cfg.DATASETS.TRAIN_SETS = list(set(train_sets))
    cfg.DATASETS.TEST_SETS = list(set(test_sets))

def format_roi(cls_index, xmin, ymin, xmax, ymax, img_file_path):
    use_relative_coords_ctr_wh = False
    use_pad_scale = False
    pad_width = 850
    pad_height = 850
    posx = xmin
    posy = ymin
    width = (xmax - xmin)
    height = (ymax - ymin)

    if use_pad_scale or use_relative_coords_ctr_wh:
        img_width, img_height = Image.open(img_file_path).size

        if use_pad_scale:
            scale_x = (1.0 * pad_width) / img_width
            scale_y = (1.0 * pad_height) / img_height

            min_scale = min(scale_x, scale_y)
            new_width = round(img_width * min_scale)
            new_height = round(img_height * min_scale)
            assert(new_width == pad_width or new_height == pad_height)
            assert(new_width <= pad_width and new_height <= pad_height)

            offset_x = (pad_width - new_width) / 2
            offset_y = (pad_height - new_height) / 2

            width = round(width * min_scale)
            height = round(height * min_scale)
            posx = round(posx * min_scale + offset_x)
            posy = round(posy * min_scale + offset_y)

            norm_width = pad_width
            norm_height = pad_height
        else:
            norm_width = img_width
            norm_height = img_height

        if use_relative_coords_ctr_wh:
            ctrx = xmin + width / 2
            ctry = ymin + height / 2

            width = float(width) / norm_width
            height = float(height) / norm_height
            ctrx = float (ctrx) / norm_width
            ctry = float(ctry) / norm_height

    if use_relative_coords_ctr_wh:
        return "{:.4f} {:.4f} {:.4f} {:.4f} {} ".format(ctrx, ctry, width, height, cls_index)
    else:
        posx2 = posx + width
        posy2 = posy + height
        return "{} {} {} {} {} ".format(int(posx), int(posy), int(posx2), int(posy2), cls_index)
 

def create_mapping_file(cfg, train=None):
    prefix = 'train' if train else 'test'
    print('[VERBOSE] Mapping %s file' % prefix)
    img_map_input = '%s.txt' % prefix 
    img_map_output = '%s_img_file.txt' % prefix 
    rot_map_output = '%s_roi_file.txt' % prefix
    in_map_file_path = os.path.join(cfg.DATASETS.IMAGESETS_PATH, img_map_input)
    out_map_file_path = os.path.join('mappings', img_map_output)
    roi_file_path = os.path.join('mappings', rot_map_output)

    with open(in_map_file_path) as input_file:
        input_lines = input_file.readlines()

    with open(out_map_file_path, 'w') as img_file: 
        with open(roi_file_path, 'w') as roi_file:
            for counter, line in enumerate(input_lines):
                img_number = line.strip()
                prepare_img_file_path = '%s/%s.jpg' % (cfg.DATASETS.IMAGES_PATH, img_number)
                datasets_img_file_path = '../JPEGImages/%s.jpg' % (img_number)
                img_line = "{}\t{}\t0\n".format(counter, datasets_img_file_path)
                img_file.write(img_line)

                annotation_file = os.path.join(cfg.DATASETS_PREPARE, cfg.DATASETS.ANNOTATIONS_PATH, '%s.xml' % img_number)
                annotations = ElementTree.parse(annotation_file).getroot()
                roi_line = "%d |roiAndLabel " % counter
                for obj in annotations.findall('object'):
                    cls = obj.findall('name')[0].text
                    cls_index = cfg.DATASETS.CLASSES.index(cls)
                    bbox = obj.findall('bndbox')[0]
                    xmin = int(bbox.findall('xmin')[0].text)
                    ymin = int(bbox.findall('ymin')[0].text)
                    xmax = int(bbox.findall('xmax')[0].text)
                    ymax = int(bbox.findall('ymax')[0].text)
                    roi_line += format_roi(cls_index, xmin, ymin, xmax, ymax, prepare_img_file_path)
                roi_file.write(roi_line + "\n")
                print('[VERBOSE] Processed %s (%d/%d)' % (img_number, counter, len(input_lines)-1))

def create_mappings(cfg):

    if not os.path.exists('mappings'):
        os.mkdir('mappings')

    class_map_file_path = os.path.join(cfg.DATASETS_PREPARE, 'mappings', 'class_map.txt')

    print('[VERBOSE] Create "class_map.txt"')
    with open(class_map_file_path, 'w') as class_map_file:
        for i, name in enumerate(cfg.DATASETS.CLASSES):
            class_map_file.write("{}\t{}\n".format(name, i))


    create_mapping_file(cfg, train=True) 
    create_mapping_file(cfg, train=False)
    
def copy_datasets(cfg):
    os.chdir(os.path.join(cfg.DATASETS_PREPARE, '..'))
    os.rename('prepare', 'Custom')
    os.mkdir('prepare')

def setting_config(cfg):
    modified = []
    with open(os.path.join(cfg.PREPARE, '..', 'configs', 'Custom_config.py'), 'r') as f:
        for line in f:
            if 'DATA.NUM_TRAIN_IMAGES' in line:
                option = line.split(' ')[0]
                line = '%s = %d\n' % (option, len(cfg.DATASETS.TRAIN_SETS))

            if 'DATA.NUM_TEST_IMAGES' in line:
                option = line.split(' ')[0]
                line = '%s = %d\n' % (option, len(cfg.DATASETS.TEST_SETS))
            modified += [line]

    with open(os.path.join(cfg.PREPARE, '..', 'configs', 'Custom_config.py'), 'w') as f:
        f.write(''.join(modified))

def prepare_datasets(cfg):
    verify_files(cfg)
    rename_all(cfg)
    create_mappings(cfg)
    copy_datasets(cfg)
    setting_config(cfg)

    print('[SUCCESS] Datasets ready')
