"""
HTML Presentation Templates

Generates beautiful, interactive HTML slide presentations with:
- Smooth animations and transitions
- Keyboard navigation (arrow keys, space, escape)
- Fullscreen mode (F key)
- Speaker notes view (S key)
- Progress indicator
- Touch/swipe support
- Print-friendly mode
- Full project branding
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from jinja2 import Template

if TYPE_CHECKING:
    from ..core.theme import Theme


@dataclass
class Slide:
    """A single slide in the presentation."""

    type: str  # title, content, section, quote, image, two_column
    title: str = ""
    subtitle: str = ""
    bullets: List[str] = field(default_factory=list)
    left_title: str = ""
    left_bullets: List[str] = field(default_factory=list)
    right_title: str = ""
    right_bullets: List[str] = field(default_factory=list)
    quote: str = ""
    author: str = ""
    image: str = ""
    caption: str = ""
    notes: str = ""


# Modern HTML Presentation Template
PRESENTATION_TEMPLATE = """<!DOCTYPE html>
<html lang="{{ lang }}" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    {% if fonts_css_path %}
    <link rel="stylesheet" href="{{ fonts_css_path }}">
    {% endif %}
    <style>
        /* ========================================
           CSS Variables from Theme
           ======================================== */
        :root {
            --bg-primary: {{ theme.dark.background }};
            --bg-secondary: {{ theme.dark.surface }};
            --bg-tertiary: {{ theme.dark.border }};
            --text-primary: {{ theme.dark.text }};
            --text-muted: {{ theme.dark.muted }};
            --accent-color: {{ theme.dark.accent }};
            --accent-secondary: {{ theme.colors.secondary }};
            --border-color: {{ theme.dark.border }};
            --font-heading: '{{ theme.typography.heading }}', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-body: '{{ theme.typography.body }}', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: '{{ theme.typography.code }}', 'SF Mono', Monaco, monospace;
        }

        [data-theme="light"] {
            --bg-primary: {{ theme.colors.background }};
            --bg-secondary: {{ theme.colors.surface }};
            --bg-tertiary: {{ theme.colors.border }};
            --text-primary: {{ theme.colors.text }};
            --text-muted: {{ theme.colors.muted }};
            --accent-color: {{ theme.colors.accent }};
            --border-color: {{ theme.colors.border }};
        }

        /* ========================================
           Base Styles
           ======================================== */
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        html, body {
            height: 100%;
            overflow: hidden;
            font-family: var(--font-body);
            background: var(--bg-primary);
            color: var(--text-primary);
        }

        /* ========================================
           Presentation Container
           ======================================== */
        .presentation {
            width: 100vw;
            height: 100vh;
            position: relative;
            overflow: hidden;
        }

        /* ========================================
           Slides
           ======================================== */
        .slides {
            width: 100%;
            height: 100%;
            position: relative;
        }

        .slide {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 60px 80px;
            opacity: 0;
            visibility: hidden;
            transform: translateX(100px);
            transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            background: var(--bg-primary);
        }

        .slide.active {
            opacity: 1;
            visibility: visible;
            transform: translateX(0);
            z-index: 10;
        }

        .slide.prev {
            transform: translateX(-100px);
        }

        /* ========================================
           Slide Content
           ======================================== */
        .slide-content {
            max-width: 1200px;
            width: 100%;
            text-align: left;
        }

        .slide-title {
            font-family: var(--font-heading);
            font-size: clamp(2rem, 5vw, 3.5rem);
            font-weight: 700;
            margin-bottom: 0.5em;
            letter-spacing: -0.02em;
            line-height: 1.1;
        }

        .slide-subtitle {
            font-size: clamp(1.25rem, 2.5vw, 1.75rem);
            color: var(--text-muted);
            margin-bottom: 1.5em;
            font-weight: 400;
        }

        .accent-bar {
            width: 80px;
            height: 4px;
            background: var(--accent-color);
            margin-bottom: 2em;
            border-radius: 2px;
        }

        /* ========================================
           Title Slide
           ======================================== */
        .slide--title {
            text-align: center;
        }

        .slide--title .slide-content {
            text-align: center;
        }

        .slide--title .slide-title {
            font-size: clamp(3rem, 8vw, 5rem);
            margin-bottom: 0.3em;
        }

        .slide--title .slide-subtitle {
            font-size: clamp(1.5rem, 3vw, 2rem);
            max-width: 800px;
            margin: 0 auto;
        }

        .slide--title .accent-bar {
            width: 120px;
            margin: 1.5em auto;
        }

        .slide--title .logo {
            max-height: 100px;
            margin-bottom: 2em;
        }

        /* ========================================
           Content Slide (Bullets)
           ======================================== */
        .bullets {
            list-style: none;
            font-size: clamp(1.1rem, 2vw, 1.5rem);
            line-height: 1.6;
        }

        .bullets li {
            margin-bottom: 0.8em;
            padding-left: 1.5em;
            position: relative;
            opacity: 0;
            transform: translateY(20px);
            animation: fadeInUp 0.5s ease forwards;
        }

        .slide.active .bullets li {
            opacity: 1;
            transform: translateY(0);
        }

        .bullets li:nth-child(1) { animation-delay: 0.1s; }
        .bullets li:nth-child(2) { animation-delay: 0.2s; }
        .bullets li:nth-child(3) { animation-delay: 0.3s; }
        .bullets li:nth-child(4) { animation-delay: 0.4s; }
        .bullets li:nth-child(5) { animation-delay: 0.5s; }
        .bullets li:nth-child(6) { animation-delay: 0.6s; }
        .bullets li:nth-child(7) { animation-delay: 0.7s; }
        .bullets li:nth-child(8) { animation-delay: 0.8s; }

        .bullets li::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0.5em;
            width: 8px;
            height: 8px;
            background: var(--accent-color);
            border-radius: 50%;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* ========================================
           Section Slide
           ======================================== */
        .slide--section {
            background: var(--accent-color);
            text-align: center;
        }

        .slide--section .slide-content {
            text-align: center;
        }

        .slide--section .slide-title {
            color: white;
            font-size: clamp(2.5rem, 6vw, 4rem);
        }

        .slide--section .slide-subtitle {
            color: rgba(255, 255, 255, 0.8);
        }

        /* ========================================
           Quote Slide
           ======================================== */
        .slide--quote {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
            text-align: center;
        }

        .slide--quote .slide-content {
            text-align: center;
            max-width: 900px;
        }

        .quote-text {
            font-family: var(--font-heading);
            font-size: clamp(1.75rem, 4vw, 2.5rem);
            font-style: italic;
            line-height: 1.4;
            margin-bottom: 1.5em;
            position: relative;
        }

        .quote-text::before {
            content: '"';
            font-size: 4em;
            color: var(--accent-color);
            position: absolute;
            top: -0.3em;
            left: -0.3em;
            opacity: 0.3;
            font-family: Georgia, serif;
        }

        .quote-author {
            font-size: 1.25rem;
            color: var(--accent-color);
            font-weight: 500;
        }

        /* ========================================
           Two Column Slide
           ======================================== */
        .two-columns {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 60px;
            width: 100%;
        }

        .column-title {
            font-family: var(--font-heading);
            font-size: 1.5rem;
            color: var(--accent-color);
            margin-bottom: 1em;
            font-weight: 600;
        }

        .column .bullets {
            font-size: 1.1rem;
        }

        /* ========================================
           Image Slide
           ======================================== */
        .slide--image .slide-image {
            max-width: 100%;
            max-height: 60vh;
            border-radius: 8px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            margin: 1.5em 0;
        }

        .image-caption {
            font-size: 1rem;
            color: var(--text-muted);
            text-align: center;
        }

        /* ========================================
           Navigation Controls
           ======================================== */
        .nav-controls {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 12px;
            z-index: 100;
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .presentation:hover .nav-controls {
            opacity: 1;
        }

        .nav-btn {
            width: 44px;
            height: 44px;
            border: none;
            border-radius: 50%;
            background: var(--bg-secondary);
            color: var(--text-primary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            transition: all 0.2s ease;
            border: 1px solid var(--border-color);
        }

        .nav-btn:hover {
            background: var(--accent-color);
            color: white;
            transform: scale(1.1);
        }

        .nav-btn:disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }

        .nav-btn:disabled:hover {
            transform: none;
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        /* ========================================
           Progress Bar
           ======================================== */
        .progress-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            height: 4px;
            background: var(--accent-color);
            transition: width 0.3s ease;
            z-index: 100;
        }

        /* ========================================
           Slide Counter
           ======================================== */
        .slide-counter {
            position: fixed;
            bottom: 30px;
            right: 30px;
            font-family: var(--font-mono);
            font-size: 0.9rem;
            color: var(--text-muted);
            z-index: 100;
        }

        /* ========================================
           Top Bar
           ======================================== */
        .top-bar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 100;
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .presentation:hover .top-bar {
            opacity: 1;
        }

        .top-bar .logo {
            height: 36px;
        }

        .logo-dark { display: block; }
        .logo-light { display: none; }
        [data-theme="light"] .logo-dark { display: none; }
        [data-theme="light"] .logo-light { display: block; }

        .toolbar {
            display: flex;
            gap: 8px;
        }

        .toolbar-btn {
            padding: 8px 12px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            background: var(--bg-secondary);
            color: var(--text-muted);
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s ease;
        }

        .toolbar-btn:hover {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }

        /* ========================================
           Speaker Notes (Hidden by default)
           ======================================== */
        .speaker-notes {
            display: none;
            position: fixed;
            bottom: 80px;
            left: 30px;
            right: 30px;
            max-height: 200px;
            overflow-y: auto;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            font-size: 0.95rem;
            line-height: 1.6;
            color: var(--text-muted);
            z-index: 100;
        }

        .speaker-notes.visible {
            display: block;
        }

        .speaker-notes h4 {
            color: var(--text-primary);
            margin-bottom: 0.5em;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* ========================================
           Keyboard Shortcuts Help
           ======================================== */
        .help-overlay {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.9);
            z-index: 200;
            justify-content: center;
            align-items: center;
        }

        .help-overlay.visible {
            display: flex;
        }

        .help-content {
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 40px;
            max-width: 500px;
        }

        .help-content h3 {
            font-family: var(--font-heading);
            margin-bottom: 1.5em;
            font-size: 1.5rem;
        }

        .shortcut {
            display: flex;
            justify-content: space-between;
            padding: 0.5em 0;
            border-bottom: 1px solid var(--border-color);
        }

        .shortcut:last-child {
            border-bottom: none;
        }

        .shortcut kbd {
            background: var(--bg-tertiary);
            padding: 4px 10px;
            border-radius: 4px;
            font-family: var(--font-mono);
            font-size: 0.85rem;
        }

        /* ========================================
           Fullscreen Mode
           ======================================== */
        .presentation:fullscreen {
            background: var(--bg-primary);
        }

        .presentation:fullscreen .top-bar,
        .presentation:fullscreen .nav-controls {
            opacity: 0;
        }

        .presentation:fullscreen:hover .top-bar,
        .presentation:fullscreen:hover .nav-controls {
            opacity: 1;
        }

        /* ========================================
           Print Styles
           ======================================== */
        @media print {
            .slide {
                position: relative;
                page-break-after: always;
                opacity: 1;
                visibility: visible;
                transform: none;
                height: auto;
                min-height: 100vh;
            }

            .top-bar, .nav-controls, .progress-bar,
            .slide-counter, .speaker-notes, .help-overlay {
                display: none !important;
            }
        }

        /* ========================================
           Responsive
           ======================================== */
        @media (max-width: 768px) {
            .slide {
                padding: 40px 30px;
            }

            .two-columns {
                grid-template-columns: 1fr;
                gap: 30px;
            }

            .nav-controls {
                bottom: 20px;
            }

            .toolbar {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class="presentation" id="presentation">
        <!-- Top Bar -->
        <div class="top-bar">
            {% if logo_path %}
            <div>
                <img src="{{ logo_path }}" alt="{{ title }}" class="logo logo-dark">
                <img src="{{ logo_path_light }}" alt="{{ title }}" class="logo logo-light">
            </div>
            {% else %}
            <div></div>
            {% endif %}
            <div class="toolbar">
                <button class="toolbar-btn" id="theme-toggle" title="Toggle theme (T)">Theme</button>
                <button class="toolbar-btn" id="fullscreen-btn" title="Fullscreen (F)">Fullscreen</button>
                <button class="toolbar-btn" id="help-btn" title="Help (?)">?</button>
            </div>
        </div>

        <!-- Slides -->
        <div class="slides">
            {% for slide in slides %}
            <div class="slide slide--{{ slide.type }}{% if loop.first %} active{% endif %}" data-index="{{ loop.index0 }}" data-notes="{{ slide.notes | e }}">
                <div class="slide-content">
                    {% if slide.type == "title" %}
                        {% if logo_path and loop.first %}
                        <img src="{{ logo_path }}" alt="" class="logo logo-dark">
                        <img src="{{ logo_path_light }}" alt="" class="logo logo-light">
                        {% endif %}
                        <h1 class="slide-title">{{ slide.title }}</h1>
                        <div class="accent-bar"></div>
                        {% if slide.subtitle %}
                        <p class="slide-subtitle">{{ slide.subtitle }}</p>
                        {% endif %}

                    {% elif slide.type == "content" %}
                        <h2 class="slide-title">{{ slide.title }}</h2>
                        <div class="accent-bar"></div>
                        {% if slide.bullets %}
                        <ul class="bullets">
                            {% for bullet in slide.bullets %}
                            <li>{{ bullet }}</li>
                            {% endfor %}
                        </ul>
                        {% endif %}

                    {% elif slide.type == "section" %}
                        <h2 class="slide-title">{{ slide.title }}</h2>
                        {% if slide.subtitle %}
                        <p class="slide-subtitle">{{ slide.subtitle }}</p>
                        {% endif %}

                    {% elif slide.type == "quote" %}
                        <div class="quote-text">{{ slide.quote }}</div>
                        {% if slide.author %}
                        <div class="quote-author">— {{ slide.author }}</div>
                        {% endif %}

                    {% elif slide.type == "two_column" %}
                        <h2 class="slide-title">{{ slide.title }}</h2>
                        <div class="accent-bar"></div>
                        <div class="two-columns">
                            <div class="column">
                                {% if slide.left_title %}
                                <h3 class="column-title">{{ slide.left_title }}</h3>
                                {% endif %}
                                <ul class="bullets">
                                    {% for bullet in slide.left_bullets %}
                                    <li>{{ bullet }}</li>
                                    {% endfor %}
                                </ul>
                            </div>
                            <div class="column">
                                {% if slide.right_title %}
                                <h3 class="column-title">{{ slide.right_title }}</h3>
                                {% endif %}
                                <ul class="bullets">
                                    {% for bullet in slide.right_bullets %}
                                    <li>{{ bullet }}</li>
                                    {% endfor %}
                                </ul>
                            </div>
                        </div>

                    {% elif slide.type == "image" %}
                        <h2 class="slide-title">{{ slide.title }}</h2>
                        <div class="accent-bar"></div>
                        {% if slide.image %}
                        <img src="{{ slide.image }}" alt="{{ slide.title }}" class="slide-image">
                        {% endif %}
                        {% if slide.caption %}
                        <p class="image-caption">{{ slide.caption }}</p>
                        {% endif %}
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- Navigation -->
        <div class="nav-controls">
            <button class="nav-btn" id="prev-btn" title="Previous (←)">←</button>
            <button class="nav-btn" id="next-btn" title="Next (→)">→</button>
        </div>

        <!-- Progress Bar -->
        <div class="progress-bar" id="progress-bar"></div>

        <!-- Slide Counter -->
        <div class="slide-counter">
            <span id="current-slide">1</span> / <span id="total-slides">{{ slides|length }}</span>
        </div>

        <!-- Speaker Notes -->
        <div class="speaker-notes" id="speaker-notes">
            <h4>Speaker Notes</h4>
            <div id="notes-content"></div>
        </div>

        <!-- Help Overlay -->
        <div class="help-overlay" id="help-overlay">
            <div class="help-content">
                <h3>Keyboard Shortcuts</h3>
                <div class="shortcut"><span>Next slide</span><kbd>→</kbd> <kbd>Space</kbd> <kbd>N</kbd></div>
                <div class="shortcut"><span>Previous slide</span><kbd>←</kbd> <kbd>P</kbd></div>
                <div class="shortcut"><span>First slide</span><kbd>Home</kbd></div>
                <div class="shortcut"><span>Last slide</span><kbd>End</kbd></div>
                <div class="shortcut"><span>Fullscreen</span><kbd>F</kbd></div>
                <div class="shortcut"><span>Speaker notes</span><kbd>S</kbd></div>
                <div class="shortcut"><span>Toggle theme</span><kbd>T</kbd></div>
                <div class="shortcut"><span>This help</span><kbd>?</kbd></div>
                <div class="shortcut"><span>Close overlay</span><kbd>Esc</kbd></div>
            </div>
        </div>
    </div>

    <script>
        // Presentation Controller
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
                const savedTheme = localStorage.getItem('presentation-theme') || 'dark';
                document.documentElement.setAttribute('data-theme', savedTheme);

                // Check URL hash for slide number
                const hash = window.location.hash;
                if (hash && hash.startsWith('#slide-')) {
                    const slideNum = parseInt(hash.replace('#slide-', ''));
                    if (slideNum > 0 && slideNum <= this.totalSlides) {
                        this.currentIndex = slideNum - 1;
                    }
                }

                this.bindEvents();
                this.goToSlide(this.currentIndex);
            }

            bindEvents() {
                // Keyboard navigation
                document.addEventListener('keydown', (e) => this.handleKeydown(e));

                // Button clicks
                this.prevBtn.addEventListener('click', () => this.prev());
                this.nextBtn.addEventListener('click', () => this.next());
                this.themeToggle.addEventListener('click', () => this.toggleTheme());
                this.fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
                this.helpBtn.addEventListener('click', () => this.toggleHelp());

                // Touch/swipe support
                let touchStartX = 0;
                document.addEventListener('touchstart', (e) => {
                    touchStartX = e.touches[0].clientX;
                });
                document.addEventListener('touchend', (e) => {
                    const touchEndX = e.changedTouches[0].clientX;
                    const diff = touchStartX - touchEndX;
                    if (Math.abs(diff) > 50) {
                        if (diff > 0) this.next();
                        else this.prev();
                    }
                });

                // Hash change
                window.addEventListener('hashchange', () => {
                    const hash = window.location.hash;
                    if (hash && hash.startsWith('#slide-')) {
                        const slideNum = parseInt(hash.replace('#slide-', ''));
                        if (slideNum > 0 && slideNum <= this.totalSlides) {
                            this.goToSlide(slideNum - 1);
                        }
                    }
                });
            }

            handleKeydown(e) {
                // Don't handle if help overlay is visible (except Escape)
                if (this.helpOverlay.classList.contains('visible') && e.key !== 'Escape') {
                    if (e.key === 'Escape') this.toggleHelp();
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
                        if (this.helpOverlay.classList.contains('visible')) {
                            this.toggleHelp();
                        } else if (document.fullscreenElement) {
                            document.exitFullscreen();
                        }
                        break;
                }
            }

            goToSlide(index) {
                if (index < 0 || index >= this.totalSlides) return;

                // Update classes
                this.slides.forEach((slide, i) => {
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
                const progress = ((this.currentIndex + 1) / this.totalSlides) * 100;
                this.progressBar.style.width = progress + '%';
                this.currentSlideEl.textContent = this.currentIndex + 1;
            }

            updateNotes() {
                const currentSlide = this.slides[this.currentIndex];
                const notes = currentSlide.dataset.notes || '';
                this.notesContent.textContent = notes || 'No notes for this slide.';
            }

            updateButtons() {
                this.prevBtn.disabled = this.currentIndex === 0;
                this.nextBtn.disabled = this.currentIndex === this.totalSlides - 1;
            }

            updateHash() {
                history.replaceState(null, null, '#slide-' + (this.currentIndex + 1));
            }

            toggleTheme() {
                const current = document.documentElement.getAttribute('data-theme');
                const next = current === 'dark' ? 'light' : 'dark';
                document.documentElement.setAttribute('data-theme', next);
                localStorage.setItem('presentation-theme', next);
            }

            toggleFullscreen() {
                const elem = document.getElementById('presentation');
                if (!document.fullscreenElement) {
                    elem.requestFullscreen().catch(err => {
                        console.log('Fullscreen error:', err);
                    });
                } else {
                    document.exitFullscreen();
                }
            }

            toggleNotes() {
                this.speakerNotes.classList.toggle('visible');
            }

            toggleHelp() {
                this.helpOverlay.classList.toggle('visible');
            }
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            new Presentation();
        });
    </script>
</body>
</html>
"""


class PresentationTemplate:
    """HTML presentation template renderer."""

    def __init__(self, theme: "Theme" = None):
        from ..core.theme import COPPER_AND_CREAM

        self.theme = theme or COPPER_AND_CREAM
        self.template = Template(PRESENTATION_TEMPLATE)

    def render(
        self,
        title: str,
        slides: List[Slide],
        logo_path: Optional[str] = None,
        logo_path_light: Optional[str] = None,
        fonts_css_path: Optional[str] = None,
        lang: str = "en",
    ) -> str:
        """Render the presentation to HTML."""
        return self.template.render(
            title=title,
            slides=slides,
            theme=self.theme,
            logo_path=logo_path,
            logo_path_light=logo_path_light or (logo_path.replace("logo.", "logo-light.") if logo_path else None),
            fonts_css_path=fonts_css_path,
            lang=lang,
            date=datetime.now().strftime("%Y-%m-%d"),
        )


def render_presentation(
    title: str,
    slides: List[Slide],
    theme: "Theme" = None,
    logo_path: Optional[str] = None,
    fonts_css_path: Optional[str] = None,
    lang: str = "en",
) -> str:
    """Convenience function to render a presentation."""
    template = PresentationTemplate(theme=theme)
    return template.render(
        title=title,
        slides=slides,
        logo_path=logo_path,
        fonts_css_path=fonts_css_path,
        lang=lang,
    )


def build_presentation_from_yaml(yaml_path: Path, theme: "Theme" = None) -> tuple[str, List[Slide]]:
    """
    Parse a YAML slide definition and return title and slides.

    Args:
        yaml_path: Path to YAML file
        theme: Optional theme

    Returns:
        Tuple of (title, slides)
    """
    import yaml

    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    title = data.get("title", "Presentation")
    subtitle = data.get("subtitle", "")
    slides = []

    # Add title slide if defined at top level
    if title:
        slides.append(Slide(
            type="title",
            title=title,
            subtitle=subtitle,
        ))

    # Process slides
    for slide_data in data.get("slides", []):
        slide_type = slide_data.get("type", "content")

        slide = Slide(
            type=slide_type,
            title=slide_data.get("title", ""),
            subtitle=slide_data.get("subtitle", ""),
            bullets=slide_data.get("bullets", []),
            left_title=slide_data.get("left_title", ""),
            left_bullets=slide_data.get("left_bullets", []),
            right_title=slide_data.get("right_title", ""),
            right_bullets=slide_data.get("right_bullets", []),
            quote=slide_data.get("quote", ""),
            author=slide_data.get("author", ""),
            image=slide_data.get("image", ""),
            caption=slide_data.get("caption", ""),
            notes=slide_data.get("notes", ""),
        )
        slides.append(slide)

    return title, slides
