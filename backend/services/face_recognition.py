# services/face_recognition.py

import cv2
import numpy as np
from insightface.app import FaceAnalysis
import logging
from sklearn.preprocessing import normalize

logger = logging.getLogger(__name__)


class FaceRecognizer:
    """ArcFace-based face recognition"""
    
    def __init__(self, model_name='buffalo_l'):
        """
        Initialize face recognizer
        
        Args:
            model_name: InsightFace model variant
        """
        try:
            self.app = FaceAnalysis(name=model_name, providers=['CPUProvider'])
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            self.embedding_dim = 512
            logger.info(f"✅ Face Recognizer initialized: {model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to load face recognizer: {e}")
            raise
    
    def extract_embedding(self, face_image):
        """
        Extract face embedding from face image
        
        Args:
            face_image: Face crop image
            
        Returns:
            Embedding vector (512-d) or None
        """
        try:
            # Convert BGR to RGB
            face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            
            # Detect and extract embedding
            faces = self.app.get(face_rgb)
            
            if len(faces) == 0:
                return None
            
            # Get embedding from first (largest) face
            embedding = faces[0].embedding
            
            # Normalize embedding
            embedding = normalize(embedding.reshape(1, -1)).flatten()
            
            return embedding.astype(np.float32)
        
        except Exception as e:
            logger.error(f"Error extracting embedding: {e}")
            return None
    
    def compare_embeddings(self, embedding1, embedding2, threshold=0.6):
        """
        Compare two face embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            threshold: Similarity threshold
            
        Returns:
            {
                'match': bool,
                'distance': float,
                'similarity': float
            }
        """
        try:
            if embedding1 is None or embedding2 is None:
                return {'match': False, 'distance': 1.0, 'similarity': 0.0}
            
            # Calculate cosine similarity
            embedding1 = embedding1.astype(np.float32)
            embedding2 = embedding2.astype(np.float32)
            
            # Normalize
            embedding1 = normalize(embedding1.reshape(1, -1)).flatten()
            embedding2 = normalize(embedding2.reshape(1, -1)).flatten()
            
            # Cosine similarity
            similarity = np.dot(embedding1, embedding2)
            distance = 1 - similarity
            
            match = similarity >= threshold
            
            return {
                'match': match,
                'distance': float(distance),
                'similarity': float(similarity)
            }
        
        except Exception as e:
            logger.error(f"Error comparing embeddings: {e}")
            return {'match': False, 'distance': 1.0, 'similarity': 0.0}
    
    def find_matching_student(self, embedding, student_embeddings, threshold=0.6):
        """
        Find matching student from embeddings
        
        Args:
            embedding: Input embedding
            student_embeddings: List of student embeddings from database
            threshold: Similarity threshold
            
        Returns:
            {
                'student_id': int,
                'similarity': float,
                'match': bool
            }
        """
        best_match = {
            'student_id': None,
            'similarity': -1.0,
            'match': False
        }
        
        try:
            for student_embed in student_embeddings:
                result = self.compare_embeddings(embedding, student_embed['embedding'], threshold)
                
                if result['similarity'] > best_match['similarity']:
                    best_match = {
                        'student_id': student_embed['student_id'],
                        'similarity': result['similarity'],
                        'match': result['match']
                    }
            
            return best_match
        
        except Exception as e:
            logger.error(f"Error finding matching student: {e}")
            return best_match