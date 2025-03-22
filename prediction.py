import cv2
import numpy as np
from keras.models import load_model
from keras.applications.resnet50 import preprocess_input
import json

# Load the trained model
model_path = 'newcnn5.h5'
model = load_model(model_path)

# Load the skin disorder treatments from the JSON file
with open('skin_disorder.json', 'r') as file:
    skin_disorder_data = json.load(file)

# Define the class names
class_names = ["Acne", "Actinic Keratosis", "Atopic Dermatitis", "Eczema", "Melanoma","seborheic keratoses", "Psoriasis", "Tinea Ringworm"]

# Function to preprocess input image
def preprocess_image(img):
    img = cv2.resize(img, (224, 224))
    img = np.expand_dims(img, axis=0)  # Add batch dimension
    img = preprocess_input(img)
    return img

# Function to predict disease
def predict_disease(image_data, threshold=0.8):
    # Decode the image
    img = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
    # Preprocess the image
    input_image = preprocess_image(img)
    # Get predictions
    predictions = model.predict(input_image)
    # Get the predicted class index and name
    predicted_class_index = np.argmax(predictions[0])
    predicted_class_name = class_names[predicted_class_index]
    # Get the confidence score of the prediction
    confidence = np.max(predictions[0])
    
    # Check if the confidence is below the threshold
    if confidence < threshold:
        return img, "Healthy Skin.", "No treatment information available.", round(confidence, 2)
    
    # Get treatment information
    treatment_info = skin_disorder_data.get(predicted_class_name, "No treatment information available.")
    return img, predicted_class_name, treatment_info, round(confidence, 2)

