# services/embedding_service.py

import os
import cv2
import numpy as np
from datetime import datetime
from database.models import db, FaceEmbedding, Student
from services.face_detection import FaceDetector
from services.face_recognition import FaceRecognizer
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for managing face embeddings"""
    
    def __init__(self):
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer()
    
    def process_image(self, image_path):
        """
        Process image and extract embedding
        
        Args:
            image_path: Path to image file
            
        Returns:
            {
                'embedding': numpy array,
                'quality': float,
                'success': bool
            }
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                return {'embedding': None, 'quality': 0.0, 'success': False}
            
            # Detect faces
            faces = self.face_detector.detect_faces(image)
            if not faces:
                return {'embedding': None, 'quality': 0.0, 'success': False}
            
            # Get largest face
            best_face = max(faces, key=lambda f: f['width'] * f['height'])
            face_crop = self.face_detector.extract_face(image, best_face['bbox'])
            
            # Extract embedding
            embedding = self.face_recognizer.extract_embedding(face_crop)
            if embedding is None:
                return {'embedding': None, 'quality': 0.0, 'success': False}
            
            # Calculate quality
            quality = best_face['confidence']
            
            return {
                'embedding': embedding,
                'quality': quality,
                'success': True
            }
        
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return {'embedding': None, 'quality': 0.0, 'success': False}
    
    def register_student_faces(self, student_id, image_paths, image_type='normal'):
        """
        Register multiple face images for a student
        
        Args:
            student_id: Student database ID
            image_paths: List of image paths
            image_type: 'normal' or 'masked'
            
        Returns:
            {
                'success': bool,
                'processed': int,
                'failed': int,
                'embeddings': int
            }
        """
        processed = 0
        failed = 0
        embeddings_count = 0
        
        try:
            for image_path in image_paths:
                result = self.process_image(image_path)
                
                if not result['success']:
                    failed += 1
                    continue
                
                # Save embedding to database
                embedding_record = FaceEmbedding(
                    student_id=student_id,
                    embedding=None,  # Will be set below
                    image_path=image_path,
                    image_type=image_type,
                    face_quality=result['quality'],
                    is_active=True
                )
                embedding_record.set_embedding(result['embedding'])
                
                db.session.add(embedding_record)
                processed += 1
                embeddings_count += 1
            
            db.session.commit()
            
            logger.info(f"Registered {embeddings_count} embeddings for student {student_id}")
            
            return {
                'success': True,
                'processed': processed,
                'failed': failed,
                'embeddings': embeddings_count
            }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering student faces: {e}")
            return {
                'success': False,
                'processed': processed,
                'failed': failed,
                'embeddings': 0
            }
    
    def get_student_embeddings(self, student_id):
        """
        Get all embeddings for a student
        
        Args:
            student_id: Student database ID
            
        Returns:
            List of embeddings with metadata
        """
        try:
            embeddings = FaceEmbedding.query.filter_by(
                student_id=student_id,
                is_active=True
            ).all()
            
            result = []
            for emb in embeddings:
                result.append({
                    'student_id': student_id,
                    'embedding': emb.get_embedding(),
                    'image_type': emb.image_type,
                    'quality': emb.face_quality
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Error fetching student embeddings: {e}")
            return []
    
    def update_embeddings(self, student_id, image_paths, image_type='normal'):
        """
        Update student embeddings (replace existing)
        
        Args:
            student_id: Student database ID
            image_paths: List of image paths
            image_type: 'normal' or 'masked'
            
        Returns:
            Success status
        """
        try:
            # Delete existing embeddings of this type
            FaceEmbedding.query.filter_by(
                student_id=student_id,
                image_type=image_type
            ).delete()
            
            # Register new embeddings
            result = self.register_student_faces(student_id, image_paths, image_type)
            
            return result['success']
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating embeddings: {e}")
            return False