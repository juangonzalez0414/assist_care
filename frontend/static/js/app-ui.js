(function () {
    if (window.__axiusGlobalUiInit) return;
    window.__axiusGlobalUiInit = true;

    const ASYNC_DELAY_MS = 180;
    const ROUTE_FALLBACK_MS = 2200;

    let asyncPending = 0;
    let asyncTimer = null;
    let routeTimer = null;
    let loader = null;
    let panelText = null;
    let dropdownObserver = null;
    const DROPDOWN_CLOSE_MS = 200;
    const dropdownState = new WeakMap();
    let drawerObserver = null;
    const DRAWER_CLOSE_MS = 280;
    const drawerState = new WeakMap();
    const __axDbg = () => {
        return;
    };

    function ensureLoader() {
        if (loader) return loader;

        loader = document.createElement('div');
        loader.id = 'ax-global-loader';
        loader.className = 'ax-global-loader';
        loader.setAttribute('aria-live', 'polite');
        loader.setAttribute('aria-hidden', 'true');
        loader.innerHTML = [
            '<div class="ax-global-loader__backdrop"></div>',
            '<div class="ax-global-loader__panel" role="status" aria-label="Cargando contenido">',
            '  <div class="ax-global-loader__content">',
            '    <div class="ax-global-loader__spinner" aria-hidden="true"></div>',
            '    <div>',
            '      <div class="ax-global-loader__title">Cargando...</div>',
            '      <div class="ax-global-loader__text">Estamos preparando la siguiente vista.</div>',
            '    </div>',
            '  </div>',
            '</div>',
        ].join('');

        panelText = loader.querySelector('.ax-global-loader__text');
        document.body.appendChild(loader);
        return loader;
    }

    function bodyReady() {
        document.body.classList.add('ax-ui-ready');
    }

    function showRouteLoader(message) {
        ensureLoader();
        clearTimeout(routeTimer);
        loader.classList.add('is-route-loading');
        loader.setAttribute('aria-hidden', 'false');
        document.body.classList.add('ax-route-loading');
        if (panelText) panelText.textContent = message || 'Estamos preparando la siguiente vista.';
        // #region debug-point A:route-loader-show
        __axDbg('A','app-ui.js:showRouteLoader','route loader visible',{message:message||'',bodyClass:Array.from(document.body.classList),loaderClass:loader?Array.from(loader.classList):[]});
        // #endregion

        routeTimer = window.setTimeout(() => {
            hideRouteLoader();
        }, ROUTE_FALLBACK_MS);
    }

    function hideRouteLoader() {
        if (!loader) return;
        clearTimeout(routeTimer);
        loader.classList.remove('is-route-loading');
        loader.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('ax-route-loading');
        // #region debug-point A:route-loader-hide
        __axDbg('A','app-ui.js:hideRouteLoader','route loader hidden',{bodyClass:Array.from(document.body.classList),loaderClass:loader?Array.from(loader.classList):[]});
        // #endregion
    }

    function renderAsyncState() {
        ensureLoader();
        clearTimeout(asyncTimer);
        loader.classList.remove('is-async-loading');
    }

    function startAsync() {
        asyncPending += 1;
        renderAsyncState();
    }

    function endAsync() {
        asyncPending = Math.max(0, asyncPending - 1);
        renderAsyncState();
    }

    function isModifiedClick(event) {
        return event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0;
    }

    function isHashOnlyLink(anchor) {
        const rawHref = anchor.getAttribute('href') || '';
        if (!rawHref || !rawHref.startsWith('#')) return false;
        return rawHref.length > 1;
    }

    function isInternalNavigation(anchor) {
        const href = anchor.getAttribute('href') || '';
        if (!href) return false;
        if (href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('javascript:')) return false;
        if (anchor.hasAttribute('download')) return false;
        if ((anchor.getAttribute('target') || '').toLowerCase() === '_blank') return false;

        try {
            const url = new URL(anchor.href, window.location.href);
            return url.origin === window.location.origin;
        } catch (_) {
            return false;
        }
    }

    function handleHashNavigation(anchor) {
        if (!isHashOnlyLink(anchor)) return false;
        const target = document.querySelector(anchor.getAttribute('href'));
        if (!target) return false;

        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        if (history && history.pushState) {
            history.pushState(null, '', anchor.getAttribute('href'));
        }
        return true;
    }

    function attachNavigationListeners() {
        document.addEventListener('click', (event) => {
            if (event.defaultPrevented) return;
            const anchor = event.target.closest('a');
            if (!anchor) return;
            if (anchor.dataset.noLoader === 'true') return;
            if (isModifiedClick(event)) return;

            if (handleHashNavigation(anchor)) {
                event.preventDefault();
                return;
            }

            if (!isInternalNavigation(anchor)) return;

            const message = anchor.dataset.loadingText || 'Estamos abriendo la siguiente pantalla.';
            showRouteLoader(message);
        });

        document.addEventListener('submit', (event) => {
            if (event.defaultPrevented) return;
            const form = event.target;
            if (!(form instanceof HTMLFormElement)) return;
            if (form.dataset.noLoader === 'true') return;

            const submitter = event.submitter;
            const message = (submitter && submitter.dataset.loadingText) || form.dataset.loadingText || 'Estamos procesando tu solicitud.';
            showRouteLoader(message);
        });
    }

    function looksLikeDropdown(element) {
        if (!(element instanceof HTMLElement)) return false;
        const id = (element.id || '').toLowerCase();
        const classNames = typeof element.className === 'string' ? element.className.toLowerCase() : '';
        return id.includes('dropdown') || classNames.includes('dropdown');
    }

    function getDropdownMeta(element) {
        let meta = dropdownState.get(element);
        if (!meta) {
            meta = {
                timer: null,
                suppressMutation: false,
                isClosing: false,
            };
            dropdownState.set(element, meta);
        }
        return meta;
    }

    function withSuppressedDropdownMutation(element, callback) {
        const meta = getDropdownMeta(element);
        meta.suppressMutation = true;
        try {
            callback();
        } finally {
            meta.suppressMutation = false;
        }
    }

    function showDropdown(element, immediate) {
        if (!(element instanceof HTMLElement)) return;
        const meta = getDropdownMeta(element);

        if (meta.timer) {
            clearTimeout(meta.timer);
            meta.timer = null;
        }

        meta.isClosing = false;
        element.classList.add('ax-ui-dropdown');
        element.classList.remove('ax-ui-dropdown-closing');
        withSuppressedDropdownMutation(element, () => {
            element.classList.remove('hidden');
        });
        element.setAttribute('aria-hidden', 'false');

        if (immediate) {
            element.classList.add('ax-ui-dropdown-visible');
            return;
        }

        element.classList.remove('ax-ui-dropdown-visible');
        window.requestAnimationFrame(() => {
            if (!meta.isClosing && !element.classList.contains('hidden')) {
                element.classList.add('ax-ui-dropdown-visible');
            }
        });
    }

    function hideDropdown(element) {
        if (!(element instanceof HTMLElement)) return;
        const meta = getDropdownMeta(element);

        if (meta.timer) {
            clearTimeout(meta.timer);
            meta.timer = null;
        }

        meta.isClosing = true;
        element.classList.add('ax-ui-dropdown');
        withSuppressedDropdownMutation(element, () => {
            element.classList.remove('hidden');
        });
        element.classList.remove('ax-ui-dropdown-visible');
        element.classList.add('ax-ui-dropdown-closing');
        element.setAttribute('aria-hidden', 'true');

        meta.timer = window.setTimeout(() => {
            meta.isClosing = false;
            withSuppressedDropdownMutation(element, () => {
                element.classList.add('hidden');
            });
            element.classList.remove('ax-ui-dropdown-closing');
            meta.timer = null;
        }, DROPDOWN_CLOSE_MS);
    }

    function syncDropdownState(element, immediate) {
        if (!(element instanceof HTMLElement)) return;
        element.classList.add('ax-ui-dropdown');

        if (element.classList.contains('hidden')) {
            element.classList.remove('ax-ui-dropdown-visible');
            element.classList.remove('ax-ui-dropdown-closing');
            element.setAttribute('aria-hidden', 'true');
            return;
        }

        showDropdown(element, immediate);
    }

    function registerDropdown(element, immediate) {
        if (!looksLikeDropdown(element)) return;
        syncDropdownState(element, immediate);
    }

    function scanDropdowns(root, immediate) {
        if (!root) return;
        if (looksLikeDropdown(root)) {
            registerDropdown(root, immediate);
        }
        if (!(root instanceof Element)) return;
        root.querySelectorAll('[id*="dropdown"], [class*="dropdown"]').forEach((element) => {
            registerDropdown(element, immediate);
        });
    }

    function observeDropdowns() {
        scanDropdowns(document.body, true);
        // #region debug-point E:dropdown-observer-disabled
        __axDbg('E','app-ui.js:observeDropdowns','dropdown observer disabled after freeze evidence',{path:window.location.pathname});
        // #endregion
    }

    function looksLikeOverlay(element) {
        if (!(element instanceof HTMLElement)) return false;
        const id = (element.id || '').toLowerCase();
        const classNames = typeof element.className === 'string' ? element.className.toLowerCase() : '';
        return id.includes('overlay') || classNames.includes('overlay');
    }

    function looksLikeDrawer(element) {
        if (!(element instanceof HTMLElement)) return false;
        const id = (element.id || '').toLowerCase();
        const classNames = typeof element.className === 'string' ? element.className.toLowerCase() : '';
        return id.includes('drawer') || classNames.includes('drawer');
    }

    function getDrawerMeta(element) {
        let meta = drawerState.get(element);
        if (!meta) {
            meta = {
                timer: null,
                suppressMutation: false,
                isClosing: false,
            };
            drawerState.set(element, meta);
        }
        return meta;
    }

    function withSuppressedDrawerMutation(element, callback) {
        const meta = getDrawerMeta(element);
        meta.suppressMutation = true;
        try {
            callback();
        } finally {
            meta.suppressMutation = false;
        }
    }

    function setupDrawerClasses(element) {
        if (!(element instanceof HTMLElement)) return;
        element.classList.add('ax-ui-drawer');
        element.classList.remove('ax-ui-drawer-visible', 'ax-ui-drawer-closing');
        if (!element.classList.contains('ax-ui-drawer-left') && !element.classList.contains('ax-ui-drawer-right')) {
            if (element.classList.contains('right-0')) {
                element.classList.add('ax-ui-drawer-right');
            } else {
                element.classList.add('ax-ui-drawer-left');
            }
        }
    }

    function setupOverlayClasses(element) {
        if (!(element instanceof HTMLElement)) return;
        element.classList.add('ax-ui-overlay');
        element.classList.remove('ax-ui-overlay-visible');
    }

    function showOverlay(element, immediate) {
        if (!(element instanceof HTMLElement)) return;
        const meta = getDrawerMeta(element);
        if (meta.timer) {
            clearTimeout(meta.timer);
            meta.timer = null;
        }
        meta.isClosing = false;
        setupOverlayClasses(element);
        withSuppressedDrawerMutation(element, () => {
            element.classList.remove('hidden');
        });
        element.setAttribute('aria-hidden', 'false');
        if (immediate) {
            element.classList.add('ax-ui-overlay-visible');
            // #region debug-point B:overlay-show-immediate
            __axDbg('B','app-ui.js:showOverlay','overlay visible immediate',{id:element.id||'',className:element.className,immediate:true});
            // #endregion
            return;
        }
        window.requestAnimationFrame(() => {
            if (!meta.isClosing && !element.classList.contains('hidden')) {
                element.classList.add('ax-ui-overlay-visible');
                // #region debug-point B:overlay-show
                __axDbg('B','app-ui.js:showOverlay','overlay visible',{id:element.id||'',className:element.className,immediate:false});
                // #endregion
            }
        });
    }

    function hideOverlay(element) {
        if (!(element instanceof HTMLElement)) return;
        const meta = getDrawerMeta(element);
        if (meta.timer) {
            clearTimeout(meta.timer);
            meta.timer = null;
        }
        meta.isClosing = true;
        setupOverlayClasses(element);
        withSuppressedDrawerMutation(element, () => {
            element.classList.remove('hidden');
        });
        element.classList.remove('ax-ui-overlay-visible');
        element.setAttribute('aria-hidden', 'true');
        // #region debug-point B:overlay-hide-start
        __axDbg('B','app-ui.js:hideOverlay','overlay closing start',{id:element.id||'',className:element.className});
        // #endregion
        meta.timer = window.setTimeout(() => {
            meta.isClosing = false;
            withSuppressedDrawerMutation(element, () => {
                element.classList.add('hidden');
            });
            meta.timer = null;
            // #region debug-point B:overlay-hide-end
            __axDbg('B','app-ui.js:hideOverlay','overlay hidden end',{id:element.id||'',className:element.className});
            // #endregion
        }, DRAWER_CLOSE_MS);
    }

    function showDrawer(element, immediate) {
        if (!(element instanceof HTMLElement)) return;
        const meta = getDrawerMeta(element);
        if (meta.timer) {
            clearTimeout(meta.timer);
            meta.timer = null;
        }
        meta.isClosing = false;
        setupDrawerClasses(element);
        withSuppressedDrawerMutation(element, () => {
            element.classList.remove('hidden');
        });
        element.setAttribute('aria-hidden', 'false');
        if (immediate) {
            element.classList.add('ax-ui-drawer-visible');
            // #region debug-point C:drawer-show-immediate
            __axDbg('C','app-ui.js:showDrawer','drawer visible immediate',{id:element.id||'',className:element.className,immediate:true});
            // #endregion
            return;
        }
        window.requestAnimationFrame(() => {
            if (!meta.isClosing && !element.classList.contains('hidden')) {
                element.classList.add('ax-ui-drawer-visible');
                // #region debug-point C:drawer-show
                __axDbg('C','app-ui.js:showDrawer','drawer visible',{id:element.id||'',className:element.className,immediate:false});
                // #endregion
            }
        });
    }

    function hideDrawer(element) {
        if (!(element instanceof HTMLElement)) return;
        const meta = getDrawerMeta(element);
        if (meta.timer) {
            clearTimeout(meta.timer);
            meta.timer = null;
        }
        meta.isClosing = true;
        setupDrawerClasses(element);
        withSuppressedDrawerMutation(element, () => {
            element.classList.remove('hidden');
        });
        element.classList.remove('ax-ui-drawer-visible');
        element.classList.add('ax-ui-drawer-closing');
        element.setAttribute('aria-hidden', 'true');
        // #region debug-point C:drawer-hide-start
        __axDbg('C','app-ui.js:hideDrawer','drawer closing start',{id:element.id||'',className:element.className});
        // #endregion
        meta.timer = window.setTimeout(() => {
            meta.isClosing = false;
            withSuppressedDrawerMutation(element, () => {
                element.classList.add('hidden');
            });
            element.classList.remove('ax-ui-drawer-closing');
            meta.timer = null;
            // #region debug-point C:drawer-hide-end
            __axDbg('C','app-ui.js:hideDrawer','drawer hidden end',{id:element.id||'',className:element.className});
            // #endregion
        }, DRAWER_CLOSE_MS);
    }

    function syncDrawerState(element, immediate) {
        if (!(element instanceof HTMLElement)) return;
        if (looksLikeOverlay(element)) {
            setupOverlayClasses(element);
            if (element.classList.contains('hidden')) {
                element.setAttribute('aria-hidden', 'true');
                return;
            }
            showOverlay(element, immediate);
            return;
        }

        setupDrawerClasses(element);
        if (element.classList.contains('hidden')) {
            element.setAttribute('aria-hidden', 'true');
            return;
        }
        showDrawer(element, immediate);
    }

    function registerDrawer(element, immediate) {
        if (!looksLikeDrawer(element) && !looksLikeOverlay(element)) return;
        const hasHiddenBehavior = element.classList.contains('hidden') || element.dataset.axAnimated === 'true';
        if (!hasHiddenBehavior) return;
        element.dataset.axAnimated = 'true';
        syncDrawerState(element, immediate);
    }

    function scanDrawers(root, immediate) {
        if (!root) return;
        if ((looksLikeDrawer(root) || looksLikeOverlay(root)) && root instanceof HTMLElement) {
            registerDrawer(root, immediate);
        }
        if (!(root instanceof Element)) return;
        root.querySelectorAll('[id*="drawer"], [class*="drawer"], [id*="overlay"], [class*="overlay"]').forEach((element) => {
            registerDrawer(element, immediate);
        });
    }

    function observeDrawers() {
        scanDrawers(document.body, true);
        // #region debug-point E:drawer-observer-disabled
        __axDbg('E','app-ui.js:observeDrawers','drawer observer disabled after freeze evidence',{path:window.location.pathname});
        // #endregion
    }

    function patchFetch() {
        if (typeof window.fetch !== 'function') return;
        const nativeFetch = window.fetch.bind(window);

        window.fetch = function () {
            startAsync();
            return nativeFetch.apply(window, arguments).finally(() => {
                endAsync();
            });
        };
    }

    function patchXHR() {
        if (typeof window.XMLHttpRequest !== 'function') return;

        const nativeSend = window.XMLHttpRequest.prototype.send;
        window.XMLHttpRequest.prototype.send = function () {
            startAsync();
            this.addEventListener('loadend', endAsync, { once: true });
            return nativeSend.apply(this, arguments);
        };
    }

    function attachLifecycleListeners() {
        window.addEventListener('pageshow', () => {
            hideRouteLoader();
            asyncPending = 0;
            renderAsyncState();
        });

        window.addEventListener('load', () => {
            window.setTimeout(hideRouteLoader, 120);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            bodyReady();
            ensureLoader();
            attachNavigationListeners();
            observeDropdowns();
            observeDrawers();
            // #region debug-point E:init
            __axDbg('E','app-ui.js:DOMContentLoaded','global ui initialized',{path:window.location.pathname});
            // #endregion
        });
    } else {
        bodyReady();
        ensureLoader();
        attachNavigationListeners();
        observeDropdowns();
        observeDrawers();
        // #region debug-point E:init-sync
        __axDbg('E','app-ui.js:init','global ui initialized sync',{path:window.location.pathname});
        // #endregion
    }

    patchFetch();
    patchXHR();
    attachLifecycleListeners();
})();
