import os
import numpy as np
from cntk import input_variable, Axis
from utils.nms_wrapper import apply_nms_to_single_image_results
from utils.rpn.bbox_transform import regress_rois
from utils.plot_helpers import resize_and_pad
from utils.map_helpers import evaluate_detections
from utils.od_mb_source import ObjectDetectionMinibatchSource

import base64
import cv2
from tqdm import tqdm

class FasterRCNN_Evaluator:
    def __init__(self, eval_model, cfg):
        # load model once in constructor and push images through the model in 'process_image()'
        self._img_shape = (cfg.NUM_CHANNELS, cfg.IMAGE_HEIGHT, cfg.IMAGE_WIDTH)
        image_input = input_variable(shape=self._img_shape,
                                     dynamic_axes=[Axis.default_batch_axis()],
                                     name=cfg["MODEL"].FEATURE_NODE_NAME)
        dims_input = input_variable((1,6), dynamic_axes=[Axis.default_batch_axis()], name='dims_input')
        self._eval_model = eval_model(image_input, dims_input)

    def process_image_detailed(self, img):
        _, cntk_img_input, dims = resize_and_pad(img, self._img_shape[2], self._img_shape[1], 114)
#        _, cntk_img_input, dims = load_resize_and_pad(img_path, self._img_shape[2], self._img_shape[1])

        cntk_dims_input = np.array(dims, dtype=np.float32)
        cntk_dims_input.shape = (1,) + cntk_dims_input.shape
        output = self._eval_model.eval({self._eval_model.arguments[0]: [cntk_img_input],
                                        self._eval_model.arguments[1]: cntk_dims_input})

        out_dict = dict([(k.name, k) for k in output])
        out_cls_pred = output[out_dict['cls_pred']][0]
        out_rpn_rois = output[out_dict['rpn_rois']][0]
        out_bbox_regr = output[out_dict['bbox_regr']][0]

        return out_cls_pred, out_rpn_rois, out_bbox_regr, dims


def serialization_detections(roi_coords, roi_labels, roi_scores,
                         pad_width, pad_height, classes, decision_threshold = 0.0):
    # read and resize image
    rect_scale = 800 / pad_width

    assert(len(roi_labels) == len(roi_coords))
    if roi_scores is not None:
        assert(len(roi_labels) == len(roi_scores))
        minScore = min(roi_scores)
        if minScore > decision_threshold:
            decision_threshold = minScore * 0.5

    results = []
    # draw multiple times to avoid occlusions
    for roiIndex in range(len(roi_coords)):
        label = roi_labels[roiIndex]
        if roi_scores is not None:
            score = roi_scores[roiIndex]
            if decision_threshold and score < decision_threshold:
                label = 0

        rect = [(rect_scale * i) for i in roi_coords[roiIndex]]
        rect[0] = int(max(0, min(pad_width, rect[0])))
        rect[1] = int(max(0, min(pad_height, rect[1])))
        rect[2] = int(max(0, min(pad_width, rect[2])))
        rect[3] = int(max(0, min(pad_height, rect[3])))

        if label > 0:
            if roi_scores is not None:
                results += [{
                "name": classes[label],
                "box": {
                    "left": rect[0],
                    "top": rect[1],
                    "right": rect[2],
                    "bottom": rect[3]
                },
                "score": "%.2f" % score
            }]
    return results

def get_results(evaluator, payload, cfg):
    # from matplotlib.pyplot import imsave
    img_shape = (cfg.NUM_CHANNELS, cfg.IMAGE_HEIGHT, cfg.IMAGE_WIDTH)
    # img_result = "{}/{}".format(results_base_path, os.path.basename(img_path))

    img = base64.b64decode(payload); 
    npimg = np.fromstring(img, dtype=np.uint8); 
    source = cv2.imdecode(npimg, 1) 

    out_cls_pred, out_rpn_rois, out_bbox_regr, dims = evaluator.process_image_detailed(source)
    labels = out_cls_pred.argmax(axis=1)
    scores = out_cls_pred.max(axis=1)

    # apply regression and nms to bbox coordinates
    regressed_rois = regress_rois(out_rpn_rois, out_bbox_regr, labels, dims)
    nmsKeepIndices = apply_nms_to_single_image_results(regressed_rois, labels, scores,
                                                       use_gpu_nms=cfg.USE_GPU_NMS,
                                                       device_id=cfg.GPU_ID,
                                                       nms_threshold=cfg.RESULTS_NMS_THRESHOLD,
                                                       conf_threshold=cfg.RESULTS_NMS_CONF_THRESHOLD)

    filtered_bboxes = regressed_rois[nmsKeepIndices]
    filtered_labels = labels[nmsKeepIndices]
    filtered_scores = scores[nmsKeepIndices]

    return serialization_detections(filtered_bboxes, filtered_labels, filtered_scores,
                                img_shape[2], img_shape[1],
                                classes=cfg["DATA"].CLASSES,
                                decision_threshold=cfg.RESULTS_BGR_PLOT_THRESHOLD)

def compute_test_set_aps(eval_model, cfg):
    num_test_images = min(cfg["DATA"].NUM_TEST_IMAGES, 100)
    classes = cfg["DATA"].CLASSES
    image_input = input_variable(shape=(cfg.NUM_CHANNELS, cfg.IMAGE_HEIGHT, cfg.IMAGE_WIDTH),
                                 dynamic_axes=[Axis.default_batch_axis()],
                                 name=cfg["MODEL"].FEATURE_NODE_NAME)
    roi_input = input_variable((cfg.INPUT_ROIS_PER_IMAGE, 5), dynamic_axes=[Axis.default_batch_axis()])
    dims_input = input_variable((6), dynamic_axes=[Axis.default_batch_axis()])
    frcn_eval = eval_model(image_input, dims_input)

    # Create the minibatch source
    minibatch_source = ObjectDetectionMinibatchSource(
        cfg["DATA"].TEST_MAP_FILE,
        cfg["DATA"].TEST_ROI_FILE,
        max_annotations_per_image=cfg.INPUT_ROIS_PER_IMAGE,
        pad_width=cfg.IMAGE_WIDTH,
        pad_height=cfg.IMAGE_HEIGHT,
        pad_value=cfg["MODEL"].IMG_PAD_COLOR,
        randomize=False, use_flipping=False,
        max_images=cfg["DATA"].NUM_TEST_IMAGES,
        num_classes=cfg["DATA"].NUM_CLASSES,
        proposal_provider=None)

    # define mapping from reader streams to network inputs
    input_map = {
        minibatch_source.image_si: image_input,
        minibatch_source.roi_si: roi_input,
        minibatch_source.dims_si: dims_input
    }

    # all detections are collected into:
    #    all_boxes[cls][image] = N x 5 array of detections in (x1, y1, x2, y2, score)
    all_boxes = [[[] for _ in range(num_test_images)] for _ in range(cfg["DATA"].NUM_CLASSES)]

    # evaluate test images and write netwrok output to file
    print("[INFO] Evaluating Faster R-CNN model for %s images." % num_test_images)
    print("[INFO] It will take a while, please wait")
    all_gt_infos = {key: [] for key in classes}
    pbar = tqdm(total=num_test_images)
    pbar.set_description('EVA')
    for img_i in range(0, num_test_images):
        mb_data = minibatch_source.next_minibatch(1, input_map=input_map)

        gt_row = mb_data[roi_input].asarray()
        gt_row = gt_row.reshape((cfg.INPUT_ROIS_PER_IMAGE, 5))
        all_gt_boxes = gt_row[np.where(gt_row[:,-1] > 0)]

        pbar.update(1)
        for cls_index, cls_name in enumerate(classes):
            if cls_index == 0: continue
            cls_gt_boxes = all_gt_boxes[np.where(all_gt_boxes[:,-1] == cls_index)]
            all_gt_infos[cls_name].append({'bbox': np.array(cls_gt_boxes),
                                           'difficult': [False] * len(cls_gt_boxes),
                                           'det': [False] * len(cls_gt_boxes)})

        output = frcn_eval.eval({image_input: mb_data[image_input], dims_input: mb_data[dims_input]})
        out_dict = dict([(k.name, k) for k in output])
        out_cls_pred = output[out_dict['cls_pred']][0]
        out_rpn_rois = output[out_dict['rpn_rois']][0]
        out_bbox_regr = output[out_dict['bbox_regr']][0]

        labels = out_cls_pred.argmax(axis=1)
        scores = out_cls_pred.max(axis=1)
        regressed_rois = regress_rois(out_rpn_rois, out_bbox_regr, labels, mb_data[dims_input].asarray())

        labels.shape = labels.shape + (1,)
        scores.shape = scores.shape + (1,)
        coords_score_label = np.hstack((regressed_rois, scores, labels))

        #   shape of all_boxes: e.g. 21 classes x 4952 images x 58 rois x 5 coords+score
        for cls_j in range(1, cfg["DATA"].NUM_CLASSES):
            coords_score_label_for_cls = coords_score_label[np.where(coords_score_label[:,-1] == cls_j)]
            all_boxes[cls_j][img_i] = coords_score_label_for_cls[:,:-1].astype(np.float32, copy=False)


    pbar.close()

    # calculate mAP
    aps = evaluate_detections(all_boxes, all_gt_infos, classes,
                              use_gpu_nms = cfg.USE_GPU_NMS,
                              device_id = cfg.GPU_ID,
                              nms_threshold=cfg.RESULTS_NMS_THRESHOLD,
                              conf_threshold = cfg.RESULTS_NMS_CONF_THRESHOLD)

    return aps
