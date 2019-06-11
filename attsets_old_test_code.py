import tensorflow as tf
import os
import sys
sys.path.append('..')
import tools as tools
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd 
import copy 
import shutil
GPU='0'

vox_res = 32

test_views=5

def metric_IoU(batch_voxel_occup_pred, batch_voxel_occup_true):
    batch_voxel_occup_pred_ = copy.deepcopy(batch_voxel_occup_pred)
    batch_voxel_occup_pred_[batch_voxel_occup_pred_ >= 0.5] = 1
    batch_voxel_occup_pred_[batch_voxel_occup_pred_ < 0.5] = 0
	
    I = batch_voxel_occup_pred_ * batch_voxel_occup_true
    U = batch_voxel_occup_pred_ + batch_voxel_occup_true			
    U[U < 1] = 0
    U[U >= 1] = 1
    iou = np.sum(I) * 1.0 / np.sum(U) * 1.0
    return iou
	
def evaluate_voxel_prediction(prediction, gt):
  #"""  The prediction and gt are 3 dim voxels. Each voxel has values 1 or 0"""
    prediction[prediction >= 0.5] = 1
    prediction[prediction < 0.5] = 0        
    intersection = np.sum(np.logical_and(prediction,gt))
    union = np.sum(np.logical_or(prediction,gt))
    IoU = float(intersection) / float(union)
    return IoU
  
def load_real_rgbs(test_mv=test_views):
    obj_rgbs_folder ='./Data_sample/amazon_real_rgbs/lamp/'
    rgbs = []
    rgbs_views = sorted(os.listdir(obj_rgbs_folder))
    for v in rgbs_views:
        if not v.endswith('png'): continue
        rgbs.append(tools.Data.load_single_X_rgb_r2n2(obj_rgbs_folder + v, train=False))
    rgbs = np.asarray(rgbs)
    x_sample = rgbs[0:test_mv, :, :, :].reshape(1, test_mv, 127, 127, 3)
    return x_sample, None

def load_shapenet_rgbs(test_mv=test_views):
    obj_rgbs_folder = './Data_sample/ShapeNetRendering/03001627/1aa07508b731af79814e2be0234da26c/rendering/'
    obj_gt_vox_path ='./Data_sample/ShapeNetVox32/03001627/1aa07508b731af79814e2be0234da26c/model.binvox'
    rgbs=[]
    rgbs_views = sorted(os.listdir(obj_rgbs_folder))
    for v in rgbs_views:
        if not v.endswith('png'): continue
        rgbs.append(tools.Data.load_single_X_rgb_r2n2(obj_rgbs_folder + v, train=False))
    rgbs = np.asarray(rgbs)
    x_sample = rgbs[0:test_mv, :, :, :].reshape(1, test_mv, 127, 127, 3)
    y_true = tools.Data.load_single_Y_vox(obj_gt_vox_path)
    #########################################
    Y_true_vox = []
    Y_true_vox.append(y_true)
    Y_true_vox = np.asarray(Y_true_vox)
    return x_sample, Y_true_vox
    #########################################
def ttest_demo():
    model_path = './Model_released/'
    if not os.path.isfile(model_path + 'model.cptk.data-00000-of-00001'):
        print ('please download our released model first!')
        return

    config = tf.ConfigProto(allow_soft_placement=True)
    config.gpu_options.visible_device_list = GPU
    with tf.Session(config=config) as sess:
        saver = tf.train.import_meta_graph(model_path + 'model.cptk.meta', clear_devices=True)
        saver.restore(sess, model_path + 'model.cptk')
        print ('model restored!')

        X = tf.get_default_graph().get_tensor_by_name("Placeholder:0")
        Y_pred = tf.get_default_graph().get_tensor_by_name("r2n/Reshape_7:0")

#        x_sample, gt_vox = load_real_rgbs()
        x_sample, gt_vox = load_shapenet_rgbs()
        
	### reconstruction loss #########################################################
   
        gt_vox1=gt_vox.astype(np.float32)
        Y_vox_ = tf.reshape(gt_vox1, shape=[-1, vox_res ** 3])
        Y_pred_ = tf.reshape(Y_pred, shape=[-1, vox_res ** 3])
        rec_loss=tf.reduce_mean(-tf.reduce_mean(Y_vox_*tf.log(Y_pred_ + 1e-8),reduction_indices=[1])-tf.reduce_mean((1-Y_vox_)*tf.log(1 - Y_pred_+1e-8),reduction_indices=[1]))
        
                                #########################################################
        ## session run
        y_pred,recon_loss = sess.run([Y_pred, rec_loss], feed_dict={X: x_sample})		
		
        print("Number of Views : ", test_views) 		
        print("Cross entropy loss : ",	recon_loss)
        
        y_pred_=y_pred

        iou_=evaluate_voxel_prediction(y_pred_,gt_vox1)
        print("evaluate_voxel_prediction:",iou_)
		
        iou_value= metric_IoU( y_pred,gt_vox1)
        print("metric_IoU :",iou_value)		                     
        
#        y_pred= sess.run(Y_pred, feed_dict={X: x_sample})             
    ###### to visualize
    th = 0.25
    y_pred[y_pred>=th]=1
    y_pred[y_pred<th]=0
    tools.Data.plotFromVoxels(np.reshape(y_pred,[32,32,32]), title='y_pred')
    if gt_vox is not None:
        tools.Data.plotFromVoxels(np.reshape(gt_vox,[32,32,32]), title='y_true')
    from matplotlib.pyplot import show
    show()

#########################
if __name__ == '__main__':
    ttest_demo()