// IMG AI Studio - Main Application
class ImgAIApp {
    constructor() {
        this.camera = document.getElementById('camera');
        this.snapshot = document.getElementById('snapshot');
        this.preview = document.getElementById('preview');
        this.stream = null;
        this.currentImageData = null;
        this.currentImageFile = null;

        this.initElements();
        this.bindEvents();
        this.checkStatus();
        this.loadGallery();
    }

    initElements() {
        // Buttons
        this.btnCamera = document.getElementById('btn-camera');
        this.btnCapture = document.getElementById('btn-capture');
        this.btnGenerate = document.getElementById('btn-generate');
        this.btnDownload = document.getElementById('btn-download');
        this.btnRetry = document.getElementById('btn-retry');
        this.btnNew = document.getElementById('btn-new');
        this.btnRefreshGallery = document.getElementById('btn-refresh-gallery');
        this.fileInput = document.getElementById('file-input');

        // Settings
        this.strengthSlider = document.getElementById('strength');
        this.strengthValue = document.getElementById('strength-value');
        this.promptInput = document.getElementById('prompt');

        // Results
        this.resultSection = document.querySelector('.result-section');
        this.originalResult = document.getElementById('original-result');
        this.generatedResult = document.getElementById('generated-result');

        // Loading
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.loadingText = document.getElementById('loading-text');
        this.progress = document.getElementById('progress');

        // Status
        this.gpuStatus = document.getElementById('gpu-status');
        this.modelStatus = document.getElementById('model-status');

        // Gallery
        this.gallery = document.getElementById('gallery');
    }

    bindEvents() {
        this.btnCamera.addEventListener('click', () => this.toggleCamera());
        this.btnCapture.addEventListener('click', () => this.capturePhoto());
        this.btnGenerate.addEventListener('click', () => this.generateImage());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        this.strengthSlider.addEventListener('input', (e) => {
            this.strengthValue.textContent = e.target.value;
        });

        this.btnDownload?.addEventListener('click', () => this.downloadResult());
        this.btnRetry?.addEventListener('click', () => this.generateImage());
        this.btnNew?.addEventListener('click', () => this.resetToNew());
        this.btnRefreshGallery?.addEventListener('click', () => this.loadGallery());
    }

    async toggleCamera() {
        if (this.stream) {
            this.stopCamera();
        } else {
            await this.startCamera();
        }
    }

    async startCamera() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                }
            });

            this.camera.srcObject = this.stream;
            this.camera.style.display = 'block';
            this.preview.style.display = 'none';

            this.btnCamera.innerHTML = '<span class="icon">🛑</span> 카메라 끄기';
            this.btnCapture.disabled = false;

            this.showToast('카메라가 시작되었습니다', 'success');
        } catch (error) {
            console.error('카메라 접근 오류:', error);
            this.showToast('카메라에 접근할 수 없습니다. 권한을 확인해주세요.', 'error');
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        this.camera.srcObject = null;
        this.btnCamera.innerHTML = '<span class="icon">📷</span> 카메라 시작';
        this.btnCapture.disabled = true;
    }

    capturePhoto() {
        const ctx = this.snapshot.getContext('2d');
        this.snapshot.width = this.camera.videoWidth;
        this.snapshot.height = this.camera.videoHeight;

        ctx.drawImage(this.camera, 0, 0);

        this.currentImageData = this.snapshot.toDataURL('image/jpeg', 0.9);

        // Convert to blob for upload
        this.snapshot.toBlob((blob) => {
            this.currentImageFile = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
        }, 'image/jpeg', 0.9);

        this.preview.src = this.currentImageData;
        this.preview.style.display = 'block';
        this.camera.style.display = 'none';

        this.stopCamera();
        this.btnGenerate.disabled = false;

        this.showToast('사진이 촬영되었습니다!', 'success');
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            this.showToast('이미지 파일만 선택할 수 있습니다.', 'error');
            return;
        }

        this.currentImageFile = file;

        const reader = new FileReader();
        reader.onload = (e) => {
            this.currentImageData = e.target.result;
            this.preview.src = this.currentImageData;
            this.preview.style.display = 'block';
            this.camera.style.display = 'none';
            this.stopCamera();
            this.btnGenerate.disabled = false;
        };
        reader.readAsDataURL(file);

        this.showToast('이미지가 로드되었습니다!', 'success');
    }

    async generateImage() {
        if (!this.currentImageFile && !this.currentImageData) {
            this.showToast('먼저 이미지를 선택하거나 촬영해주세요.', 'error');
            return;
        }

        const style = document.querySelector('input[name="style"]:checked').value;
        const strength = this.strengthSlider.value;
        const prompt = this.promptInput.value;

        this.showLoading(true);
        this.updateProgress(0);

        try {
            // Upload image
            this.loadingText.textContent = '이미지 업로드 중...';
            this.updateProgress(10);

            const formData = new FormData();
            formData.append('image', this.currentImageFile);
            formData.append('style', style);
            formData.append('strength', strength);
            formData.append('prompt', prompt);

            const uploadResponse = await fetch('php/upload.php', {
                method: 'POST',
                body: formData
            });

            const uploadResult = await uploadResponse.json();

            if (!uploadResult.success) {
                throw new Error(uploadResult.error || '업로드 실패');
            }

            this.updateProgress(30);
            this.loadingText.textContent = 'AI 변환 시작...';

            // Start generation
            const generateResponse = await fetch('php/generate.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: uploadResult.filename,
                    style: style,
                    strength: parseFloat(strength),
                    prompt: prompt
                })
            });

            // Poll for progress
            await this.pollProgress(uploadResult.filename);

            const generateResult = await generateResponse.json();

            if (!generateResult.success) {
                throw new Error(generateResult.error || '생성 실패');
            }

            // Show results
            this.originalResult.src = 'uploads/' + uploadResult.filename;
            this.generatedResult.src = 'outputs/' + generateResult.output;
            this.resultSection.style.display = 'block';

            this.showToast('이미지 변환이 완료되었습니다!', 'success');
            this.loadGallery();

        } catch (error) {
            console.error('생성 오류:', error);
            this.showToast('오류: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async pollProgress(filename) {
        const messages = [
            'AI가 이미지를 분석하는 중...',
            '스타일 특징을 추출하는 중...',
            '새로운 이미지를 생성하는 중...',
            '디테일을 다듬는 중...',
            '마무리 작업 중...'
        ];

        for (let i = 0; i < 5; i++) {
            await this.delay(2000);
            this.loadingText.textContent = messages[i];
            this.updateProgress(30 + (i * 15));

            try {
                const response = await fetch(`php/progress.php?filename=${filename}`);
                const data = await response.json();

                if (data.progress) {
                    this.updateProgress(data.progress);
                }
                if (data.status === 'complete') {
                    this.updateProgress(100);
                    break;
                }
            } catch (e) {
                // Continue polling
            }
        }
    }

    updateProgress(percent) {
        this.progress.style.width = percent + '%';
    }

    showLoading(show) {
        this.loadingOverlay.style.display = show ? 'flex' : 'none';
    }

    async loadGallery() {
        try {
            const response = await fetch('php/gallery.php');
            const data = await response.json();

            if (!data.success) {
                this.gallery.innerHTML = '<p style="color: var(--text-muted)">갤러리가 비어있습니다</p>';
                return;
            }

            this.gallery.innerHTML = data.images.map(img => `
                <div class="gallery-item" onclick="app.viewImage('${img.output}')">
                    <img src="outputs/${img.output}" alt="${img.style}" loading="lazy">
                    <div class="overlay">
                        <span>${this.getStyleName(img.style)}</span><br>
                        <small>${img.date}</small>
                    </div>
                </div>
            `).join('');

        } catch (error) {
            console.error('갤러리 로드 오류:', error);
            this.gallery.innerHTML = '<p style="color: var(--text-muted)">갤러리를 불러올 수 없습니다</p>';
        }
    }

    getStyleName(style) {
        const names = {
            'anime': '애니메이션',
            'cartoon': '카툰',
            'ghibli': '지브리',
            'comic': '코믹북'
        };
        return names[style] || style;
    }

    viewImage(filename) {
        window.open('outputs/' + filename, '_blank');
    }

    downloadResult() {
        const link = document.createElement('a');
        link.href = this.generatedResult.src;
        link.download = 'ai_generated_' + Date.now() + '.png';
        link.click();
    }

    resetToNew() {
        this.currentImageData = null;
        this.currentImageFile = null;
        this.preview.style.display = 'none';
        this.camera.style.display = 'block';
        this.resultSection.style.display = 'none';
        this.btnGenerate.disabled = true;
        this.fileInput.value = '';
    }

    async checkStatus() {
        try {
            const response = await fetch('php/status.php');
            const data = await response.json();

            this.gpuStatus.textContent = `GPU: ${data.gpu || '확인 필요'}`;
            this.modelStatus.textContent = `모델: ${data.model || '설치 필요'}`;

            if (!data.ready) {
                this.showToast('AI 모델이 설치되지 않았습니다. setup.bat을 실행해주세요.', 'error');
            }
        } catch (error) {
            this.gpuStatus.textContent = 'GPU: 연결 오류';
            this.modelStatus.textContent = '모델: 확인 필요';
        }
    }

    showToast(message, type = 'info') {
        const existing = document.querySelector('.toast');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.remove(), 4000);
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize app
const app = new ImgAIApp();
