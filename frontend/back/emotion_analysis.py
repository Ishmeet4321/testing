import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import cv2
import numpy as np

def analyze_emotion(image_path, model_name="trpakov/vit-face-expression"):
    processor = AutoImageProcessor.from_pretrained(model_name)
    model = AutoModelForImageClassification.from_pretrained(model_name)
    image = Image.open(image_path)
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    predicted_class_idx = int(torch.argmax(outputs.logits))
    emotions = model.config.id2label[predicted_class_idx]
    return emotions
