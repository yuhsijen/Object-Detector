import os
import re
import shutil
import json
from datetime import datetime

import tensorflow as tf
from google.protobuf import text_format
from object_detection import exporter
from object_detection.protos import pipeline_pb2
from object_detection.utils.label_map_util import get_label_map_dict
from object_detection.builders import model_builder

slim = tf.contrib.slim
flags = tf.app.flags

flags.DEFINE_string('input_type', 'image_tensor', 'Type of input node. Can be '
                    'one of [`image_tensor`, `encoded_image_string_tensor`, '
                    '`tf_example`]')
flags.DEFINE_string('input_shape', None,
                    'If input_type is `image_tensor`, this can explicitly set '
                    'the shape of this input tensor to a fixed size. The '
                    'dimensions are to be provided as a comma-separated list '
                    'of integers. A value of -1 can be used for unknown '
                    'dimensions. If not specified, for an `image_tensor, the '
                    'default shape will be partially specified as '
                    '`[None, None, None, 3]`.')
flags.DEFINE_string('result_base', '.tmp',
                    'Path to a string_int_label_map_pb2.StringIntLabelMapItem '
                    'file.')
flags.DEFINE_string('pipeline_config_path', 'pipeline.config',
                    'Path to a pipeline_pb2.TrainEvalPipelineConfig config '
                    'file.')
flags.DEFINE_string('label_map_path', 'data/label_map.pbtxt',
                    'Path to a string_int_label_map_pb2.StringIntLabelMapItem '
                    'file.')
flags.DEFINE_string('trained_checkpoint_path', 'checkpoint',
                    'Path to trained checkpoint, typically of the form '
                    'path/to/checkpoints')
flags.DEFINE_string('trained_checkpoint_prefix', None,
                    'Path to trained checkpoint, typically of the form '
                    'path/to/model.ckpt')
flags.DEFINE_string('model_dir', 'exported_graph', 'Path to write outputs.')
flags.DEFINE_string('output_label_path', 'labels.json', 'Path to write outputs.')
flags.DEFINE_string('config_override', '',
                    'pipeline_pb2.TrainEvalPipelineConfig '
                    'text proto to override pipeline_config_path.')
flags.DEFINE_boolean('write_inference_graph', False,
                     'If true, writes inference graph to disk.')
FLAGS = flags.FLAGS


def main(_):
    pipeline_config = pipeline_pb2.TrainEvalPipelineConfig()
    with tf.gfile.GFile(os.path.join(FLAGS.result_base, FLAGS.pipeline_config_path), 'r') as f:
        text_format.Merge(f.read(), pipeline_config)
    text_format.Merge(FLAGS.config_override, pipeline_config)
    if FLAGS.input_shape:
        input_shape = [
            int(dim) if dim != '-1' else None
            for dim in FLAGS.input_shape.split(',')
        ]
    else:
        input_shape = None

    if os.path.exists(FLAGS.model_dir) and os.path.isdir(FLAGS.model_dir):
        shutil.rmtree(FLAGS.model_dir)
  
    if not FLAGS.trained_checkpoint_prefix:
        path = os.path.join(FLAGS.result_base, FLAGS.trained_checkpoint_path)
        regex = re.compile(r"model\.ckpt-([0-9]+)\.index")
        numbers = [int(regex.search(f).group(1)) for f in os.listdir(path) if regex.search(f)]
        if not numbers:
            print('No checkpoint found!')
            exit()
        trained_checkpoint_prefix = os.path.join(path, 'model.ckpt-{}'.format(max(numbers)))
        print("Trained checkpoint prefix is", trained_checkpoint_prefix)
    else:
        trained_checkpoint_prefix = FLAGS.trained_checkpoint_prefix
        print("Trained checkpoint prefix is", trained_checkpoint_prefix)

    exporter.export_inference_graph(
            FLAGS.input_type, pipeline_config, trained_checkpoint_prefix,
            FLAGS.model_dir, input_shape=input_shape,
            write_inference_graph=FLAGS.write_inference_graph)

    label_map = get_label_map_dict(os.path.join(FLAGS.result_base, FLAGS.label_map_path))
    label_array = [k for k in sorted(label_map, key=label_map.get)]
    with open(os.path.join(FLAGS.model_dir, FLAGS.output_label_path), 'w') as f:
        json.dump(label_array, f)


if __name__ == '__main__':
    tf.app.run()
