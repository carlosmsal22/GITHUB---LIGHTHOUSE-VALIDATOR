import numpy as np
import cv2
import urllib.request
from keras.applications.resnet50 import ResNet50, preprocess_input, decode_predictions
from keras.utils import img_to_array

def download_image(url, filename):
    """Download image from URL and save locally"""
    urllib.request.urlretrieve(url, filename)
    return filename

def classify_image(img_path):
    # Load model
    model = ResNet50(weights='imagenet')
    
    # Load and preprocess image
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Could not read image from {img_path}")
    
    img = cv2.resize(img, (224, 224))
    x = img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    
    # Predict and return results
    preds = model.predict(x)
    return decode_predictions(preds, top=3)[0]

if __name__ == '__main__':
    # Imgur direct image URL (use i.imgur.com with file extension)
    imgur_url = "https://i.imgur.com/v1Q5RYu.jpg"  # Added .jpg extension
    local_filename = "temp_image.jpg"
    
    try:
        # Download image
        print(f"Downloading image from {imgur_url}...")
        download_image(imgur_url, local_filename)
        
        # Classify image
        print("Classifying image...")
        result = classify_image(local_filename)
        print("Predicted:", result)
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Clean up (remove temporary file)
        import os
        if os.path.exists(local_filename):
            os.remove(local_filename)
