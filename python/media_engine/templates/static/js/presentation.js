/**
 * HTML Presentation Template - Interactive Presentation Controller
 */

(function() {
    'use strict';

    class Presentation {
        constructor() {
            this.slides = document.querySelectorAll('.slide');
            this.currentIndex = 0;
            this.totalSlides = this.slides.length;

            // Elements
            this.progressBar = document.getElementById('progress-bar');
            this.currentSlideEl = document.getElementById('current-slide');
            this.prevBtn = document.getElementById('prev-btn');
            this.nextBtn = document.getElementById('next-btn');
            this.speakerNotes = document.getElementById('speaker-notes');
            this.notesContent = document.getElementById('notes-content');
            this.helpOverlay = document.getElementById('help-overlay');
            this.themeToggle = document.getElementById('theme-toggle');
            this.fullscreenBtn = document.getElementById('fullscreen-btn');
            this.helpBtn = document.getElementById('help-btn');

            this.init();
        }

        init() {
            // Load saved state
            var savedTheme = localStorage.getItem('presentation-theme') || 'dark';
            document.documentElement.setAttribute('data-theme', savedTheme);

            // Check URL hash for slide number
            var hash = window.location.hash;
            if (hash && hash.startsWith('#slide-')) {
                var slideNum = parseInt(hash.replace('#slide-', ''));
                if (slideNum > 0 && slideNum <= this.totalSlides) {
                    this.currentIndex = slideNum - 1;
                }
            }

            this.bindEvents();
            this.goToSlide(this.currentIndex);
        }

        bindEvents() {
            var self = this;

            // Keyboard navigation
            document.addEventListener('keydown', function(e) {
                self.handleKeydown(e);
            });

            // Button clicks
            if (this.prevBtn) {
                this.prevBtn.addEventListener('click', function() {
                    self.prev();
                });
            }
            if (this.nextBtn) {
                this.nextBtn.addEventListener('click', function() {
                    self.next();
                });
            }
            if (this.themeToggle) {
                this.themeToggle.addEventListener('click', function() {
                    self.toggleTheme();
                });
            }
            if (this.fullscreenBtn) {
                this.fullscreenBtn.addEventListener('click', function() {
                    self.toggleFullscreen();
                });
            }
            if (this.helpBtn) {
                this.helpBtn.addEventListener('click', function() {
                    self.toggleHelp();
                });
            }

            // Touch/swipe support
            var touchStartX = 0;
            document.addEventListener('touchstart', function(e) {
                touchStartX = e.touches[0].clientX;
            });
            document.addEventListener('touchend', function(e) {
                var touchEndX = e.changedTouches[0].clientX;
                var diff = touchStartX - touchEndX;
                if (Math.abs(diff) > 50) {
                    if (diff > 0) {
                        self.next();
                    } else {
                        self.prev();
                    }
                }
            });

            // Hash change
            window.addEventListener('hashchange', function() {
                var hash = window.location.hash;
                if (hash && hash.startsWith('#slide-')) {
                    var slideNum = parseInt(hash.replace('#slide-', ''));
                    if (slideNum > 0 && slideNum <= self.totalSlides) {
                        self.goToSlide(slideNum - 1);
                    }
                }
            });
        }

        handleKeydown(e) {
            var self = this;

            // Don't handle if help overlay is visible (except Escape)
            if (this.helpOverlay && this.helpOverlay.classList.contains('visible') && e.key !== 'Escape') {
                if (e.key === 'Escape') {
                    this.toggleHelp();
                }
                return;
            }

            switch (e.key) {
                case 'ArrowRight':
                case ' ':
                case 'n':
                case 'N':
                    e.preventDefault();
                    this.next();
                    break;
                case 'ArrowLeft':
                case 'p':
                case 'P':
                    e.preventDefault();
                    this.prev();
                    break;
                case 'Home':
                    e.preventDefault();
                    this.goToSlide(0);
                    break;
                case 'End':
                    e.preventDefault();
                    this.goToSlide(this.totalSlides - 1);
                    break;
                case 'f':
                case 'F':
                    e.preventDefault();
                    this.toggleFullscreen();
                    break;
                case 's':
                case 'S':
                    e.preventDefault();
                    this.toggleNotes();
                    break;
                case 't':
                case 'T':
                    e.preventDefault();
                    this.toggleTheme();
                    break;
                case '?':
                    e.preventDefault();
                    this.toggleHelp();
                    break;
                case 'Escape':
                    if (this.helpOverlay && this.helpOverlay.classList.contains('visible')) {
                        this.toggleHelp();
                    } else if (document.fullscreenElement) {
                        document.exitFullscreen();
                    }
                    break;
            }
        }

        goToSlide(index) {
            if (index < 0 || index >= this.totalSlides) return;

            var self = this;

            // Update classes
            this.slides.forEach(function(slide, i) {
                slide.classList.remove('active', 'prev');
                if (i === index) {
                    slide.classList.add('active');
                } else if (i < index) {
                    slide.classList.add('prev');
                }
            });

            this.currentIndex = index;

            // Update UI
            this.updateProgress();
            this.updateNotes();
            this.updateButtons();
            this.updateHash();
        }

        next() {
            if (this.currentIndex < this.totalSlides - 1) {
                this.goToSlide(this.currentIndex + 1);
            }
        }

        prev() {
            if (this.currentIndex > 0) {
                this.goToSlide(this.currentIndex - 1);
            }
        }

        updateProgress() {
            if (this.progressBar) {
                var progress = ((this.currentIndex + 1) / this.totalSlides) * 100;
                this.progressBar.style.width = progress + '%';
            }
            if (this.currentSlideEl) {
                this.currentSlideEl.textContent = this.currentIndex + 1;
            }
        }

        updateNotes() {
            if (this.notesContent) {
                var currentSlide = this.slides[this.currentIndex];
                var notes = currentSlide.dataset.notes || '';
                this.notesContent.textContent = notes || 'No notes for this slide.';
            }
        }

        updateButtons() {
            if (this.prevBtn) {
                this.prevBtn.disabled = this.currentIndex === 0;
            }
            if (this.nextBtn) {
                this.nextBtn.disabled = this.currentIndex === this.totalSlides - 1;
            }
        }

        updateHash() {
            history.replaceState(null, null, '#slide-' + (this.currentIndex + 1));
        }

        toggleTheme() {
            var current = document.documentElement.getAttribute('data-theme');
            var next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('presentation-theme', next);
        }

        toggleFullscreen() {
            var elem = document.getElementById('presentation');
            if (!document.fullscreenElement) {
                elem.requestFullscreen().catch(function(err) {
                    console.log('Fullscreen error:', err);
                });
            } else {
                document.exitFullscreen();
            }
        }

        toggleNotes() {
            if (this.speakerNotes) {
                this.speakerNotes.classList.toggle('visible');
            }
        }

        toggleHelp() {
            if (this.helpOverlay) {
                this.helpOverlay.classList.toggle('visible');
            }
        }
    }

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        new Presentation();
    });

})();
