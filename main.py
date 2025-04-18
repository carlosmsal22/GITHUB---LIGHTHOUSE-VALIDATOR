# main.py

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from fastapi import FastAPI
from keras.applications.resnet50 import ResNet50, preprocess_input, decode_predictions
from keras.preprocessing import image

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Lighthouse Validator is live and ready 🚀"}
