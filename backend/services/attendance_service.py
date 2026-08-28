# backend/services/attendance_service.py

import cv2
import numpy as np
import logging
import threading
from datetime import datetime, date, time
from backend.database.models import db, Attendance, AttendanceLog, Student, FaceEmbedding
from backend.config import Config

logger = logging.getLogger(__name__)


class AttendanceService:
    """Service for real-time attendance processing"""
    
    def __init__(self, face_detector=None, face_recognizer=None, mask_detector=None):
        self.face_detector = face_detector
        self.face_recognizer = face_recognizer
        self.mask_detector = mask_detector
        self.camera = None
        self.is_running = False
        self.lock = threading.Lock()
        self.student_embeddings = []
        self.recognized_today = set()
        self.last_recognition = {}
        self.cooldown_seconds = 5
    
    def load_embeddings(self):
        """Load all student embeddings from database"""
        try:
            records = FaceEmbedding.query.filter_by(is_active=True).all()
            self.student_embeddings = []
            
            for record in records:
                emb = record.get_embedding()
                if emb is not None:
                    self.student_embeddings.append({
                        'student_id': record.student_id,
                        'embedding': emb,
                        'image_type': record.image_type
                    })
            
            logger.info(f"Loaded {len(self.student_embeddings)} embeddings for attendance")
            return len(self.student_embeddings)
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            return 0
    
    def start_camera(self, source=0):
        """Start camera capture"""
        with self.lock:
            if self.camera is not None:
                self.camera.release()
            
            self.camera = cv2.VideoCapture(source)
            if not self.camera.isOpened():
                logger.error("Cannot open camera")
                self.camera = None
                return False
            
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.is_running = True
            
            self.load_embeddings()
            self.recognized_today = set()
            self.last_recognition = {}
            
            logger.info("Camera started")
            return True
    
    def stop_camera(self):
        """Stop camera capture"""
        with self.lock:
            self.is_running = False
            if self.camera is not None:
                self.camera.release()
                self.camera = None
            logger.info("Camera stopped")
    
    def process_frame(self, frame):
        """
        Full attendance pipeline on a single frame:
        Face Detection -> Mask Detection -> Face Alignment -> ArcFace -> 
        Generate Embedding -> Compare with Database -> Identify Student -> 
        Check Today's Attendance -> Mark Attendance
        """
        if frame is None:
            return frame
        
        display_frame = frame.copy()
        
        try:
            faces = []
            if self.face_detector:
                faces = self.face_detector.detect_faces(frame)
            
            for face in faces:
                bbox = face['bbox']
                x1, y1, x2, y2 = bbox
                conf = face['confidence']
                
                face_crop = self.face_detector.extract_face(frame, bbox)
                if face_crop is None or face_crop.size == 0:
                    continue
                
                mask_info = {'mask_detected': False, 'confidence': 0.0, 'class': 'no_mask'}
                if self.mask_detector:
                    mask_info = self.mask_detector.detect_mask(face_crop)
                
                embedding = None
                if self.face_recognizer:
                    embedding = self.face_recognizer.extract_embedding(face_crop)
                
                student_id = None
                similarity = 0.0
                student_name = "Unknown"
                color = (0, 0, 255)
                
                if embedding is not None and len(self.student_embeddings) > 0:
                    match = self.face_recognizer.find_matching_student(
                        embedding, 
                        self.student_embeddings,
                        threshold=Config.RECOGNITION_THRESHOLD
                    )
                    
                    if match['match'] and match['student_id'] is not None:
                        student_id = match['student_id']
                        similarity = match['similarity']
                        
                        student = Student.query.get(student_id)
                        if student:
                            student_name = student.name
                            color = (0, 255, 0)
                            
                            self._try_mark_attendance(
                                student_id, similarity, mask_info['mask_detected']
                            )
                
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                
                label = f"{student_name} ({similarity:.0%})"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(display_frame, (x1, y1 - label_size[1] - 10), 
                            (x1 + label_size[0], y1), color, -1)
                cv2.putText(display_frame, label, (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                mask_label = "MASK" if mask_info['mask_detected'] else "NO MASK"
                mask_color = (0, 200, 200) if mask_info['mask_detected'] else (200, 200, 0)
                cv2.putText(display_frame, mask_label, (x1, y2 + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, mask_color, 2)
            
            status = f"Faces: {len(faces)} | Enrolled: {len(set(e['student_id'] for e in self.student_embeddings))} | Marked Today: {len(self.recognized_today)}"
            cv2.rectangle(display_frame, (0, 0), (640, 30), (0, 0, 0), -1)
            cv2.putText(display_frame, status, (10, 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
        
        return display_frame
    
    def _try_mark_attendance(self, student_id, confidence, mask_detected):
        import time as time_mod
        
        now = time_mod.time()
        
        last_time = self.last_recognition.get(student_id, 0)
        if now - last_time < self.cooldown_seconds:
            return
        self.last_recognition[student_id] = now
        
        if student_id in self.recognized_today:
            return
        
        try:
            today = date.today()
            existing = Attendance.query.filter_by(
                student_id=student_id,
                attendance_date=today
            ).first()
            
            if existing:
                self.recognized_today.add(student_id)
                return
            
            attendance = Attendance(
                student_id=student_id,
                attendance_date=today,
                attendance_time=datetime.now().time(),
                mask_detected=mask_detected,
                recognition_confidence=float(confidence),
                camera_source='default_camera'
            )
            db.session.add(attendance)
            
            log = AttendanceLog(
                student_id=student_id,
                event_type='marked_present',
                event_data={
                    'confidence': float(confidence),
                    'mask_detected': mask_detected,
                    'time': datetime.now().isoformat()
                }
            )
            db.session.add(log)
            db.session.commit()
            
            self.recognized_today.add(student_id)
            
            student = Student.query.get(student_id)
            name = student.name if student else f"ID:{student_id}"
            logger.info(f"Attendance marked: {name} (confidence: {confidence:.2%}, mask: {mask_detected})")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error marking attendance: {e}")
    
    def generate_frames(self):
        while self.is_running:
            with self.lock:
                if self.camera is None or not self.camera.isOpened():
                    break
                
                success, frame = self.camera.read()
            
            if not success:
                continue
            
            processed = self.process_frame(frame)
            
            ret, buffer = cv2.imencode('.jpg', processed, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        self.stop_camera()
    
    @staticmethod
    def get_today_attendance():
        today = date.today()
        records = db.session.query(Attendance, Student).join(
            Student, Attendance.student_id == Student.id
        ).filter(
            Attendance.attendance_date == today
        ).order_by(Attendance.attendance_time.desc()).all()
        
        return records
    
    @staticmethod
    def get_attendance_by_date_range(start_date, end_date, department=None):
        query = db.session.query(Attendance, Student).join(
            Student, Attendance.student_id == Student.id
        ).filter(
            Attendance.attendance_date >= start_date,
            Attendance.attendance_date <= end_date
        )
        
        if department:
            query = query.filter(Student.department == department)
        
        return query.order_by(Attendance.attendance_date.desc(), Attendance.attendance_time.desc()).all()
    
    @staticmethod
    def get_attendance_stats():
        today = date.today()
        
        total_students = Student.query.filter_by(is_active=True).count()
        today_present = Attendance.query.filter_by(attendance_date=today).count()
        
        today_mask = Attendance.query.filter_by(
            attendance_date=today, mask_detected=True
        ).count()
        today_no_mask = today_present - today_mask
        
        if total_students > 0:
            attendance_rate = round((today_present / total_students) * 100, 1)
        else:
            attendance_rate = 0
        
        total_embeddings = FaceEmbedding.query.filter_by(is_active=True).count()
        enrolled_students = db.session.query(
            FaceEmbedding.student_id
        ).filter_by(is_active=True).distinct().count()
        
        return {
            'total_students': total_students,
            'today_present': today_present,
            'today_absent': total_students - today_present,
            'today_mask': today_mask,
            'today_no_mask': today_no_mask,
            'attendance_rate': attendance_rate,
            'total_embeddings': total_embeddings,
            'enrolled_students': enrolled_students
        }
    
    @staticmethod
    def get_weekly_stats():
        from datetime import timedelta
        
        stats = []
        for i in range(6, -1, -1):
            d = date.today() - timedelta(days=i)
            count = Attendance.query.filter_by(attendance_date=d).count()
            stats.append({
                'date': d.strftime('%a'),
                'full_date': d.strftime('%d %b'),
                'count': count
            })
        
        return stats
    
    @staticmethod
    def get_department_stats():
        today = date.today()
        results = db.session.query(
            Student.department,
            db.func.count(Attendance.id)
        ).join(
            Attendance, Student.id == Attendance.student_id
        ).filter(
            Attendance.attendance_date == today
        ).group_by(Student.department).all()
        
        return [{'department': r[0] or 'Unknown', 'count': r[1]} for r in results]