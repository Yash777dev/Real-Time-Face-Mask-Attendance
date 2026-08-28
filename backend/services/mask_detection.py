# services/mask_detection.py

import cv2
import numpy as np
from ultralytics import YOLO
import logging

logger = logging.getLogger(__name__)


class MaskDetector:
    """Mask detection using YOLOv8"""
    
    def __init__(self, model_path='mask_detector.pt'):
        """
        Initialize mask detector
        
        Args:
            model_path: Path to mask detection model
        """
        try:
            self.model = YOLO(model_path)
            logger.info(f"✅ Mask Detector initialized: {model_path}")
        except Exception as e:
            logger.warning(f"⚠️ Mask detector not available: {e}")
            self.model = None
    
    def detect_mask(self, face_image):
        """
        Detect if face is wearing mask
        
        Args:
            face_image: Face crop image
            
        Returns:
            {
                'mask_detected': bool,
                'confidence': float,
                'class': 'mask' or 'no_mask'
            }
        """
        if self.model is None:
            return {'mask_detected': False, 'confidence': 0.0, 'class': 'no_mask'}
        
        try:
            results = self.model(face_image, verbose=False)[0]
            
            if len(results.boxes) == 0:
                return {'mask_detected': False, 'confidence': 0.0, 'class': 'no_mask'}
            
            # Get the prediction with highest confidence
            best_detection = results.boxes[0]
            class_id = int(best_detection.cls[0])
            confidence = float(best_detection.conf[0])
            
            # Assuming class 0 = mask, class 1 = no_mask
            mask_detected = class_id == 0
            class_name = 'mask' if mask_detected else 'no_mask'
            
            return {
                'mask_detected': mask_detected,
                'confidence': confidence,
                'class': class_name
            }
        
        except Exception as e:
            logger.error(f"Error in mask detection: {e}")
            return {'mask_detected': False, 'confidence': 0.0, 'class': 'no_mask'}
    
    def visualize_mask(self, frame, mask_info, position=(10, 30)):
        """
        Draw mask detection result on frame
        
        Args:
            frame: Input frame
            mask_info: Mask detection result
            position: Text position
            
        Returns:
            Annotated frame
        """
        mask_text = f"Mask: {mask_info['class'].upper()} ({mask_info['confidence']:.2f})"
        color = (0, 255, 0) if mask_info['mask_detected'] else (0, 0, 255)
        
        cv2.putText(frame, mask_text, position,
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        return frame