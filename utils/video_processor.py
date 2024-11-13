import cv2
import numpy as np
from datetime import datetime
import re
import time
from ultralytics import YOLO
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
            'employee_detection': True,
            'door_detection': {'detected': False, 'status': 'Unknown', 'movement': None},
            'people_counting': {'male': 0, 'female': 0},
            'face_recognition': []
        }
        # Load the YOLOv8 model
        self.door_model = YOLO('door_detection.pt')
        self.previous_door_box = None
        self.door_movement_threshold = 5  # pixels
        self.frame_size = (640, 480)  # Set a fixed frame size
        self.previous_door_frame = None
        self.motion_threshold = 1000  # Adjust this value to fine-tune motion detection sensitivity

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
            frame = cv2.resize(frame, self.frame_size)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            if stream_name == 'door_detection':
                # Use the YOLOv8 model for door detection
                results = self.door_model(rgb_frame)
                
                # Process the results
                door_detected = len(results[0].boxes) > 0
                self.results[stream_name]['detected'] = door_detected
                
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
                            self.results[stream_name]['movement'] = 'Moving'
                            self.results[stream_name]['status'] = 'Opening/Closing'
                        else:
                            self.results[stream_name]['movement'] = 'Static'
                            self.results[stream_name]['status'] = 'Open/Closed'
                    else:
                        self.results[stream_name]['movement'] = 'Unknown'
                        self.results[stream_name]['status'] = 'Detected'
                    
                    self.previous_door_box = box
                    
                    # Add motion detection information
                    if motion_detected:
                        cv2.putText(rgb_frame, "Motion Detected", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                else:
                    self.results[stream_name]['movement'] = None
                    self.results[stream_name]['status'] = 'Not Detected'
                    self.previous_door_box = None
                
                self.previous_door_frame = frame
            elif stream_name == 'cash_drawer':
                self.results[stream_name] = np.random.choice([True, False], p=[0.1, 0.9])
            elif stream_name == 'employee_detection':
                self.results[stream_name] = np.random.choice([True, False], p=[0.8, 0.2])
            elif stream_name == 'people_counting':
                self.results[stream_name] = {
                    'male': np.random.randint(0, 10),
                    'female': np.random.randint(0, 10)
                }
            elif stream_name == 'face_recognition':
                if np.random.random() < 0.1:
                    self.results[stream_name].append({
                        'name': f"Employee {np.random.randint(1, 100)}",
                        'time': datetime.now().strftime("%H:%M:%S")
                    })
                    if len(self.results[stream_name]) > 5:
                        self.results[stream_name].pop(0)

            detections = self.get_detections(stream_name)
            return rgb_frame, detections
        return None, []

    def get_detections(self, stream_name):
        detections = []
        if stream_name == 'door_detection':
            if self.results[stream_name]['detected']:
                detections.append(f"Door {self.results[stream_name]['status']}")
                if self.results[stream_name]['movement']:
                    detections.append(f"Movement: {self.results[stream_name]['movement']}")
        elif stream_name == 'cash_drawer' and self.results[stream_name]:
            detections.append("Cash drawer opened")
        elif stream_name == 'employee_detection' and not self.results[stream_name]:
            detections.append("No employee at cash drawer")
        return detections

    def release(self):
        for stream in self.streams.values():
            if stream:
                stream.release()