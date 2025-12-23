/**
 * HTML Document Template - Interactive Features
 */

(function() {
    'use strict';

    // Configuration (can be overridden via data attributes)
    const config = {
        defaultTheme: document.documentElement.dataset.theme || 'dark',
        includeProgress: document.getElementById('progress') !== null,
        includeBackToTop: document.getElementById('back-to-top') !== null
    };

    // ========================================
    // Theme Toggle
    // ========================================
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const themeText = document.getElementById('theme-text');

    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        if (themeIcon && themeText) {
            if (theme === 'light') {
                themeIcon.textContent = '\u{1F319}'; // Moon emoji
                themeText.textContent = 'Dark';
            } else {
                themeIcon.textContent = '\u{2600}\u{FE0F}'; // Sun emoji
                themeText.textContent = 'Light';
            }
        }
    }

    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || config.defaultTheme;
    setTheme(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const current = document.documentElement.getAttribute('data-theme');
            setTheme(current === 'light' ? 'dark' : 'light');
        });
    }

    // ========================================
    // Reading Progress Bar
    // ========================================
    if (config.includeProgress) {
        const progressBar = document.getElementById('progress');

        function updateProgress() {
            const scrollTop = window.scrollY;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
            progressBar.style.width = progress + '%';
        }

        window.addEventListener('scroll', updateProgress);
        updateProgress(); // Initial call
    }

    // ========================================
    // Back to Top Button
    // ========================================
    if (config.includeBackToTop) {
        const backToTop = document.getElementById('back-to-top');

        function updateBackToTopVisibility() {
            if (window.scrollY > 300) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        }

        window.addEventListener('scroll', updateBackToTopVisibility);

        backToTop.addEventListener('click', function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });

        updateBackToTopVisibility(); // Initial call
    }

    // ========================================
    // Active TOC Highlighting
    // ========================================
    const tocItems = document.querySelectorAll('.toc-item');

    if (tocItems.length > 0) {
        const observerOptions = {
            rootMargin: '-80px 0px -70% 0px'
        };

        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    tocItems.forEach(function(item) {
                        item.classList.remove('active');
                    });
                    const id = entry.target.id;
                    const tocItem = document.querySelector('.toc-item[data-chapter="' + id + '"]');
                    if (tocItem) {
                        tocItem.classList.add('active');
                    }
                }
            });
        }, observerOptions);

        document.querySelectorAll('.chapter, h2[id]').forEach(function(section) {
            observer.observe(section);
        });
    }

    // ========================================
    // Mobile Sidebar Toggle (optional)
    // ========================================
    const sidebar = document.getElementById('sidebar');
    const menuToggle = document.getElementById('menu-toggle');

    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });

        // Close sidebar when clicking outside
        document.addEventListener('click', function(e) {
            if (sidebar.classList.contains('open') &&
                !sidebar.contains(e.target) &&
                !menuToggle.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        });
    }

})();
