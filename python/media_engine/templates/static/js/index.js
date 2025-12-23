/**
 * HTML Index Templates - Interactive Features
 */

(function() {
    'use strict';

    // ========================================
    // Theme Toggle
    // ========================================
    var toggle = document.getElementById('theme-toggle');

    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        if (toggle) {
            toggle.textContent = theme === 'light' ? '\u{1F319} Dark' : '\u{2600}\u{FE0F} Light';
        }
    }

    var saved = localStorage.getItem('theme') || 'dark';
    setTheme(saved);

    if (toggle) {
        toggle.addEventListener('click', function() {
            var current = document.documentElement.getAttribute('data-theme');
            setTheme(current === 'light' ? 'dark' : 'light');
        });
    }

    // ========================================
    // Video Player Modal
    // ========================================
    var videoModal = document.getElementById('video-modal');
    var videoPlayer = document.getElementById('video-player');
    var videoTitle = document.getElementById('video-title');
    var videoDownload = document.getElementById('video-download');
    var videoClose = document.getElementById('video-close');

    // Open video modal
    document.querySelectorAll('[data-video]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            if (!videoModal || !videoPlayer) return;

            var videoPath = btn.dataset.video;
            var title = btn.dataset.title;

            var source = videoPlayer.querySelector('source');
            if (source) {
                source.src = videoPath;
            }
            videoPlayer.load();

            if (videoTitle) {
                videoTitle.textContent = title;
            }
            if (videoDownload) {
                videoDownload.href = videoPath;
            }

            videoModal.classList.add('active');
            videoPlayer.play();
        });
    });

    // Close video modal
    function closeVideoModal() {
        if (!videoModal || !videoPlayer) return;

        videoModal.classList.remove('active');
        videoPlayer.pause();
        videoPlayer.currentTime = 0;
    }

    if (videoClose) {
        videoClose.addEventListener('click', closeVideoModal);
    }

    if (videoModal) {
        videoModal.addEventListener('click', function(e) {
            if (e.target === videoModal) {
                closeVideoModal();
            }
        });
    }

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && videoModal && videoModal.classList.contains('active')) {
            closeVideoModal();
        }
    });

})();
