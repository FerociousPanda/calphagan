import os
from random import shuffle
import glob
from scipy import misc
import tensorflow as tf
import numpy as np
import tensorlayer as tl

def load_image(data_dir):
    img_list = glob.glob(data_dir+"/**/*.JPEG")
    save_dir = "./cropped_images_125"
    save_dir_1 = "./cropped_images_150"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    if not os.path.exists(save_dir_1):
        os.makedirs(save_dir_1)
    t_num_img = len(img_list)
    cnt = 0
    print ("Start...")
    for img in img_list:
        try:
            im = misc.imread(img)
        except:
            continue
        short_edge = min(im.shape[:2])
        long_edge = max(im.shape[:2])

        cnt += 1

        if cnt % 200 == 0:
            print ("{}/{}".format(cnt, t_num_img))

        if short_edge < 120:
            continue
        if long_edge/short_edge < 1.5:
            xx = int((im.shape[1]-short_edge) / 2)
            yy = int((im.shape[0]-short_edge) / 2)
            im = im[yy:yy+short_edge, xx:xx+short_edge]
            im = misc.imresize(im, (224, 224))
            if im.shape != (224, 224, 3):
                continue
            name = img.split('/')[-1]
            misc.imsave(save_dir_1+'/'+name, im)
            if long_edge/short_edge < 1.25:
                misc.imsave(save_dir+'/'+name, im)

def mkdir_if_not_exists(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def get_test_images(dir='./train_samples'):
    img_paths = glob.glob(dir+'/*')
    imgs = []
    for img_path in img_paths:
        im = misc.imread(img_path)
        im = misc.imresize(im, [64, 64])
        imgs.append(im)

    return np.array(imgs)

def _int64_feature(value):
  return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

def _float32_feature(value):
    return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))

def _bytes_feature(value):
  return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

def parse_image_name_to_image_id(name):
    n1, n2 = name.split('_')
    n1 = ''.join(s for s in n1 if s.isdigit())
    n2 = ''.join(s for s in n2 if s.isdigit())

    return np.float32(n1) + np.float32(n2)/1000000

def load_and_save_to_tfrecord(data_dir, save_dir, name):

    mkdir_if_not_exists(save_dir)

    file_name = os.path.join(save_dir, name+'.tf')

    img_paths = glob.glob(data_dir+'/*/*.JPEG')


    # shuffle all the images
    shuffle(img_paths)

    print ('Writing ', file_name)

    with tf.python_io.TFRecordWriter(file_name) as writer:
        cnt = 0
        for img_path in img_paths:
            cnt += 1
            if cnt % 1000 == 0:
                print ('{}/{}'.format(cnt, len(img_paths)))
            im = misc.imread(img_path)
            im = misc.imresize(im, [64, 64])
            img_label = int(img_path.split('/')[-2])
            example = tf.train.Example(
                features = tf.train.Features(
                    feature={'image_raw': _bytes_feature(im.tostring()),
                             'label': _int64_feature(img_label)}
                )
            )
            writer.write(example.SerializeToString())

def decode(serialized_example):
    features = tf.parse_single_example(
        serialized_example,
        features={
            'image_raw': tf.FixedLenFeature([], tf.string),
            'label' : tf.FixedLenFeature([], tf.int64)
        }
    )
    image = tf.decode_raw(features['image_raw'], tf.uint8)

    label = tf.cast(features['label'], tf.int32)

    image.set_shape((64*64*3))

    image = tf.reshape(image, (64, 64, 3))

    return image, label

def augment(img, label):
    "j"
    image_size_r = int(64*1.2)
    "1. randomly flip the image from left to right"
    img = tf.image.random_flip_left_right(img)

    "2. rotate the image counterclockwise 90 degree"
    img = tf.image.rot90(img, k=1)

    img = tf.image.random_flip_up_down(img)
    img = tf.image.resize_images(img, size=[image_size_r, image_size_r], method=tf.image.ResizeMethod.BICUBIC)

    img = tf.random_crop(img, [64, 64, 3])

    return img, label

def input_batch(filename, batch_size, num_epochs, shuffle_size, is_augment):
    with tf.name_scope('input'):
        dataset = tf.data.TFRecordDataset(filename)

        dataset = dataset.map(decode)

        if is_augment:
            dataset = dataset.map(augment)

        dataset = dataset.shuffle(buffer_size=shuffle_size)

        dataset = dataset.repeat(num_epochs)

        dataset = dataset.batch(batch_size)

        iterator = dataset.make_one_shot_iterator()

    return iterator.get_next()

#def run():
#    batch_size = 8
#    num_epochs = 12
#
#    filename = './train/cifar10_labeled.tf'
#
#    im_batch, label =  input_batch(filename, batch_size, num_epochs, is_augment=False, shuffle_size=500)
#    #init_ops = tf.group(tf.global_variables_initializer(), tf.local_variables_initializer())
#    with tf.Session() as sess:
#        #sess.run(init_ops)
#        try:
#            while True:
#                imgs, la_bz = sess.run([im_batch, label])
#                label_one_hot = np.eye(10)[la_bz]
#                print (label_one_hot)
#        except tf.errors.OutOfRangeError:
#            print ('Done')
#
# if __name__ == '__main__':
#     run()
    #load_and_save_to_tfrecord('./train_class', './train', 'cifar10_labeled')
