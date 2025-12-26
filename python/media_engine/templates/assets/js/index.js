/**
 * Media Engine Deliverables - Index Page Scripts
 *
 * Features:
 * - Theme toggle (dark/light)
 * - Video player modal
 * - Keyboard navigation
 */

(function() {
    'use strict';

    // Theme Toggle
    const themeToggle = document.getElementById('theme-toggle');
    const html = document.documentElement;

    function getPreferredTheme() {
        const saved = localStorage.getItem('me-theme');
        if (saved) return saved;
        return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    }

    function setTheme(theme) {
        html.setAttribute('data-theme', theme);
        localStorage.setItem('me-theme', theme);
        updateThemeButton(theme);
    }

    function updateThemeButton(theme) {
        if (themeToggle) {
            themeToggle.textContent = theme === 'dark' ? '\u2600\uFE0F Light Mode' : '\uD83C\uDF19 Dark Mode';
        }
    }

    // Initialize theme
    setTheme(getPreferredTheme());

    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const current = html.getAttribute('data-theme');
            setTheme(current === 'dark' ? 'light' : 'dark');
        });
    }

    // Video Player Modal
    const videoModal = document.getElementById('video-modal');
    const videoPlayer = document.getElementById('video-player');
    const videoTitle = document.getElementById('video-title');
    const videoDownload = document.getElementById('video-download');
    const videoClose = document.getElementById('video-close');

    if (videoModal && videoPlayer) {
        // Open video on click
        document.querySelectorAll('[data-video]').forEach(function(btn) {
            btn.addEventListener('click', function() {
                const videoSrc = this.getAttribute('data-video');
                const title = this.getAttribute('data-title') || 'Video';

                videoPlayer.querySelector('source').src = videoSrc;
                videoPlayer.load();
                videoTitle.textContent = title;
                videoDownload.href = videoSrc;
                videoModal.classList.add('active');

                // Auto-play
                videoPlayer.play().catch(function() {
                    // Autoplay blocked, user will click play
                });
            });
        });

        // Close modal
        function closeVideoModal() {
            videoModal.classList.remove('active');
            videoPlayer.pause();
            videoPlayer.querySelector('source').src = '';
        }

        if (videoClose) {
            videoClose.addEventListener('click', closeVideoModal);
        }

        videoModal.addEventListener('click', function(e) {
            if (e.target === videoModal) {
                closeVideoModal();
            }
        });

        // Escape key to close
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && videoModal.classList.contains('active')) {
                closeVideoModal();
            }
        });
    }

    // Single language redirect
    // If there's only one language, redirect directly to it
    const languageCards = document.querySelectorAll('.language-card');
    if (languageCards.length === 1 && document.body.classList.contains('project-index')) {
        // Single language - redirect immediately
        window.location.href = languageCards[0].href;
    }

})();
