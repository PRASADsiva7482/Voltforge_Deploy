/**
 * Voltforge Keycloak Theme - v-app.js
 * Professional enterprise authentication enhancements:
 * - Dynamic high-res Voltforge SVG & ICO Favicon injection across all web flows
 * - Clean SVG password visibility toggles
 * - Safe enterprise text rebranding (Voltforge)
 * - Accessible focus handling and smooth interactions
 * - Polished "Already have an account? Log in" switcher
 */

// =========================================================================
// 1. Instant Voltforge Favicon Injection (Runs Immediately in Head)
// =========================================================================
(function applyVoltforgeFavicon() {
    const svgData = `<svg viewBox="0 0 48 48" width="64" height="64" fill="none" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="topNarayanaGrad" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#FFD700"/><stop offset="30%" stop-color="#FF9933"/><stop offset="70%" stop-color="#1DA1F2"/><stop offset="100%" stop-color="#0A4D8C"/></linearGradient><linearGradient id="topShivaGrad" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.9"/><stop offset="50%" stop-color="#E0E0E0" stop-opacity="0.8"/><stop offset="100%" stop-color="#CCCCCC" stop-opacity="0.7"/></linearGradient><filter id="topGlow"><feGaussianBlur stdDeviation="0.8" result="coloredBlur"/><feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><g filter="url(#topGlow)"><path d="M10 8 L24 40 L38 8" stroke="url(#topNarayanaGrad)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" fill="none"/><path d="M13 11 L24 36 L35 11" stroke="rgba(255,255,255,0.4)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/></g><g opacity="0.85"><line x1="14" y1="14" x2="34" y2="14" stroke="url(#topShivaGrad)" stroke-width="2.2" stroke-linecap="round"/><line x1="16" y1="20" x2="32" y2="20" stroke="url(#topShivaGrad)" stroke-width="2.2" stroke-linecap="round"/><line x1="18" y1="26" x2="30" y2="26" stroke="url(#topShivaGrad)" stroke-width="2.2" stroke-linecap="round"/></g><circle cx="24" cy="5" r="2.5" fill="#FFD700" opacity="0.9" filter="url(#topGlow)"/><circle cx="20" cy="30" r="0.8" fill="rgba(255,255,255,0.5)"/><circle cx="28" cy="30" r="0.8" fill="rgba(255,255,255,0.5)"/></svg>`;

    const faviconUrl = 'data:image/svg+xml,' + encodeURIComponent(svgData);

    function updateIcons() {
        const existingIcons = document.querySelectorAll("link[rel*='icon']");
        existingIcons.forEach(el => el.remove());

        const svgLink = document.createElement('link');
        svgLink.rel = 'icon';
        svgLink.type = 'image/svg+xml';
        svgLink.href = faviconUrl;
        document.head.appendChild(svgLink);

        const shortcutLink = document.createElement('link');
        shortcutLink.rel = 'shortcut icon';
        shortcutLink.type = 'image/svg+xml';
        shortcutLink.href = faviconUrl;
        document.head.appendChild(shortcutLink);
    }

    if (document.head) {
        updateIcons();
    } else {
        document.addEventListener("DOMContentLoaded", updateIcons);
    }
})();

document.addEventListener("DOMContentLoaded", function () {

    // =========================================================================
    // 2. Voltforge Enterprise Rebranding
    // =========================================================================
    function rebrand() {
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        while (walker.nextNode()) {
            const node = walker.currentNode;
            if (node.parentElement && (
                node.parentElement.tagName === 'INPUT' ||
                node.parentElement.tagName === 'TEXTAREA' ||
                node.parentElement.tagName === 'SCRIPT' ||
                node.parentElement.tagName === 'STYLE'
            )) {
                continue;
            }
            if (node.nodeValue && /keycloak|v-app/i.test(node.nodeValue)) {
                node.nodeValue = node.nodeValue
                    .replace(/Keycloak\s+Account\s+Management/gi, 'Voltforge Account Management')
                    .replace(/Keycloak\s+Administration\s+Console/gi, 'Voltforge Administration Console')
                    .replace(/V-App\s+Account\s+Management/gi, 'Voltforge Account Management')
                    .replace(/V-App\s+Administration\s+Console/gi, 'Voltforge Administration Console')
                    .replace(/Keycloak/gi, 'Voltforge')
                    .replace(/\bV-App\b/g, 'Voltforge');
            }
        }

        if (document.title && /keycloak|v-app/i.test(document.title)) {
            document.title = document.title
                .replace(/Keycloak/gi, 'Voltforge')
                .replace(/V-App/gi, 'Voltforge');
        }
    }

    rebrand();

    // =========================================================================
    // 3. High-Performance Password Visibility Toggles
    // =========================================================================
    function setupPasswordToggles() {
        const passwordInputs = document.querySelectorAll('input[type="password"]');

        passwordInputs.forEach(function (input) {
            const parent = input.parentElement;
            if (!parent) return;

            if (parent.querySelector('.v-pwd-toggle')) return;

            if (getComputedStyle(parent).position === 'static') {
                parent.style.position = 'relative';
            }

            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'v-pwd-toggle';
            btn.setAttribute('aria-label', 'Toggle password visibility');
            btn.setAttribute('tabindex', '-1');

            const eyeIcon = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>';
            const eyeSlashIcon = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>';

            btn.innerHTML = eyeIcon;

            btn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                if (input.type === 'password') {
                    input.type = 'text';
                    btn.innerHTML = eyeSlashIcon;
                    btn.classList.add('active');
                } else {
                    input.type = 'password';
                    btn.innerHTML = eyeIcon;
                    btn.classList.remove('active');
                }
            });

            parent.appendChild(btn);
            input.style.paddingRight = '42px';
        });

        const pfButtons = document.querySelectorAll('.pf-c-button.pf-m-control');
        pfButtons.forEach(function (btn) {
            btn.style.display = 'none';
        });
    }

    setupPasswordToggles();

    // =========================================================================
    // 4. Enterprise Back-to-Login Polish
    // =========================================================================
    function polishBackToLogin() {
        const backLinks = document.querySelectorAll('#kc-form-options a');
        backLinks.forEach(function (link) {
            if (/back\s+to\s+login/i.test(link.textContent)) {
                link.innerHTML = 'Already have an account? <span style="color:#06b6d4;font-weight:600;margin-left:4px;">Log in</span>';
            }
        });
    }

    polishBackToLogin();

    // =========================================================================
    // 5. Subtle Legal Terms on Registration
    // =========================================================================
    function addTermsNotice() {
        const regForm = document.getElementById('kc-register-form');
        if (!regForm || regForm.querySelector('.vf-terms-notice')) return;

        const termsNotice = document.createElement('div');
        termsNotice.className = 'vf-terms-notice';
        termsNotice.innerHTML = 'By creating an account, you agree to Voltforge\'s <a href="#" onclick="return false;">Terms of Service</a> &amp; <a href="#" onclick="return false;">Privacy Policy</a>.';

        const submitGroup = regForm.querySelector('.form-group:has(#kc-register), .form-group:has(#kc-form-buttons)');
        if (submitGroup) {
            regForm.insertBefore(termsNotice, submitGroup);
        } else {
            regForm.appendChild(termsNotice);
        }
    }

    addTermsNotice();

    // =========================================================================
    // 6. Enterprise Footer Injection
    // =========================================================================
    function addFooter() {
        if (document.querySelector('.v-app-footer')) return;

        const footer = document.createElement('div');
        footer.className = 'v-app-footer';
        footer.innerHTML = '&copy; ' + new Date().getFullYear() + ' <span class="v-highlight">Voltforge Inc.</span> &bull; Enterprise Identity System';

        const card = document.querySelector('.card-pf');
        if (card && card.parentNode) {
            card.parentNode.insertBefore(footer, card.nextSibling);
        }
    }

    addFooter();

    // =========================================================================
    // 7. Dynamic Mutation Observer
    // =========================================================================
    const observer = new MutationObserver(function (mutations) {
        let hasNewNodes = false;
        mutations.forEach(function (m) {
            if (m.addedNodes.length) hasNewNodes = true;
        });
        if (hasNewNodes) {
            setupPasswordToggles();
            rebrand();
            polishBackToLogin();
            addTermsNotice();
            addFooter();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
});
