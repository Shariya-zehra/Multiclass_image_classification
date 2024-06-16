# -*- coding: utf-8 -*-
"""multiple_img.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1Eo43EbsB21bR4zp6KCBrEiQ9pgmVtWzj
"""

import os
import xml.etree.ElementTree as ET
import cv2
import numpy as np

import matplotlib.pyplot as plt
import random
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dense, Flatten, Dropout, Normalization
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

import zipfile
import os
import shutil
from google.colab import files
uploaded = files.upload()

for filename in uploaded.keys():
    print('Uploaded file "{name}" with length {length} bytes'.format(
        name=filename, length=len(uploaded[filename])))

!kaggle datasets download -d jessicali9530/stanford-dogs-dataset

from zipfile import ZipFile
file_name="/content/stanford-dogs-dataset.zip"
with ZipFile(file_name,'r') as zip:
  zip.extractall()
  print('Done')

def parse_annotation(file_path):

     tree = ET.parse(file_path)
     root = tree.getroot()

     image_path = file_path.replace('annotations', 'images').replace('Annotation', 'Images')+'.jpg'
     class_name = root.find('object').find('name').text

     bndbox = root.find('object').find('bndbox')
     xmin = int(bndbox.find('xmin').text)
     ymin = int(bndbox.find('ymin').text)
     xmax = int(bndbox.find('xmax').text)
     ymax = int(bndbox.find('ymax').text)


     return image_path, class_name, (xmin, ymin, xmax, ymax)

def preprocess_image(image_path, bbox):
    image = cv2.imread(image_path)
    if image is not None:
        xmin, ymin, xmax, ymax = bbox
        cropped_image = image[ymin:ymax, xmin:xmax]
        cropped_image = cv2.resize(cropped_image, (100, 100))  # Resize to 100x100
        cropped_image = np.array(cropped_image) / 255.0
        return cropped_image
    else:
        print(f"Image at {image_path} could not be loaded.")
    return None

import os

base_images_dir = '/content/images'
base_annotations_dir = '/content/annotations'

ann_subdirectories = [
    '/content/annotations/Annotation/n02085620-Chihuahua',
    '/content/annotations/Annotation/n02085782-Japanese_spaniel',
    '/content/annotations/Annotation/n02085936-Maltese_dog',
    '/content/annotations/Annotation/n02086079-Pekinese',
    '/content/annotations/Annotation/n02086240-Shih-Tzu',
    '/content/annotations/Annotation/n02086646-Blenheim_spaniel',
    '/content/annotations/Annotation/n02086910-papillon',
    '/content/annotations/Annotation/n02087046-toy_terrier',
    '/content/annotations/Annotation/n02087394-Rhodesian_ridgeback',
    '/content/annotations/Annotation/n02088094-Afghan_hound',
]


annotation = []

for subdir in ann_subdirectories:
    if os.path.isdir(subdir):
      # print(subdir)
      all_files = os.listdir(subdir)
      #print(all_files)
      for file in all_files:
        file_path = os.path.join(subdir, file)

        image_path, class_name, bbox = parse_annotation(file_path)
        annotation.append((image_path, class_name, bbox))


desired_classes = ['Chihuahua', 'Japanese_spaniel', 'Maltese_dog',
                   'Pekinese','Shih-Tzu','Blenheim_spaniel','papillon',
                   'toy_terrier','Rhodesian_ridgeback','Afghan_hound']

# Create a dictionary mapping class names to numerical labels
class_to_label = {class_name: idx for idx, class_name in enumerate(desired_classes)}

# (0, 'Japanese_spaniel') and (1, 'Chihuahua').


X=[]
y=[]

for image_path, class_name, bbox in annotation:
    image = preprocess_image(image_path, bbox)
    if image is not None:
        X.append(image)
        y.append(class_to_label[class_name])

print(len(X))
print(len(y))


X = np.array(X)
y = np.array(y)

print(y.shape)

# one hot encoding
y = to_categorical(y, num_classes=len(desired_classes))
print(y)

# Shuffle
X, y = shuffle(X, y, random_state=42)

print('X shape:', X.shape)
print('y shape:', y.shape)

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# split data into training and validation
X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42)

print('Training data shape:', X_train.shape, y_train.shape)
print('Validation data shape:', X_val.shape, y_val.shape)
print('Test data shape:', X_test.shape, y_test.shape)

datagen = ImageDataGenerator(
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

datagen.fit(X_train)
print('Training data shape:', X_train.shape, y_train.shape)

# Build the model
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(100, 100, 3)),
    MaxPooling2D((2, 2)),
    # Dropout(0.25),

    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),
    # Dropout(0.25),

    Conv2D(128, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),
    # Dropout(0.25),

    Flatten(),
    Dense(128, activation='relu'),
    # Dropout(0.25),

    Dense(10, activation='softmax')
])

model.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'])

# Train the model

callbacks = [
    EarlyStopping(monitor='val_loss', patience=10, verbose=1),
    ReduceLROnPlateau(monitor='val_loss', factor=0.1, patience=5, min_lr=0.00001, verbose=1)
]

model.fit(datagen.flow(X_train, y_train, batch_size=32),
          epochs=30,
          validation_data=(X_val, y_val),
          callbacks=callbacks)

# Evaluate the model
loss, accuracy = model.evaluate(X_test, y_test)
print('Test Loss:', loss)
print('Test accuracy:', accuracy)

model.save('dog_breed_classifier.h5')

# Prediction function

def predict_image(index):
  image = X_test[index].reshape((1,100, 100, 3))  # model takes 4-d input size
  true_class_idx = np.argmax(y_test[index])
  true_label = desired_classes[true_class_idx]


  predicted_prob=model.predict(image)
  predicted_class_idx = np.argmax(predicted_prob, axis=1)[0]
  predicted_label= desired_classes[predicted_class_idx]

  print(predicted_prob)

  plt.figure()
  plt.imshow(X_test[index])
  plt.title(f"Predicted Label: {predicted_label}, True Label: {true_label}")
  plt.axis('off')
  plt.show()

index=random.randint(0,384)
predict_image(index)