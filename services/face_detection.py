# services/face_detection.py

import cv2
import numpy as np
from ultralytics import YOLO
from config import Config
import logging

logger = logging.getLogger(__name__)


class FaceDetector:
    """YOLO-based face detection"""
    
    def __init__(self, model_name='yolov8n-face.pt'):
        """
        Initialize face detector
        
        Args:
            model_name: YOLOv8 model variant
        """
        try:
            self.model = YOLO(model_name)
            self.confidence_threshold = Config.MIN_FACE_SIZE
            logger.info(f"✅ Face Detector initialized: {model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to load face detector: {e}")
            raise
    
    def detect_faces(self, frame):
        """
        Detect faces in frame
        
        Args:
            frame: Input image frame
            
        Returns:
            List of face boxes: [(x1, y1, x2, y2, confidence), ...]
        """
        try:
            results = self.model(frame, verbose=False)[0]
            faces = []
            
            for detection in results.boxes:
                x1, y1, x2, y2 = detection.xyxy[0].cpu().numpy().astype(int)
                conf = float(detection.conf[0])
                
                # Filter by confidence
                if conf > 0.5:
                    faces.append({
                        'bbox': (x1, y1, x2, y2),
                        'confidence': conf,
                        'width': x2 - x1,
                        'height': y2 - y1
                    })
            
            return faces
        
        except Exception as e:
            logger.error(f"Error in face detection: {e}")
            return []
    
    def draw_faces(self, frame, faces, thickness=2, color=(0, 255, 0)):
        """
        Draw face bounding boxes on frame
        
        Args:
            frame: Input frame
            faces: List of face detections
            thickness: Box thickness
            color: Box color (BGR)
            
        Returns:
            Annotated frame
        """
        for face in faces:
            x1, y1, x2, y2 = face['bbox']
            conf = face['confidence']
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            cv2.putText(frame, f"Face {conf:.2f}", (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return frame
    
    def extract_face(self, frame, bbox):
        """
        Extract face region from frame
        
        Args:
            frame: Input frame
            bbox: Face bounding box (x1, y1, x2, y2)
            
        Returns:
            Face image crop
        """
        x1, y1, x2, y2 = bbox
        # Add padding
        padding = 10
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(frame.shape[1], x2 + padding)
        y2 = min(frame.shape[0], y2 + padding)
        
        return frame[y1:y2, x1:x2]
    
    def get_face_landmarks(self, frame, bbox):
        """
        Get face landmarks for alignment
        
        Args:
            frame: Input frame
            bbox: Face bounding box
            
        Returns:
            Face crop and quality score
        """
        try:
            face_crop = self.extract_face(frame, bbox)
            
            # Calculate face quality
            face_area = face_crop.shape[0] * face_crop.shape[1]
            quality_score = min(face_area / (640 * 480), 1.0)
            
            return face_crop, quality_score
        
        except Exception as e:
            logger.error(f"Error extracting face landmarks: {e}")
            return None, 0.0