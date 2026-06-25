(() => {
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
        window.lucide.createIcons();
    }

    let menuOpen = false;
    function syncMenuState() {
        const overlay = document.getElementById('mobile-overlay');
        const drawer = document.getElementById('mobile-drawer');
        const iconOpen = document.getElementById('menu-icon-open');
        const iconClose = document.getElementById('menu-icon-close');

        if (!overlay || !drawer || !iconOpen || !iconClose) return;

        overlay.classList.toggle('opacity-100', menuOpen);
        overlay.classList.toggle('pointer-events-auto', menuOpen);
        overlay.classList.toggle('opacity-0', !menuOpen);
        overlay.classList.toggle('pointer-events-none', !menuOpen);

        drawer.classList.toggle('translate-x-0', menuOpen);
        drawer.classList.toggle('translate-x-full', !menuOpen);

        iconOpen.classList.toggle('opacity-0', menuOpen);
        iconOpen.classList.toggle('scale-50', menuOpen);
        iconOpen.classList.toggle('rotate-90', menuOpen);
        iconOpen.classList.toggle('opacity-100', !menuOpen);
        iconOpen.classList.toggle('scale-100', !menuOpen);

        iconClose.classList.toggle('opacity-100', menuOpen);
        iconClose.classList.toggle('scale-100', menuOpen);
        iconClose.classList.toggle('opacity-0', !menuOpen);
        iconClose.classList.toggle('scale-50', !menuOpen);
        iconClose.classList.toggle('rotate-90', !menuOpen);

        document.body.style.overflow = menuOpen ? 'hidden' : '';
    }

    window.toggleMenu = function toggleMenu(force) {
        menuOpen = typeof force === 'boolean' ? force : !menuOpen;
        syncMenuState();
    };

    function updateActiveNavLink() {
        const sections = Array.from(document.querySelectorAll('.landing-section[id]'));
        const links = Array.from(document.querySelectorAll('.landing-nav-link[href^="#"]'));
        if (!sections.length || !links.length) return;

        const header = document.querySelector('header');
        const threshold = window.scrollY + (header ? header.offsetHeight : 96) + 24;
        let currentId = sections[0].id;

        sections.forEach((section) => {
            if (section.offsetTop <= threshold) {
                currentId = section.id;
            }
        });

        links.forEach((link) => {
            const isActive = link.getAttribute('href') === `#${currentId}`;
            link.classList.toggle('landing-nav-link-active', isActive);
            link.classList.toggle('text-[#0c7a43]', isActive);
            link.classList.toggle('font-bold', isActive);
        });
    }

    function initSmoothScroll() {
        document.addEventListener('click', (e) => {
            const link = e.target instanceof Element ? e.target.closest('a[href^="#"]') : null;
            if (!link) return;

            const href = link.getAttribute('href');
            if (!href || href === '#') return;

            const target = document.querySelector(href);
            if (!target) return;

            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });

            if (window.location.hash !== href) {
                window.history.replaceState(null, '', href);
            }
        });
    }

    function initMobileCloseOnNav() {
        document.addEventListener('click', (e) => {
            const closeTrigger = e.target instanceof Element ? e.target.closest('[data-close-menu="true"]') : null;
            if (!closeTrigger || !menuOpen) return;
            window.toggleMenu(false);
        });
    }

    function initEscapeToClose() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && menuOpen) {
                window.toggleMenu(false);
            }
        });
    }

    function initScrollSpy() {
        updateActiveNavLink();
        window.addEventListener('scroll', updateActiveNavLink, { passive: true });
        window.addEventListener('resize', updateActiveNavLink);
    }

    function initHashOnLoad() {
        if (!window.location.hash) return;
        const target = document.querySelector(window.location.hash);
        if (!target) return;

        window.requestAnimationFrame(() => {
            target.scrollIntoView({ behavior: 'auto', block: 'start' });
            updateActiveNavLink();
        });
    }

    function initBoomerangVideo() {
        const video = document.getElementById('boomerang-video');
        const canvas = document.getElementById('boomerang-canvas');
        if (!video || !canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const maxWidth = 1200;
        const frames = [];
        let capturing = true;
        let lastTime = -1;
        let rafId = 0;

        function captureFrame() {
            if (!capturing || video.readyState < 2) return;
            if (video.currentTime === lastTime) return;
            lastTime = video.currentTime;

            const vw = video.videoWidth;
            const vh = video.videoHeight;
            if (!vw || !vh) return;

            const scale = Math.min(1, maxWidth / vw);
            const width = Math.round(vw * scale);
            const height = Math.round(vh * scale);

            const bufferCanvas = document.createElement('canvas');
            bufferCanvas.width = width;
            bufferCanvas.height = height;

            const bufferCtx = bufferCanvas.getContext('2d');
            if (!bufferCtx) return;

            bufferCtx.drawImage(video, 0, 0, width, height);
            frames.push(bufferCanvas);
        }

        function captureLoop() {
            captureFrame();
            if (!capturing) return;

            if (typeof video.requestVideoFrameCallback === 'function') {
                video.requestVideoFrameCallback(captureLoop);
            } else {
                rafId = requestAnimationFrame(captureLoop);
            }
        }

        video.addEventListener('loadedmetadata', () => {
            video.play().catch(() => {});

            if (typeof video.requestVideoFrameCallback === 'function') {
                video.requestVideoFrameCallback(captureLoop);
            } else {
                rafId = requestAnimationFrame(captureLoop);
            }
        });

        video.addEventListener('ended', () => {
            capturing = false;
            cancelAnimationFrame(rafId);
            if (!frames.length) return;

            video.style.display = 'none';
            canvas.classList.remove('hidden');
            canvas.width = frames[0].width;
            canvas.height = frames[0].height;

            let index = 0;
            let direction = 1;
            let lastRender = performance.now();
            const interval = 1000 / 30;

            function renderLoop(now) {
                if (now - lastRender >= interval) {
                    lastRender = now;
                    ctx.drawImage(frames[index], 0, 0);
                    index += direction;

                    if (index >= frames.length - 1) {
                        index = frames.length - 1;
                        direction = -1;
                    } else if (index <= 0) {
                        index = 0;
                        direction = 1;
                    }
                }

                requestAnimationFrame(renderLoop);
            }

            requestAnimationFrame(renderLoop);
        });
    }

    function initWompiDonationForm() {
        const form = document.getElementById('wompi-donation-form');
        if (!form) return;

        const amountInput = document.getElementById('wompi-donation-amount');
        const amountInCentsInput = document.getElementById('wompi-amount-in-cents');
        const referenceInput = document.getElementById('wompi-reference');
        const signatureInput = document.getElementById('wompi-signature-integrity');
        const submitButton = document.getElementById('wompi-donation-submit');
        const csrfForm = document.getElementById('wompi-csrf-form');
        const csrfTokenInput = csrfForm ? csrfForm.querySelector('input[name="csrfmiddlewaretoken"]') : null;

        if (!amountInput || !amountInCentsInput || !referenceInput || !signatureInput) return;

        let bypassHandler = false;

        form.addEventListener('submit', async (e) => {
            if (bypassHandler) return;
            e.preventDefault();

            const pesos = Number.parseInt(String(amountInput.value || '').trim(), 10);
            if (!Number.isFinite(pesos) || pesos <= 0) {
                window.alert('Ingresa un monto válido para donar.');
                return;
            }

            const amountInCents = pesos * 100;
            amountInCentsInput.value = String(amountInCents);

            const originalLabel = submitButton ? submitButton.textContent : '';
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = 'Procesando...';
            }

            try {
                const csrfTokenRaw = csrfTokenInput ? String(csrfTokenInput.value || '').trim() : '';
                const csrfToken = csrfTokenRaw && csrfTokenRaw !== 'NOTPROVIDED' ? csrfTokenRaw : '';

                const headers = { 'Content-Type': 'application/json' };
                if (csrfToken) {
                    headers['X-CSRFToken'] = csrfToken;
                }

                const response = await window.fetch('/api/wompi/generar-firma/', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers,
                    body: JSON.stringify({ amount_in_cents: amountInCents }),
                });

                const data = await response.json().catch(() => ({}));
                if (!response.ok) {
                    throw new Error(String(data.error || 'No fue posible generar la firma de integridad.'));
                }

                referenceInput.value = String(data.reference || '').trim();
                signatureInput.value = String(data.signature || '').trim();
                if (!referenceInput.value || !signatureInput.value) {
                    throw new Error('Respuesta inválida del servidor al generar la firma.');
                }

                bypassHandler = true;
                form.submit();
            } catch (err) {
                const msg = err instanceof Error ? err.message : 'Error generando la firma de integridad.';
                window.alert(msg);
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.textContent = originalLabel;
                }
            }
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        syncMenuState();
        initSmoothScroll();
        initMobileCloseOnNav();
        initEscapeToClose();
        initScrollSpy();
        initHashOnLoad();
        initBoomerangVideo();
        initWompiDonationForm();
    });
})();
