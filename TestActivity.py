import cv2
import numpy as np
from keras.models import model_from_json

# Load the trained emotion detection model
emotion_dict = {0: "Dead Bee", 1: "Nectar Collection", 2: "Nesting", 3: "Possible Damage", 4: "Regular Activity"}
json_file = open('Activity_transfer_learning.json', 'r')
loaded_model_json = json_file.read()
json_file.close()
emotion_model = model_from_json(loaded_model_json)
emotion_model.load_weights("Activity_transfer_learning.h5")
print("Loaded model from disk")

# Function to preprocess the image before emotion prediction
def preprocess_image(img):
    resized_img = cv2.resize(img, (48, 48))  # Resize without converting to grayscale
    normalized_img = resized_img / 255.0  # Normalize pixel values
    reshaped_img = np.expand_dims(normalized_img, axis=0)  # Add batch dimension
    return reshaped_img

# start the webcam feed
cap = cv2.VideoCapture(0)  # Use 0 for webcam

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Preprocess the frame and make emotion prediction
    processed_frame = preprocess_image(frame)
    emotion_prediction = emotion_model.predict(processed_frame)
    maxindex = int(np.argmax(emotion_prediction))
    cv2.putText(frame, emotion_dict[maxindex], (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

    # Display the frame with predictions
    cv2.imshow('Bee Monitoring', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
