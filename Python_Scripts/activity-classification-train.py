# -*- coding: utf-8 -*-
"""
Created on Wed Sep 21 16:02:58 2016

@author: cs390mb

Assignment 2 : Activity Recognition

This is the starter script used to train an activity recognition
classifier on accelerometer data.

See the assignment details for instructions. Basically you will train
a decision tree classifier and vary its parameters and evalute its
performance by computing the average accuracy, precision and recall
metrics over 10-fold cross-validation. You will then train another
classifier for comparison.

Once you get to part 4 of the assignment, where you will collect your
own data, change the filename to reference the file containing the
data you collected. Then retrain the classifier and choose the best
classifier to save to disk. This will be used in your final system.

Make sure to chek the assignment details, since the instructions here are
not complete.

"""

import os
import sys
import socket
import numpy as np
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeClassifier, export_graphviz
from sklearn.linear_model import LogisticRegression
from sklearn import svm
from features import extract_features # make sure features.py is in the same directory
from util import slidingWindow, reorient, reset_vars
from sklearn import cross_validation
from sklearn.metrics import confusion_matrix
import pickle

receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receive_socket.connect(("none.cs.umass.edu", 8888))
# ensures that after 1 second, a keyboard interrupt will close
receive_socket.settimeout(1.0)
# %%---------------------------------------------------------------------------
#
#		                 Load Data From Disk
#
# -----------------------------------------------------------------------------

print("Loading data...")
sys.stdout.flush()
data_file = os.path.join('data', 'my-activity-data.csv')
data = np.genfromtxt(data_file, delimiter=',')
print("Loaded {} raw labelled activity data samples.".format(len(data)))
sys.stdout.flush()

# %%---------------------------------------------------------------------------
#
#		                    Pre-processing
#
# -----------------------------------------------------------------------------

print("Reorienting accelerometer data...")
sys.stdout.flush()
reset_vars()
reoriented = np.asarray([reorient(data[i,1], data[i,2], data[i,3]) for i in range(len(data))])
reoriented_data_with_timestamps = np.append(data[:,0:1],reoriented,axis=1)
data = np.append(reoriented_data_with_timestamps, data[:,-1:], axis=1)


# %%---------------------------------------------------------------------------
#
#		                Extract Features & Labels
#
# -----------------------------------------------------------------------------

# you may want to play around with the window and step sizes
window_size = 20
step_size = 20

# sampling rate for the sample data should be about 25 Hz; take a brief window to confirm this
n_samples = 1000
time_elapsed_seconds = (data[n_samples,0] - data[0,0]) / 1000
sampling_rate = n_samples / time_elapsed_seconds

feature_names = ["mean X", "mean Y", "mean Z", "min X", "min Y", "min Z", "max X", "max Y", "max Z", "median X", "median Y", "median Z", "standardDev X", "standardDev Y", "standardDev Z", "variance X", "variance Y", "variance Z", "mean magnitude", "peaks"]
class_names = ["Stationary", "Walking"]

print("Extracting features and labels for window size {} and step size {}...".format(window_size, step_size))
sys.stdout.flush()

n_features = len(feature_names)

X = np.zeros((0,n_features))
y = np.zeros(0,)

for i,window_with_timestamp_and_label in slidingWindow(data, window_size, step_size):
    # omit timestamp and label from accelerometer window for feature extraction:
    window = window_with_timestamp_and_label[:,1:-1]
    # extract features over window:
    x = extract_features(window)
    # append features:
    X = np.append(X, np.reshape(x, (1,-1)), axis=0)
    # append label:
    y = np.append(y, window_with_timestamp_and_label[10, -1])

print("Finished feature extraction over {} windows".format(len(X)))
print("Unique labels found: {}".format(set(y)))
sys.stdout.flush()

# %%---------------------------------------------------------------------------
#
#		                    Plot data points
#
# -----------------------------------------------------------------------------

# We provided you with an example of plotting two features.
# We plotted the mean X acceleration against the mean Y acceleration.
# It should be clear from the plot that these two features are alone very uninformative.
print("Plotting data points...")
sys.stdout.flush()
plt.figure()
formats = ['bo', 'go']
for i in range(0,len(y),10): # only plot 1/10th of the points, it's a lot of data!
    plt.plot(X[i,0], X[i,1], formats[int(y[i])])

plt.show()

# %%---------------------------------------------------------------------------
#
#		                Train & Evaluate Classifier
#
# -----------------------------------------------------------------------------

n = len(y)
n_classes = len(class_names)
overallAcc = []
overallPre = []
overallRe = []

# TODO: Train and evaluate your decision tree classifier over 10-fold CV.
# Report average accuracy, precision and recall metrics.

cv = cross_validation.KFold(n, n_folds=10, shuffle=True, random_state=None)
tree = DecisionTreeClassifier(criterion="entropy", max_depth = 20)

for i, (train_indexes, test_indexes) in enumerate(cv):

    X_train = X[train_indexes, :]
    y_train = y[train_indexes]
    X_test = X[test_indexes, :]
    y_test = y[test_indexes]
    tree.fit(X_train, y_train)
    y_pred = tree.predict(X_test)

    conf = confusion_matrix(y_test, y_pred) #creation of confusion matrix

    print("Fold {}".format(i))
    print conf
    total = 0.
    correct = 0.
    average = 0.
    dimensions = conf.shape

    for row in range(dimensions[0]):
        correct = correct + conf[row][row]
        for col in range(dimensions[1]):
            total = total + (conf[row][col])
        if total == 0:
            average = 0
        else:
            average = correct/total

    #this is recall --> col movement
    for row in range(dimensions[0]):
        totalCol = 0.
        correct = conf[row][row]
        for col in range(dimensions[1]):
            totalCol = totalCol + (conf[row][col])
        if totalCol == 0 :
            tempRe = 0.
        else:
            tempRe = correct / totalCol
        overallRe.append(tempRe)

    #this is precision --> row movement
    for col in range(dimensions[1]):
        totalRow = 0.
        totalRow = totalRow + correct
        for row in range(dimensions[0]):
            totalRow = totalRow + (conf[row][col])
        if totalRow == 0 :
            tempPre = 0.
        else:
            tempPre = correct / totalRow

        overallPre.append(tempPre)
    overallAcc.append(average)
    print("\n")
print("avg accuracy: {}".format(np.sum(overallAcc)/len(overallAcc)))
print("avg precision: {}".format(np.sum(overallPre)/len(overallPre)))
print("avg recall: {}".format(np.sum(overallRe)/len(overallRe)))
tree.fit(X,y)
export_graphviz(tree, out_file='tree.dot', feature_names = feature_names)

# TODO: Once you have collected data, train your best model on the entire
# dataset. Then save it to disk as follows:

# when ready, set this to the best model you found, trained on all the data:
best_classifier = tree
with open('classifier.pickle', 'wb') as f: # 'wb' stands for 'write bytes'
    pickle.dump(best_classifier, f)
