// camera.js — WebRTC camera capture & live attendance (Green Palette)

class FaceRegistration {
    constructor(studentId, maxCaptures = 5) {
        this.studentId = studentId;
        this.maxCaptures = maxCaptures;
        this.currentPhase = 'normal';
        this.normalCount = 0;
        this.maskedCount = 0;
        this.stream = null;
        this.video = null;
        this.canvas = null;

        this.init();
    }

    init() {
        this.video = document.getElementById('webcam');
        this.canvas = document.getElementById('captureCanvas');

        if (!this.video || !this.canvas) return;

        this.normalCount = parseInt(document.getElementById('normalCount')?.textContent || '0');
        this.maskedCount = parseInt(document.getElementById('maskedCount')?.textContent || '0');

        this.startCamera();

        document.getElementById('captureBtn')?.addEventListener('click', () => this.capture());
        document.getElementById('generateBtn')?.addEventListener('click', () => this.generateEmbeddings());
        document.getElementById('switchPhaseBtn')?.addEventListener('click', () => this.switchPhase());

        this.updateUI();
    }

    async startCamera() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480, facingMode: 'user' }
            });
            this.video.srcObject = this.stream;
            await this.video.play();
            Toast.success('Camera started');
        } catch (error) {
            Toast.error('Camera access denied. Please allow camera permissions.');
            console.error('Camera error:', error);
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }

    async capture() {
        if (!this.video || !this.canvas) return;

        const currentMax = this.maxCaptures;
        const currentCount = this.currentPhase === 'normal' ? this.normalCount : this.maskedCount;

        if (currentCount >= currentMax) {
            Toast.warning(`Maximum ${currentMax} ${this.currentPhase} images reached`);
            return;
        }

        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        const ctx = this.canvas.getContext('2d');
        ctx.drawImage(this.video, 0, 0);

        const imageData = this.canvas.toDataURL('image/jpeg', 0.9);

        try {
            const data = await apiFetch('/api/capture-image', {
                method: 'POST',
                body: JSON.stringify({
                    student_id: this.studentId,
                    image: imageData,
                    image_type: this.currentPhase
                })
            });

            if (data.success) {
                if (this.currentPhase === 'normal') {
                    this.normalCount = data.count;
                } else {
                    this.maskedCount = data.count;
                }

                Toast.success(`${this.currentPhase.toUpperCase()} image captured (${data.count}/${data.max})`);
                this.addThumbnail(imageData);

                if (this.currentPhase === 'normal' && this.normalCount >= this.maxCaptures) {
                    setTimeout(() => {
                        this.currentPhase = 'masked';
                        Toast.info('Phase 1 complete! Now capture images with a mask.');
                        this.updateUI();
                    }, 500);
                }
            } else {
                Toast.error(data.message || 'Capture failed');
            }
        } catch (error) {
            Toast.error('Error capturing image: ' + error.message);
        }

        this.updateUI();
    }

    addThumbnail(imageData) {
        const gridId = this.currentPhase === 'normal' ? 'normalGrid' : 'maskedGrid';
        const grid = document.getElementById(gridId);
        if (!grid) return;

        const placeholder = grid.querySelector('.image-placeholder');
        if (placeholder) placeholder.remove();

        const img = document.createElement('img');
        img.src = imageData;
        img.alt = `${this.currentPhase} face capture`;
        grid.appendChild(img);
    }

    switchPhase() {
        if (this.currentPhase === 'normal') {
            this.currentPhase = 'masked';
            Toast.info('Switched to MASKED capture mode.');
        } else {
            this.currentPhase = 'normal';
            Toast.info('Switched to NORMAL capture mode.');
        }
        this.updateUI();
    }

    async generateEmbeddings() {
        if (this.normalCount === 0 && this.maskedCount === 0) {
            Toast.warning('Please capture face images first');
            return;
        }

        const btn = document.getElementById('generateBtn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating embeddings...';
        }

        try {
            const data = await apiFetch(`/api/generate-embeddings/${this.studentId}`, {
                method: 'POST'
            });

            if (data.success) {
                Toast.success(data.message);
                const embCount = document.getElementById('embeddingCount');
                if (embCount) {
                    const total = (data.normal_count || 0) + (data.masked_count || 0);
                    embCount.textContent = total;
                }

                if (btn) {
                    btn.innerHTML = '<i class="fa-solid fa-check"></i> Embeddings Generated!';
                    btn.classList.add('btn-primary');
                }
            } else {
                Toast.error(data.message || 'Failed to generate embeddings');
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-brain"></i> Generate Embeddings';
                }
            }
        } catch (error) {
            Toast.error('Error: ' + error.message);
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-brain"></i> Generate Embeddings';
            }
        }
    }

    updateUI() {
        const normalCountEl = document.getElementById('normalCount');
        const maskedCountEl = document.getElementById('maskedCount');
        if (normalCountEl) normalCountEl.textContent = this.normalCount;
        if (maskedCountEl) maskedCountEl.textContent = this.maskedCount;

        const normalProgress = document.getElementById('normalProgress');
        const maskedProgress = document.getElementById('maskedProgress');
        if (normalProgress) normalProgress.style.width = `${(this.normalCount / this.maxCaptures) * 100}%`;
        if (maskedProgress) maskedProgress.style.width = `${(this.maskedCount / this.maxCaptures) * 100}%`;

        const captureBtn = document.getElementById('captureBtn');
        if (captureBtn) {
            const icon = this.currentPhase === 'masked' ? 'fa-mask' : 'fa-camera';
            captureBtn.innerHTML = `<i class="fa-solid ${icon}"></i> Capture ${this.currentPhase.toUpperCase()} Image`;
        }

        const generateBtn = document.getElementById('generateBtn');
        if (generateBtn) {
            generateBtn.style.display = (this.normalCount > 0 || this.maskedCount > 0) ? 'inline-flex' : 'none';
        }
    }
}

class LiveAttendance {
    constructor() {
        this.isRunning = false;
        this.feedImg = document.getElementById('videoFeed');
        this.startBtn = document.getElementById('startCameraBtn');
        this.stopBtn = document.getElementById('stopCameraBtn');

        if (this.startBtn) this.startBtn.addEventListener('click', () => this.start());
        if (this.stopBtn) this.stopBtn.addEventListener('click', () => this.stop());
    }

    async start() {
        try {
            const data = await apiFetch('/attendance/start', { method: 'POST' });

            if (data.success) {
                this.isRunning = true;
                Toast.success('Camera started');

                if (this.feedImg) {
                    this.feedImg.src = '/attendance/video_feed?' + Date.now();
                    this.feedImg.style.display = 'block';
                }

                const statusDot = document.querySelector('.status-dot');
                if (statusDot) statusDot.classList.add('live');

                if (this.startBtn) this.startBtn.style.display = 'none';
                if (this.stopBtn) this.stopBtn.style.display = 'inline-flex';

                this.pollStatus();
            }
        } catch (error) {
            Toast.error('Failed to start camera: ' + error.message);
        }
    }

    async stop() {
        try {
            await apiFetch('/attendance/stop', { method: 'POST' });
            this.isRunning = false;

            if (this.feedImg) {
                this.feedImg.src = '';
                this.feedImg.style.display = 'none';
            }

            const statusDot = document.querySelector('.status-dot');
            if (statusDot) statusDot.classList.remove('live');

            if (this.startBtn) this.startBtn.style.display = 'inline-flex';
            if (this.stopBtn) this.stopBtn.style.display = 'none';

            Toast.info('Camera stopped');
        } catch (error) {
            Toast.error('Error stopping camera: ' + error.message);
        }
    }

    async pollStatus() {
        if (!this.isRunning) return;

        try {
            const data = await apiFetch('/attendance/status');
            const markedEl = document.getElementById('markedToday');
            if (markedEl) markedEl.textContent = data.recognized_today || 0;

            const embeddedEl = document.getElementById('loadedEmbeddings');
            if (embeddedEl) embeddedEl.textContent = data.embeddings_loaded || 0;
        } catch (error) {
            console.error('Status poll error:', error);
        }

        if (this.isRunning) {
            setTimeout(() => this.pollStatus(), 5000);
        }
    }
}
