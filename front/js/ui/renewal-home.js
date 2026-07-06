/* ============================================================
   renewal-home.js — 四柱鏡·사주경 · 심야편 (2026-07)
   ============================================================
   히어로 인터랙션:
   - ON AIR 자동 점화 (β · 도착 3.2초 뒤 티틱)
   - Web Audio 프로그래매틱 사운드 (핑크 hiss + 티틱)
   - CTA → 기존 tab-bar 재사용 (결정론 엔진 손대지 않음)

   제거 (2026-07-06 · 사용자 명시 "정신 사나움"):
   - 하단 오실로스코프 파형
   - 간헐 지직 노이즈 burst / jitter
   ============================================================ */
(function () {
  'use strict';

  // ── 타이밍 상수 ─────────────────────────────────────────
  const IGNITE_DELAY  = 3200;      // 첫 티틱까지 대기
  const IGNITE_DUR    = 1100;      // 점화 애니 duration (CSS 매칭)

  const scene         = document.getElementById('heroScene');
  const onAirSign     = document.getElementById('onAirSign');
  const soundToggle   = document.getElementById('soundToggle');
  const anchorVideo   = document.getElementById('anchorPortraitVideo');
  const anchorCanvas  = document.getElementById('anchorPortraitCanvas');

  if (!scene) {
    console.warn('[사주경] hero scene 없음 — 이전 홈 렌더러 무시');
    exposeCompat();
    return;
  }

  const state = {
    ignited: false,
    audio: null,
    reduced: !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches),
  };

  // ============================================================
  // 0) 만월아씨 비디오 · 진짜 핑퐁 (정→역→정→역 …)
  // ============================================================
  //  전략: 브라우저 비디오 역재생 seek 은 신뢰 X → 정재생 첫 사이클에
  //        프레임을 offscreen canvas 에 캐시 → 역재생 시엔 캐시에서 그림.
  //
  //  Cycle:
  //   1) 최초 <video> 정재생 (rate 0.7) · requestVideoFrameCallback 로
  //      매 프레임 offscreen canvas 에 draw → ImageBitmap 배열에 push
  //   2) ended → video 숨김 / canvas 표시 → 캐시 배열 뒤에서 앞으로 draw
  //      실시간 rate 0.7 유지 (mediaTime 기반 스텝)
  //   3) 캐시 앞쪽 도달 → canvas 숨김 / video 표시 → video.currentTime=0 · play
  //   4) 두 번째 이후 ended → 캐시 이미 완성 → 즉시 canvas 역재생
  //
  //  Memory 예산: 5초 · 24fps 캡처 · 320×568 = 120 frames × ~730KB = ~85MB
  //   → 실제로는 브라우저가 GPU 텍스처로 관리해서 시스템 RAM 부담 낮음
  if (anchorVideo && anchorCanvas) {
    if (state.reduced) {
      anchorVideo.removeAttribute('autoplay');
      anchorVideo.pause();
    } else {
      const RATE = 0.7;
      const CAP_W = 320;
      const CAP_H = Math.round(CAP_W * 1916 / 1080); // 원본 비율 유지 = 568
      const CAP_INTERVAL_S = 1 / 24; // 24fps 캡처

      anchorCanvas.width  = CAP_W;
      anchorCanvas.height = CAP_H;
      const cctx = anchorCanvas.getContext('2d', { alpha: false, willReadFrequently: false });

      // 오프스크린 캡처 캔버스 (video → bitmap 변환용)
      const capCanvas = document.createElement('canvas');
      capCanvas.width  = CAP_W;
      capCanvas.height = CAP_H;
      const capCtx = capCanvas.getContext('2d', { alpha: false });

      const frames = []; // { t: mediaTime, bmp: ImageBitmap }[]
      let captured = false;
      let capturing = false;
      let inReverse = false;
      let reverseRAF = null;
      let lastCapTime = -1;

      const applyRate = () => { try { anchorVideo.playbackRate = RATE; } catch (_) {} };

      // 프레임 캡처 (requestVideoFrameCallback 기반)
      function startCapture() {
        if (captured || capturing) return;
        if (!('requestVideoFrameCallback' in anchorVideo)) {
          // 폴백 · setInterval 캡처
          const iv = setInterval(async () => {
            if (captured || anchorVideo.ended) { clearInterval(iv); return; }
            if (anchorVideo.currentTime - lastCapTime >= CAP_INTERVAL_S) {
              await pushFrame(anchorVideo.currentTime);
            }
          }, 1000 / 30);
          return;
        }
        capturing = true;
        const onFrame = async (_now, meta) => {
          if (captured) return;
          const t = meta.mediaTime;
          if (t - lastCapTime >= CAP_INTERVAL_S) {
            lastCapTime = t;
            await pushFrame(t);
          }
          if (!captured && !anchorVideo.ended) {
            anchorVideo.requestVideoFrameCallback(onFrame);
          }
        };
        anchorVideo.requestVideoFrameCallback(onFrame);
      }

      async function pushFrame(t) {
        try {
          capCtx.drawImage(anchorVideo, 0, 0, CAP_W, CAP_H);
          const bmp = await createImageBitmap(capCanvas);
          frames.push({ t, bmp });
        } catch (_) {}
      }

      // 역재생: 캐시 뒤→앞으로 · rate 0.7 유지
      function playReverse() {
        if (inReverse || frames.length < 2) return;
        inReverse = true;
        // 표시 전환
        anchorCanvas.style.opacity = '1';
        anchorVideo.style.opacity  = '0';
        try { anchorVideo.pause(); } catch (_) {}

        // 마지막 프레임 → 첫 프레임까지 실시간 mediaTime 기반 재생
        const totalDur = frames[frames.length - 1].t - frames[0].t; // 캡처된 총 mediaTime
        const startWall = performance.now();

        const step = (now) => {
          if (!inReverse) return;
          // 경과 실시간(ms) 을 mediaTime 으로 환산 (rate 0.7)
          const elapsedMedia = ((now - startWall) / 1000) * RATE;
          const targetMedia = Math.max(frames[0].t, frames[frames.length - 1].t - elapsedMedia);

          // 가장 가까운 프레임 찾기 (역방향 bisect)
          // frames는 t 오름차순 정렬 (mediaTime 오름차순)
          let lo = 0, hi = frames.length - 1;
          while (lo < hi) {
            const mid = (lo + hi) >> 1;
            if (frames[mid].t < targetMedia) lo = mid + 1;
            else hi = mid;
          }
          const idx = Math.max(0, Math.min(frames.length - 1, lo));
          cctx.drawImage(frames[idx].bmp, 0, 0, CAP_W, CAP_H);

          if (idx <= 0) {
            // 역재생 완료 → 정재생 재개
            inReverse = false;
            reverseRAF = null;
            resumeForward();
            return;
          }
          reverseRAF = requestAnimationFrame(step);
        };
        // 첫 프레임 즉시 draw (마지막 index)
        cctx.drawImage(frames[frames.length - 1].bmp, 0, 0, CAP_W, CAP_H);
        reverseRAF = requestAnimationFrame(step);
      }

      function resumeForward() {
        // canvas → video 전환
        try { anchorVideo.currentTime = 0; } catch (_) {}
        applyRate();
        const p = anchorVideo.play();
        if (p && p.catch) p.catch(() => {});
        // 페이드 없이 즉시 스왑 (같은 프레임에서 전환이라 시각 불연속 없음)
        anchorVideo.style.opacity = '1';
        anchorCanvas.style.opacity = '0';
      }

      anchorVideo.addEventListener('loadedmetadata', applyRate);
      anchorVideo.addEventListener('play', () => { if (!inReverse) applyRate(); });
      anchorVideo.addEventListener('playing', startCapture);
      anchorVideo.addEventListener('ended', () => {
        // 캡처 완료 마킹
        if (!captured && frames.length > 0) captured = true;
        capturing = false;
        if (frames.length >= 2) {
          playReverse();
        } else {
          // 캡처 실패 · 그냥 재시작
          try { anchorVideo.currentTime = 0; } catch (_) {}
          anchorVideo.play().catch(() => {});
        }
      });

      // 자동재생 정책 fallback
      const kickPlay = () => {
        anchorVideo.play().catch(() => {});
        document.removeEventListener('pointerdown', kickPlay);
        document.removeEventListener('keydown', kickPlay);
      };
      anchorVideo.play().catch(() => {
        document.addEventListener('pointerdown', kickPlay, { once: true });
        document.addEventListener('keydown', kickPlay, { once: true });
      });
      applyRate();

      document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
          if (reverseRAF) { cancelAnimationFrame(reverseRAF); reverseRAF = null; }
          inReverse = false;
        }
      });
    }
  }

  // ============================================================
  // 1) ON AIR 점화 시퀀스 (β · 도착 3.2초 뒤 자동)
  // ============================================================
  function ignite() {
    if (state.ignited) return;
    state.ignited = true;

    scene.classList.add('igniting');
    if (state.audio && state.audio.on) playTick();

    setTimeout(() => {
      scene.classList.remove('igniting');
      scene.classList.add('on-air');
    }, IGNITE_DUR);
  }

  // ============================================================
  // 4) Web Audio — 프로그래매틱 사운드 합성
  // ============================================================
  function ensureAudio() {
    if (state.audio) return state.audio;
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      const ctx = new AC();

      // 마스터 게인
      const master = ctx.createGain();
      master.gain.value = 0;
      master.connect(ctx.destination);

      // 핑크 노이즈 버퍼 (Paul Kellett 근사)
      const bufSize = 2 * ctx.sampleRate;
      const buf = ctx.createBuffer(1, bufSize, ctx.sampleRate);
      const data = buf.getChannelData(0);
      let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
      for (let i = 0; i < bufSize; i++) {
        const white = Math.random() * 2 - 1;
        b0 = 0.99886 * b0 + white * 0.0555179;
        b1 = 0.99332 * b1 + white * 0.0750759;
        b2 = 0.96900 * b2 + white * 0.1538520;
        b3 = 0.86650 * b3 + white * 0.3104856;
        b4 = 0.55000 * b4 + white * 0.5329522;
        b5 = -0.7616 * b5 - white * 0.0168980;
        data[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362) * 0.11;
        b6 = white * 0.115926;
      }

      // 상시 hiss (loop)
      const src = ctx.createBufferSource();
      src.buffer = buf;
      src.loop = true;

      // Low-pass로 warm 톤 (오래된 라디오)
      const lp = ctx.createBiquadFilter();
      lp.type = 'lowpass';
      lp.frequency.value = 2400;
      lp.Q.value = 0.7;

      const hissGain = ctx.createGain();
      hissGain.gain.value = 0.06;

      src.connect(lp).connect(hissGain).connect(master);
      src.start();

      state.audio = { ctx, master, hissGain, on: false };
      return state.audio;
    } catch (e) {
      console.warn('[사주경] AudioContext 실패:', e);
      return null;
    }
  }

  function playTick() {
    if (!state.audio) return;
    const { ctx, master } = state.audio;
    const now = ctx.currentTime;

    // 전기 클릭 (60ms, 짧은 지수 감쇠)
    const dur = 0.06;
    const size = Math.floor(ctx.sampleRate * dur);
    const buf = ctx.createBuffer(1, size, ctx.sampleRate);
    const data = buf.getChannelData(0);
    const decay = ctx.sampleRate * 0.008;
    for (let i = 0; i < size; i++) {
      const env = Math.exp(-i / decay);
      data[i] = (Math.random() * 2 - 1) * env;
    }

    const src = ctx.createBufferSource();
    src.buffer = buf;

    const hp = ctx.createBiquadFilter();
    hp.type = 'highpass';
    hp.frequency.value = 1400;

    const g = ctx.createGain();
    g.gain.value = 0.85;

    src.connect(hp).connect(g).connect(master);
    src.start(now);
  }

  function fadeMaster(from, to, dur) {
    if (!state.audio) return;
    const { ctx, master } = state.audio;
    const now = ctx.currentTime;
    master.gain.cancelScheduledValues(now);
    master.gain.setValueAtTime(from, now);
    master.gain.linearRampToValueAtTime(to, now + dur);
  }

  // ============================================================
  // 5) 사운드 토글
  // ============================================================
  if (soundToggle) {
    soundToggle.addEventListener('click', () => {
      const a = ensureAudio();
      if (!a) return;
      if (a.ctx.state === 'suspended') a.ctx.resume();

      if (a.on) {
        fadeMaster(a.master.gain.value, 0, 0.4);
        a.on = false;
        soundToggle.classList.remove('is-on');
        soundToggle.setAttribute('aria-pressed', 'false');
        soundToggle.setAttribute('aria-label', '방송 사운드 켜기');
      } else {
        fadeMaster(0, 1, 0.6);
        a.on = true;
        soundToggle.classList.add('is-on');
        soundToggle.setAttribute('aria-pressed', 'true');
        soundToggle.setAttribute('aria-label', '방송 사운드 끄기');
        playTick(); // 라디오 켜지는 팟
      }
    });

    // 사운드 아이콘 상태별 교체
    const svgMuted = soundToggle.innerHTML;
    const svgOn = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
        <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
        <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
      </svg>`;
    const updateIcon = () => {
      soundToggle.innerHTML = soundToggle.classList.contains('is-on') ? svgOn : svgMuted;
    };
    const mo = new MutationObserver(updateIcon);
    mo.observe(soundToggle, { attributes: true, attributeFilter: ['class'] });
  }

  // ============================================================
  // 6) CTA 라우팅 · 사주 입력 플로우 진입
  // ============================================================
  function enterInputFlow(tab) {
    // body 상태: gallery-mode/tab-home 제거, sk-input-flow 진입
    document.body.classList.remove(
      'gallery-mode', 'menu-mode', 'content-mode',
      'tab-home', 'tab-journal', 'tab-profile',
      'gallery-at-start'
    );
    document.body.classList.add('sk-input-flow', `sk-input-${tab}`);

    // 기존 tab 시스템 활용해 .tab-content 활성화
    const target = document.querySelector(`.tab-btn[data-tab="${tab}"]`);
    if (target) target.click();

    window.scrollTo({ top: 0, behavior: 'instant' });
  }

  function exitInputFlow() {
    document.body.classList.remove(
      'sk-input-flow',
      'sk-input-saju', 'sk-input-hwapae', 'sk-input-dream', 'sk-input-face'
    );
    document.body.classList.add('gallery-mode', 'tab-home');
    window.scrollTo({ top: 0, behavior: 'instant' });
  }

  scene.addEventListener('click', (e) => {
    const cta = e.target.closest('[data-tab]');
    if (!cta) return;
    if (!scene.classList.contains('on-air')) return;

    const tab = cta.dataset.tab;
    if (!tab) return;

    if (state.audio && state.audio.on) playTick();
    enterInputFlow(tab);
  });

  // 사주 입력 상단바 뒤로 버튼
  const backBtn = document.getElementById('skBackBtn');
  if (backBtn) {
    backBtn.addEventListener('click', exitInputFlow);
  }


  // ============================================================
  // 8) 시작 — β 시퀀스 예약
  // ============================================================
  function start() {
    if (state.reduced) {
      // 접근성: 애니 없이 즉시 ON AIR
      scene.classList.add('on-air');
      return;
    }
    setTimeout(ignite, IGNITE_DELAY);
  }

  // 호환 유지 (외부 코드가 여전히 참조 가능)
  function exposeCompat() {
    window.RenewalHome = {
      build: () => !!scene,
      routeToDomain(domain) {
        const t = document.querySelector(`.tab-btn[data-tab="${domain}"]`);
        if (t) { t.click(); return true; }
        return false;
      },
    };
    window.Sajukyung = { ignite };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { start(); exposeCompat(); });
  } else {
    start();
    exposeCompat();
  }
})();
