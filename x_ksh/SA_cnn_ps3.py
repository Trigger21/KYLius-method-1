#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 26 18:53:10 2018

@author: kimseunghyuck
"""

#import important modules
import numpy as np
import tensorflow as tf
tf.set_random_seed(777) 

trainData = np.genfromtxt('/home/paperspace/Downloads/trainData.csv', delimiter=',')
trainData = trainData.reshape(-1, 20, 100)
testData = np.genfromtxt('/home/paperspace/Downloads/testData.csv', delimiter=',')
testData = testData.reshape(-1, 20, 100)
trainLabel = np.genfromtxt('/home/paperspace/Downloads/trainLabel.csv', delimiter=',')
testLabel = np.genfromtxt('/home/paperspace/Downloads/testLabel.csv', delimiter=',')

print(trainData.shape, testData.shape, trainLabel.shape, testLabel.shape)
# (6631, 20, 100) (2842, 20, 100) (6631,) (2842,)

#다시 돌릴때는 여기부터 
tf.reset_default_graph()     #그래프 초기화

# hyper parameters
learning_rate = 0.0002
training_epochs = 300
batch_size = 100
steps_for_validate = 5

#placeholder
X = tf.placeholder(tf.float32, [None, 20, 100], name="X")
X_sound = tf.reshape(X, [-1, 20, 100, 1])          # 20*100*1 (frequency, time, amplitude)
Y = tf.placeholder(tf.int32, [None, 1], name="Y")
Y_onehot=tf.reshape(tf.one_hot(Y, 41), [-1, 41])
p_keep_conv = tf.placeholder(tf.float32, name="p_keep_conv")
p_keep_hidden = tf.placeholder(tf.float32, name="p_keep_hidden")

# L1 SoundIn shape=(?, 20, 100, 1)
W1 = tf.get_variable("W1", shape=[2, 10, 1, 32],initializer=tf.contrib.layers.xavier_initializer())
L1 = tf.nn.conv2d(X_sound, W1, strides=[1, 1, 1, 1], padding='SAME')
L1 = tf.nn.elu(L1)
L1 = tf.nn.max_pool(L1, ksize=[1, 3, 3, 1],strides=[1, 3, 3, 1], padding='SAME') 
L1 = tf.nn.dropout(L1, p_keep_conv)

# L2 Input shape=(?,7,34,32)
W2 = tf.get_variable("W2", shape=[2, 10, 32, 64],initializer=tf.contrib.layers.xavier_initializer())
L2 = tf.nn.conv2d(L1, W2, strides=[1, 1, 1, 1], padding='SAME')
L2 = tf.nn.elu(L2)
L2 = tf.nn.max_pool(L2, ksize=[1, 3, 3, 1],strides=[1, 3, 3, 1], padding='SAME') 
L2 = tf.nn.dropout(L2, p_keep_conv)

# L3 Input shape=(?,3,12,64)
W3 = tf.get_variable("W3", shape=[2, 10, 64, 128],initializer=tf.contrib.layers.xavier_initializer())
L3 = tf.nn.conv2d(L2, W3, strides=[1, 1, 1, 1], padding='SAME')
L3 = tf.nn.elu(L3)
L3 = tf.nn.max_pool(L3, ksize=[1, 3, 3, 1],strides=[1, 3, 3, 1], padding='SAME') 
L3 = tf.nn.dropout(L3, p_keep_conv)
L3_flat= tf.reshape(L3, shape=[-1, 4*128])

# Final FC 2*3*128 inputs -> 41 outputs
W4 = tf.get_variable("W4", shape=[4*128, 512],initializer=tf.contrib.layers.xavier_initializer())
L4 = tf.nn.elu(tf.matmul(L3_flat, W4))
L4 = tf.nn.dropout(L4, p_keep_hidden)
W_o = tf.get_variable("W_o", shape=[512,41],initializer=tf.contrib.layers.xavier_initializer())
b = tf.Variable(tf.random_normal([41]))
logits = tf.matmul(L4, W_o) + b

# define cost/loss & optimizer
cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=logits,labels= Y_onehot))
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost) # 아담버젼
predict_op = tf.argmax(logits, 1, name="pred")

# initialize
sess = tf.Session()
sess.run(tf.global_variables_initializer())
saver = tf.train.Saver()

# train my model
print('Learning started. It takes sometime.')
for epoch in range(training_epochs):
    avg_cost = 0
    total_batch = int(len(trainData) / batch_size)
    for i in range(total_batch):
        batch_xs = trainData[i*batch_size:(i+1)*batch_size]
        batch_ys = trainLabel[i*batch_size:(i+1)*batch_size].reshape(-1, 1)
        feed_dict = {X: batch_xs, Y: batch_ys, p_keep_conv: .8, p_keep_hidden: 0.7}
        c, _ = sess.run([cost, optimizer], feed_dict=feed_dict)
        avg_cost += c / total_batch
    print('Epoch:', '%04d' % (epoch + 1), 'cost =', '{:.9f}'.format(avg_cost))
    if epoch % steps_for_validate == steps_for_validate-1:
        correct_prediction = tf.equal(tf.argmax(logits, 1), tf.argmax(Y_onehot, 1))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
        x=np.random.choice(testLabel.shape[0], 300, replace=False)
        print('Accuracy:', sess.run(accuracy, feed_dict={
                X: testData[x], Y: testLabel[x].reshape(-1, 1), p_keep_conv: 1, p_keep_hidden: 1}))
        save_path = saver.save(sess, '/home/paperspace/Downloads/optx/optx')
print('Finished!')

"""
1) conv2d layer * 2 + FC 
learning_rate = 0.001
training_epochs = 500
p_keep_conv, p_keep_hidden = 0.7, 0.5
accuracy : 36~46% (epoch 50 이상부터 계속 왔다갔다 함)
2) 위랑 같음
lr=0.0002~5, epoch = 500
accuracy : 43~53% 
3) con2d layer * 3 + FC
lr=0.0002, epoch = 300    
p_keep_conv, p_keep_hidden = 0.8, 0.7
win : (2, 10), (2,2), (2,2)
max_pool : (2,5), (3,3), (3,3)
accuracy: 51~60%
4) 3에서 윈도우 조절
win : (2, 10), (2,4), (2,3)
max_pool : (2,5), (3,3), (3,3)
accuracy: 53~65%
5) 3에서 윈도우 조절2
win : (2, 10), (2,10), (2,10)
max_pool : (3,3), (3,3), (3,3)
 
"""