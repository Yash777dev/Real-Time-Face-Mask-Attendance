# backend/services/embedding_service.py

import os
import cv2
import numpy as np
import logging
from backend.database.models import db, FaceEmbedding, Student
from backend.utils.helpers import get_face_images
from backend.config import Config

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing face embeddings"""

    def __init__(self, face_recognizer=None):
        self.face_recognizer = face_recognizer

    def generate_embeddings(self, student_id):
        """Generate face embeddings for a student from stored images"""
        student = Student.query.get(student_id)
        if not student:
            logger.error(f"Student ID {student_id} not found")
            return {'success': False, 'message': 'Student not found'}

        if self.face_recognizer is None:
            logger.error("Face recognizer model not loaded")
            return {'success': False, 'message': 'Recognition model not initialized'}

        normal_images = get_face_images(student_id, 'normal')
        masked_images = get_face_images(student_id, 'masked')

        if not normal_images and not masked_images:
            return {'success': False, 'message': 'No face images found for this student'}

        normal_count = 0
        masked_count = 0

        # Process normal images
        for img_path in normal_images:
            emb = self._process_and_save(student_id, img_path, 'normal')
            if emb:
                normal_count += 1

        # Process masked images
        for img_path in masked_images:
            emb = self._process_and_save(student_id, img_path, 'masked')
            if emb:
                masked_count += 1

        total = normal_count + masked_count
        logger.info(f"Generated {total} embeddings for student {student.register_number} ({normal_count} normal, {masked_count} masked)")

        return {
            'success': True,
            'message': f'Generated {total} face embeddings successfully',
            'normal_count': normal_count,
            'masked_count': masked_count,
            'total_embeddings': total
        }

    def _process_and_save(self, student_id, image_path, image_type):
        """Extract embedding from image and save to database"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                logger.warning(f"Could not read image: {image_path}")
                return None

            embedding_vector = self.face_recognizer.extract_embedding(image)
            if embedding_vector is None:
                logger.warning(f"No face detected in {image_path}")
                return None

            record = FaceEmbedding(
                student_id=student_id,
                image_path=image_path,
                image_type=image_type,
                face_quality=1.0,
                is_active=True
            )
            record.set_embedding(embedding_vector)

            db.session.add(record)
            db.session.commit()
            return embedding_vector

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing {image_path}: {e}")
            return None

    @staticmethod
    def get_embedding_stats(student_id):
        """Get embedding statistics for a student"""
        embeddings = FaceEmbedding.query.filter_by(
            student_id=student_id, is_active=True
        ).all()

        normal = sum(1 for e in embeddings if e.image_type == 'normal')
        masked = sum(1 for e in embeddings if e.image_type == 'masked')

        return {
            'total': len(embeddings),
            'normal': normal,
            'masked': masked,
            'has_embeddings': len(embeddings) > 0
        }