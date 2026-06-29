// ============================================================
// face-camera.js — 관상용 카메라 촬영 모달
// 사용자 요청: 파일 업로드 X, 카메라로 즉시 촬영.
// WebRTC getUserMedia → video preview → canvas capture → base64 dataURL.
// 모바일/데스크탑 모두 동작. 전·후면 카메라 전환 지원.
// 캡쳐된 base64는 window.__getCapturedFacePhoto()로 접근.
// ============================================================
(function () {
  let stream = null;
  let facingMode = 'user'; // 전면 카메라 default
  let capturedBase64 = null;

  // 외부에서 캡쳐된 사진 가져가는 인터페이스
  window.__getCapturedFacePhoto = () => capturedBase64;
  window.__clearCapturedFacePhoto = () => { capturedBase64 = null; updatePreview(); };

  function getEls() {
    return {
      openBtn: document.getElementById('faceCameraOpenBtn'),
      modal: document.getElementById('faceCameraModal'),
      video: document.getElementById('faceCameraVideo'),
      shootBtn: document.getElementById('faceCameraShootBtn'),
      cancelBtn: document.getElementById('faceCameraCancelBtn'),
      closeBtn: document.getElementById('faceCameraCloseBtn'),
      switchBtn: document.getElementById('faceCameraSwitchBtn'),
      preview: document.getElementById('facePhotoPreview'),
    };
  }

  async function startStream() {
    const { video } = getEls();
    stopStream();
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode, width: { ideal: 1280 }, height: { ideal: 1024 } },
        audio: false,
      });
      video.srcObject = stream;
    } catch (e) {
      alert('카메라 접근이 거부되거나 사용 불가합니다.\n브라우저 권한을 확인하거나 다른 기기에서 시도해주세요.\n\n오류: ' + (e.message || e));
      closeModal();
    }
  }

  function stopStream() {
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      stream = null;
    }
  }

  async function openModal() {
    const { modal } = getEls();
    modal.style.display = 'flex';
    await startStream();
  }

  function closeModal() {
    const { modal } = getEls();
    stopStream();
    modal.style.display = 'none';
  }

  async function switchCamera() {
    facingMode = (facingMode === 'user') ? 'environment' : 'user';
    await startStream();
  }

  function capture() {
    const { video } = getEls();
    if (!video.videoWidth) {
      alert('카메라 영상이 준비되지 않았어요. 잠시 후 다시 시도해주세요.');
      return;
    }
    const canvas = document.createElement('canvas');
    // 1024px 권장 (face API 권장 크기)
    const maxDim = 1024;
    const scale = Math.min(1, maxDim / Math.max(video.videoWidth, video.videoHeight));
    canvas.width = Math.round(video.videoWidth * scale);
    canvas.height = Math.round(video.videoHeight * scale);
    const ctx = canvas.getContext('2d');
    // 전면 카메라면 좌우 반전 (사용자 시야 일치)
    if (facingMode === 'user') {
      ctx.translate(canvas.width, 0);
      ctx.scale(-1, 1);
    }
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    capturedBase64 = canvas.toDataURL('image/jpeg', 0.85);
    updatePreview();
    closeModal();
  }

  function updatePreview() {
    const { preview } = getEls();
    if (!preview) return;
    if (!capturedBase64) {
      preview.innerHTML = '';
      preview.classList.remove('has-photo');
      return;
    }
    preview.innerHTML = `
      <img src="${capturedBase64}" alt="찍은 사진">
      <button type="button" class="face-photo-clear" aria-label="다시 찍기">✕ 다시</button>
    `;
    preview.classList.add('has-photo');
    preview.querySelector('.face-photo-clear').addEventListener('click', () => {
      capturedBase64 = null;
      updatePreview();
    });
  }

  function init() {
    const els = getEls();
    if (!els.openBtn || !els.modal) return; // DOM 없으면 skip
    els.openBtn.addEventListener('click', openModal);
    els.shootBtn?.addEventListener('click', capture);
    els.cancelBtn?.addEventListener('click', closeModal);
    els.closeBtn?.addEventListener('click', closeModal);
    els.switchBtn?.addEventListener('click', switchCamera);
    // ESC 닫기
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && els.modal.style.display === 'flex') closeModal();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
