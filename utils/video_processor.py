import cv2
import numpy as np
from datetime import datetime
import re
import time
import os
from ultralytics import YOLO
import face_recognition
try:
    import yt_dlp
except ImportError:
    print("Please install yt-dlp: pip install yt-dlp")

class VideoProcessor:
    def __init__(self):
        self.streams = {
            'cash_drawer': None,
            'employee_detection': None,
            'door_detection': None,
            'people_counting': None,
            'face_recognition': None
        }
        self.results = {
            'cash_drawer': False,
            'employee_detection': False,
            'door_detection': {'detected': False, 'status': 'Unknown', 'movement': None},
            'people_counting': {'male': 0, 'female': 0, 'total': 0},
            'face_recognition': []
        }
        # Load the YOLOv8 model for door detection
        self.door_model = YOLO('models/door_detection.pt')
        
        # Load face detection model
        self.face_net = cv2.dnn.readNetFromCaffe("models/deploy.prototxt", "models/res10_300x300_ssd_iter_140000.caffemodel")
        
        # Load gender detection model
        self.gender_net = cv2.dnn.readNetFromCaffe("models/gender_deploy.prototxt", "models/gender_net.caffemodel")
        
        self.gender_list = ['Male', 'Female']
        
        self.previous_door_box = None
        self.door_movement_threshold = 5  # pixels
        self.frame_size = (640, 480)  # Set a fixed frame size
        self.previous_door_frame = None
        self.motion_threshold = 1000  # Adjust this value to fine-tune motion detection sensitivity

        # Load employee face encodings
        self.known_face_encodings = []
        self.known_face_names = []
        self.load_employee_faces()

    def load_employee_faces(self):
        employee_folder = "employee_images"
        for filename in os.listdir(employee_folder):
            if filename.endswith((".jpg", ".png", ".jpeg")):
                image_path = os.path.join(employee_folder, filename)
                employee_image = face_recognition.load_image_file(image_path)
                employee_encoding = face_recognition.face_encodings(employee_image)[0]
                self.known_face_encodings.append(employee_encoding)
                self.known_face_names.append(os.path.splitext(filename)[0])
        print(f"Loaded {len(self.known_face_encodings)} employee face(s)")

    def is_youtube_url(self, url):
        youtube_regex = (
            r'(https?://)?(www\.)?'
            '(youtube|youtu|youtube-nocookie)\.(com|be)/'
            '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
        return bool(re.match(youtube_regex, url))

    def get_youtube_stream_url(self, url):
        try:
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'quiet': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info['url']
        except Exception as e:
            print(f"Error extracting YouTube URL: {str(e)}")
            return None

    def set_camera(self, stream_name, camera_input):
        try:
            # Handle different input types
            if isinstance(camera_input, str):
                if camera_input.isdigit():
                    camera_input = int(camera_input)
                elif self.is_youtube_url(camera_input):
                    camera_input = self.get_youtube_stream_url(camera_input)
                    if not camera_input:
                        return False
                elif camera_input.lower().startswith('rtsp://'):
                    return self.set_rtsp_stream(stream_name, camera_input)

            # Create video capture object
            new_cap = cv2.VideoCapture(camera_input)
            if new_cap.isOpened():
                if self.streams[stream_name]:
                    self.streams[stream_name].release()
                self.streams[stream_name] = new_cap
                return True
            return False
        except Exception as e:
            print(f"Error setting camera: {str(e)}")
            return False

    def set_rtsp_stream(self, stream_name, rtsp_url):
        try:
            # RTSP-specific options
            new_cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            new_cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Set buffer size
            new_cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            new_cap.set(cv2.CAP_PROP_FPS, 30)  # Adjust FPS if needed

            # Try to read a frame to confirm the connection
            retry_count = 0
            max_retries = 5
            while retry_count < max_retries:
                ret, frame = new_cap.read()
                if ret:
                    if self.streams[stream_name]:
                        self.streams[stream_name].release()
                    self.streams[stream_name] = new_cap
                    print(f"Successfully connected to RTSP stream for {stream_name}")
                    return True
                retry_count += 1
                time.sleep(1)  # Wait for 1 second before retrying

            print(f"Failed to connect to RTSP stream for {stream_name} after {max_retries} attempts")
            return False
        except Exception as e:
            print(f"Error setting RTSP stream: {str(e)}")
            return False

    def detect_motion(self, current_frame, previous_frame, door_box):
        if previous_frame is None:
            return False

        # Extract the door region from both frames
        x1, y1, x2, y2 = map(int, door_box)
        current_door = current_frame[y1:y2, x1:x2]
        previous_door = previous_frame[y1:y2, x1:x2]

        # Convert to grayscale
        current_gray = cv2.cvtColor(current_door, cv2.COLOR_BGR2GRAY)
        previous_gray = cv2.cvtColor(previous_door, cv2.COLOR_BGR2GRAY)

        # Calculate the absolute difference
        frame_delta = cv2.absdiff(previous_gray, current_gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) > self.motion_threshold:
                motion_detected = True
                break

        return motion_detected

    def process_frame(self, stream_name):
        if self.streams[stream_name] is None:
            return None, []

        ret, frame = self.streams[stream_name].read()
        if ret:
            # Resize the frame to a fixed size
            frame = cv2.resize(frame, self.frame_size, interpolation=cv2.INTER_AREA)
            
            if frame.shape[:2] != self.frame_size[::-1]:
                print(f"Warning: Frame size mismatch. Expected {self.frame_size[::-1]}, got {frame.shape[:2]}")
                frame = cv2.resize(frame, self.frame_size, interpolation=cv2.INTER_AREA)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            if stream_name == 'door_detection':
                rgb_frame, detections = self.process_door_detection(rgb_frame, frame)
            elif stream_name == 'people_counting':
                rgb_frame, detections = self.process_people_counting(rgb_frame, frame)
            elif stream_name == 'cash_drawer':
                rgb_frame, detections = self.process_cash_drawer(rgb_frame)
            elif stream_name == 'employee_detection':
                rgb_frame, detections = self.process_employee_detection(rgb_frame)
            elif stream_name == 'face_recognition':
                rgb_frame, detections = self.process_face_recognition(rgb_frame)
            else:
                detections = []

            return rgb_frame, detections
        return None, []

    def process_door_detection(self, rgb_frame, frame):
        # Use the YOLOv8 model for door detection
        results = self.door_model(rgb_frame)
        
        # Process the results
        door_detected = len(results[0].boxes) > 0
        self.results['door_detection']['detected'] = door_detected
        
        detections = []
        if door_detected:
            # Get the bounding box of the detected door
            box = results[0].boxes[0].xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = map(int, box)
            
            # Draw bounding box on the frame
            cv2.rectangle(rgb_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Detect motion only within the door region
            motion_detected = self.detect_motion(frame, self.previous_door_frame, box)
            
            # Check for door movement
            if self.previous_door_box is not None:
                movement = np.mean(np.abs(box - self.previous_door_box))
                if movement > self.door_movement_threshold or motion_detected:
                    self.results['door_detection']['movement'] = 'Moving'
                    self.results['door_detection']['status'] = 'Opening/Closing'
                else:
                    self.results['door_detection']['movement'] = 'Static'
                    self.results['door_detection']['status'] = 'Open/Closed'
            else:
                self.results['door_detection']['movement'] = 'Unknown'
                self.results['door_detection']['status'] = 'Detected'
            
            self.previous_door_box = box
            
            # Add motion detection information
            if motion_detected:
                cv2.putText(rgb_frame, "Motion Detected", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            detections.append(f"Door {self.results['door_detection']['status']}")
            if self.results['door_detection']['movement']:
                detections.append(f"Movement: {self.results['door_detection']['movement']}")
        else:
            self.results['door_detection']['movement'] = None
            self.results['door_detection']['status'] = 'Not Detected'
            self.previous_door_box = None
        
        self.previous_door_frame = frame
        return rgb_frame, detections

    def process_people_counting(self, rgb_frame, frame):
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
        self.face_net.setInput(blob)
        detections = self.face_net.forward()
        
        male_count = 0
        female_count = 0
        
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:
                box = detections[0, 0, i, 3:7] * np.array([frame.shape[1], frame.shape[0], frame.shape[1], frame.shape[0]])
                (x, y, x1, y1) = box.astype("int")
                
                face = frame[y:y1, x:x1]
                if face.shape[0] > 0 and face.shape[1] > 0:
                    blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), (78.4263377603, 87.7689143744, 114.895847746), swapRB=False)
                    self.gender_net.setInput(blob)
                    gender_preds = self.gender_net.forward()
                    gender = self.gender_list[gender_preds[0].argmax()]
                    
                    if gender == 'Male':
                        male_count += 1
                        color = (255, 0, 0)  # Blue for male
                    else:
                        female_count += 1
                        color = (255, 0, 255)  # Pink for female
                    
                    cv2.rectangle(rgb_frame, (x, y), (x1, y1), color, 2)
                    cv2.putText(rgb_frame, gender, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        self.results['people_counting'] = {
            'male': male_count,
            'female': female_count,
            'total': male_count + female_count
        }
        
        detections = [
            f"Male: {male_count}",
            f"Female: {female_count}",
            f"Total: {male_count + female_count}"
        ]
        return rgb_frame, detections

    def process_cash_drawer(self, rgb_frame):
        # Placeholder implementation
        self.results['cash_drawer'] = np.random.choice([True, False], p=[0.1, 0.9])
        status = "Open" if self.results['cash_drawer'] else "Closed"
        cv2.putText(rgb_frame, f"Cash Drawer: {status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        return rgb_frame, [f"Cash Drawer: {status}"]

    def process_employee_detection(self, rgb_frame):
        # Use face detection to determine if an employee is present
        face_locations = face_recognition.face_locations(rgb_frame)
        self.results['employee_detection'] = len(face_locations) > 0
        status = "Present" if self.results['employee_detection'] else "Absent"
        cv2.putText(rgb_frame, f"Employee: {status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        return rgb_frame, [f"Employee: {status}"]

    def process_face_recognition(self, rgb_frame):
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        recognized_faces = []
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = self.known_face_names[first_match_index]
                recognized_faces.append(name)

            cv2.rectangle(rgb_frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(rgb_frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        self.results['face_recognition'] = recognized_faces
        return rgb_frame, [f"Face recognized: {name}" for name in recognized_faces] if recognized_faces else ["No face recognized"]

    def release(self):
        for stream in self.streams.values():
            if stream:
                stream.release()

    def set_feature_active(self, feature_name, is_active):
        if feature_name in self.streams:
            self.streams[feature_name] = None if not is_active else self.streams[feature_name]
            print(f"Feature '{feature_name}' set to {'active' if is_active else 'inactive'}")
        else:
            print(f"Unknown feature: {feature_name}")