from flask import Flask, render_template, request, jsonify, Response
import os
import numpy as np
import skimage.io
import skimage.transform
from keras.models import model_from_json
import serial
import time
import cv2

app = Flask(__name__)

# Load the model architecture for bee health
with open('health.json', 'r') as json_file:
    loaded_model_json = json_file.read()
    bee_health_model = model_from_json(loaded_model_json)

# Load model weights for bee health
bee_health_model.load_weights('bee_health.h5')

# Load the subspecies model architecture
with open('Subspecies_placeholder.json', 'r') as json_file:
    subspecies_model_json = json_file.read()
    subspecies_model = model_from_json(subspecies_model_json)

# Load subspecies model weights
subspecies_model.load_weights('bee_subp.h5')

# Load the model architecture for beehive health
with open('Hive_health.json', 'r') as json_file:
    hive_model_json = json_file.read()
    hive_model = model_from_json(hive_model_json)

# Load model weights for beehive health
hive_model.load_weights('beehive_health.h5')

# Path to the uploaded bee images
UPLOAD_FOLDER_BEE = 'static1/images'
app.config['UPLOAD_FOLDER_BEE'] = UPLOAD_FOLDER_BEE

# Path to the uploaded beehive images
UPLOAD_FOLDER_BEEHIVE = 'static2/images'
app.config['UPLOAD_FOLDER_BEEHIVE'] = UPLOAD_FOLDER_BEEHIVE

# Health categories mapping for bee
health_mapping = {0: 'unhealthy', 1: 'healthy', 2: 'Possible bodily damages', 3: 'few varroa, hive beetles'}

# Health categories mapping for beehive
health_mapping_beehive = {0: 'Unhealthy', 1: 'Healthy'}

# Subspecies labels for bee
subspecies_labels = ['The rock bee(Apis Dorsata)', 'The Indian hive bee(Apis cerana indica)',
                     'The little bee(Apis florea)', 'The European or Italian bee(Apis mellifera)',
                     'Dammer Bee(Melipona irridipennis)', 'VSH Italian Honey Bee']

# Load the trained emotion detection model
emotion_dict_cv = {0: "Dead Bee", 1: "Nectar Collection", 2: "Nesting", 3: "Possible Damage", 4: "Regular Activity"}
json_file_cv = open('Activity_transfer_learning.json', 'r')
loaded_model_json_cv = json_file_cv.read()
json_file_cv.close()
emotion_model_cv = model_from_json(loaded_model_json_cv)
emotion_model_cv.load_weights("Activity_transfer_learning.h5")
print("Loaded model from disk for Computer Vision")

# Load the image and preprocess it for bee health prediction
def preprocess_image_bee(image_path):
    img = skimage.io.imread(image_path)
    img = skimage.transform.resize(img, (128, 128), mode='reflect')
    img = img[np.newaxis, ...]
    return img

# Load the image and preprocess it for beehive health prediction
def preprocess_image_beehive(image_path):
    img = skimage.io.imread(image_path)
    if img.shape[2] == 4:
        img = img[:, :, :3]
    img = skimage.transform.resize(img, (128, 128), mode='reflect')
    img = img[np.newaxis, ...]
    return img

# Arduino serial communication setup
def get_arduino_data():
    try:
        ser = serial.Serial('COM9', 9600)  # Replace 'COMx' with the actual port your Arduino is connected to
        data = ser.readline().decode().strip()
        ser.close()

        if data:
            temperature, humidity = parse_data(data)
            return {'temperature': temperature, 'humidity': humidity}
    except Exception as e:
        return {'error': str(e)}

def parse_data(data):
    parts = data.split(',')
    temperature = float(parts[0].split(':')[1])
    humidity = float(parts[1].split(':')[1])
    return temperature, humidity

# Function to preprocess the image before emotion prediction
def preprocess_image(img):
    resized_img = cv2.resize(img, (48, 48))  # Resize without converting to grayscale
    normalized_img = resized_img / 255.0  # Normalize pixel values
    reshaped_img = np.expand_dims(normalized_img, axis=0)  # Add batch dimension
    return reshaped_img

def generate_frames():
    cap = cv2.VideoCapture(0)  # Use 0 for webcam
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Preprocess the frame and make emotion prediction
        processed_frame = preprocess_image(frame)
        emotion_prediction = emotion_model_cv.predict(processed_frame)
        maxindex = int(np.argmax(emotion_prediction))
        cv2.putText(frame, emotion_dict_cv[maxindex], (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
        
        # Encode the frame in JPEG format
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()
    cv2.destroyAllWindows()


     
# Route for bee prediction
@app.route('/predict/bee', methods=['GET', 'POST'])
def predict_bee():
    prediction = None
    error = None
    if request.method == 'POST':
        if 'image' not in request.files:
            error = "No image part"
        else:
            file = request.files['image']
            if file.filename == '':
                error = "No selected image"
            else:
                image_path = os.path.join(app.config['UPLOAD_FOLDER_BEE'], file.filename)
                file.save(image_path)

                try:
                    img_bee = preprocess_image_bee(image_path)
                    prediction_probs_bee = bee_health_model.predict(img_bee)
                    prediction_class_bee = np.argmax(prediction_probs_bee)
                    health_bee = health_mapping[prediction_class_bee]

                    img_subspecies = preprocess_image_bee(image_path)
                    prediction_probs_subspecies = subspecies_model.predict(img_subspecies)
                    prediction_class_subspecies = np.argmax(prediction_probs_subspecies)
                    subspecies = subspecies_labels[prediction_class_subspecies]

                    prediction = {'health': health_bee, 'subspecies': subspecies}
                except Exception as e:
                    error = f"Error processing image: {str(e)}"

    return render_template('bee.html', prediction=prediction, error=error)

# Route for beehive prediction
@app.route('/predict/beehive', methods=['GET', 'POST'])
def predict_beehive():
    prediction = None
    error = None
    arduino_data = get_arduino_data()  # Retrieve live temperature and humidity from Arduino

    if request.method == 'POST':
        if 'image' not in request.files:
            error = "No image part"
        else:
            file = request.files['image']
            if file.filename == '':
                error = "No selected image"
            else:
                image_path_beehive = os.path.join(app.config['UPLOAD_FOLDER_BEEHIVE'], file.filename)
                file.save(image_path_beehive)

                try:
                    img_beehive = preprocess_image_beehive(image_path_beehive)
                    prediction_probs_beehive = hive_model.predict(img_beehive)
                    prediction_class_beehive = np.argmax(prediction_probs_beehive)
                    health_beehive = health_mapping_beehive[prediction_class_beehive]

                    prediction = {'health': health_beehive}
                except Exception as e:
                    error = f"Error processing image: {str(e)}"

    return render_template('beehive.html', prediction=prediction, error=error, arduino_data=arduino_data)

# Additional route to fetch live data
@app.route('/get_data')
def get_data():
    arduino_data = get_arduino_data()
    return jsonify(arduino_data)

# Route for cv_monitor page
@app.route('/cv_monitor')
def cv_monitor():
    return render_template('cv_monitor.html')


# @app.route('/video_feed')
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Route for home (index) page
@app.route('/')
def home():
    arduino_data = get_arduino_data()  # Retrieve live temperature and humidity from Arduino
    return render_template('index.html', arduino_data=arduino_data)

if __name__ == '__main__':
    app.run(debug=True)
