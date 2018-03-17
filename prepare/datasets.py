import sys, os




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
    img_sets, xml_sets, eva_sets = [], [], []
   
    for f in img_files:
        if not f.endswith('.jpg'):
            print('[INFO] Ignore not image file "%s"' % f)
        else:
            img_sets += [os.path.splitext(f)[0]]

    for f in xml_files:
        if not f.endswith('.xml'):
            print('[INFO] Ignore not xml file "%s"' % f)
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
 
    for eva in eva_files:
        with open(os.path.join(cfg.DATASETS_PREPARE, require[0], "Main", eva), 'r') as f:
            for line in f:
                if not line.split(' ')[0] in img_sets:
                    print('[ERROR] missing jpg/xml file "%s"' % line.split(' ')[0])
                    failed = True
                eva_sets += [line.split(' ')[0]]

    for diff in list(set(img_sets) - set(eva_sets)):
         print('[ERROR] "%s" file not exist in train/val file' % diff)
         failed = True

    if failed:  
        print('[FAILED] You need to prepare your datasets in specific rule. see https://aka.ms/rod_prepare')
        exit(1)
    print('[SUCCESS] Verification pass')

def prepare_datasets(cfg):
    print(os.listdir(cfg.DATASETS_BASE))
    print(os.listdir(cfg.DATASETS_PREPARE))
    verify_files(cfg)
