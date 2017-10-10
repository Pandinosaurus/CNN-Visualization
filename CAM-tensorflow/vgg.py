# File: vgg.py
# Author: Qian Ge <geqian1001@gmail.com>
import argparse

import tensorflow as tf

import tensorcv
from tensorcv.dataflow.image import *
from tensorcv.callbacks import *
from tensorcv.train.config import TrainConfig
from tensorcv.train.simple import SimpleFeedTrainer
from tensorcv.predicts.simple import SimpleFeedPredictor
from tensorcv.predicts import *

from CAM import VGGCAM
import configvgg as config_path

def get_config(FLAGS):
    # data for training
    dataset_train = ImageLabelFromFolder(FLAGS.type, data_dir = config_path.data_dir, 
                        num_class = FLAGS.nclass,
                        resize = 224,
                        num_channel = FLAGS.nchannel)

    # Print image class name and label
    # print(dataset_train.label_dict)

    # Since the aim of training is visulization of class map, all the images 
    # are used for training. Using the training set as validation set is just
    # for checking whether the training works correctly.
    dataset_val = ImageLabelFromFolder(FLAGS.type, data_dir = config_path.data_dir, 
                        num_class = FLAGS.nclass,
                        resize = 224,
                        num_channel = FLAGS.nchannel)

    # Image use for inference the class acitivation map during training
    dataset_test = ImageFromFile(FLAGS.type, 
                                data_dir = config_path.infer_data_dir, 
                                shuffle = False,
                                resize = 224,
                                num_channel = FLAGS.nchannel)

    # Check accuracy during training using training set
    inference_list_validation = [InferScalars('accuracy/result', 'test_accuracy')]
    # Check class acitivation map during training
    inference_list_test = [
           InferOverlay(['classmap/result', 'image'], ['map', 'image'], color = True),
           InferImages('classmap/result', 'map', color = True)
        ]

    return TrainConfig(
                 dataflow = dataset_train, 
                 model = VGGCAM(num_class = FLAGS.nclass, 
                           inspect_class = FLAGS.label,
                           learning_rate = 0.001,
                           is_load = True,
                           pre_train_path = config_path.vgg_dir),
                 monitors = TFSummaryWriter(),
                 callbacks = [
                    ModelSaver(periodic = 100),
                    TrainSummary(key = 'train', periodic = 50),
                    FeedInferenceBatch(dataset_val, 
                                  periodic = 100, 
                                  batch_count = 10, 
                                  inferencers = inference_list_validation),
                    FeedInference(dataset_test, periodic = 50,
                                  infer_batch_size = 4, 
                                  inferencers = inference_list_test),
                    CheckScalar(['accuracy/result','loss/result'], 
                                 periodic = 10),
                  ],
                 batch_size = FLAGS.bsize, 
                 max_epoch = 25,
                 summary_periodic = 50,
                 default_dirs = config_path)

def get_predict_config(FLAGS):
    dataset_test = ImageFromFile(FLAGS.type, 
                                data_dir = config_path.test_data_dir, 
                                shuffle = False,
                                resize = 224,
                                num_channel = 3)
    # dataset_test = ImageLabelFromFolder('.jpg', data_dir = config_path.data_dir, 
    #                     num_class = FLAGS.nclass,
    #                     resize = 224,
    #                     num_channel = FLAGS.nchannel)
    prediction_list = [
             # PredictionScalar(['pre_label'], ['label']),
             # PredictionMeanScalar('accuracy/result', 'test_accuracy'),
             PredictionMat('classmap/result', ['test']),
             PredictionOverlay(['classmap/result', 'image'], ['map', 'image'], color = True, merge_im = True),
             PredictionImage(['image'], ['image'], color = True, merge_im = True)
             ]

    return PridectConfig(
                dataflow = dataset_test,
                model = VGGCAM(num_class = FLAGS.nclass, 
                           inspect_class = FLAGS.label,
                           learning_rate = 0.001,
                           is_load = True,
                           pre_train_path = config_path.vgg_dir),
                model_name = FLAGS.model,
                predictions = prediction_list,
                batch_size = FLAGS.bsize,
                default_dirs = config_path)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bsize', default = 32, type = int)
    parser.add_argument('--label', default = 1, type = int,
                        help = 'Label of inspect class.')
    parser.add_argument('--nclass', default = 257, type = int, 
                        help = 'number of image class')
    parser.add_argument('--nchannel', default = 3, type = int, 
                        help = 'number of image channels')

    parser.add_argument('--predict', action = 'store_true', 
                        help = 'Run prediction')
    parser.add_argument('--train', action = 'store_true', 
                        help = 'Train the model')

    parser.add_argument('--type', default = '.jpg', type = str, 
                        help = 'image type for training and testing')

    parser.add_argument('--model', type = str, 
                        help = 'file name of the trained model')

    return parser.parse_args()

if __name__ == '__main__':
    FLAGS = get_args()
    if FLAGS.train:
        config = get_config(FLAGS)
        SimpleFeedTrainer(config).train()
    if FLAGS.predict:
        config = get_predict_config(FLAGS)
        SimpleFeedPredictor(config).run_predict()

# 0.6861924529075623

