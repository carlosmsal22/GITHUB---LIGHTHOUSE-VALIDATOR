import os
import cv2
import numpy as np
import matplotlib.pyplot as plt

from keras.applications.resnet50 import ResNet50, preprocess_input, decode_predictions
from keras.preprocessing import image
