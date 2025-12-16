"""
Reusable HTML Components

Components for building professional HTML documents:
- Theme toggle button
- Reading progress bar
- Back to top button
- Sidebar navigation
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ThemeToggle:
    """Theme toggle button component."""

    default_theme: str = "dark"

    def render(self) -> str:
        return """
<button class="topbar-btn" id="theme-toggle">
    <span id="theme-icon">☀️</span>
    <span id="theme-text">Light</span>
</button>
"""

    def render_script(self) -> str:
        return f"""
const themeToggle = document.getElementById('theme-toggle');
const themeIcon = document.getElementById('theme-icon');
const themeText = document.getElementById('theme-text');

function setTheme(theme) {{
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    if (theme === 'light') {{
        themeIcon.textContent = '🌙';
        themeText.textContent = 'Dark';
    }} else {{
        themeIcon.textContent = '☀️';
        themeText.textContent = 'Light';
    }}
}}

const savedTheme = localStorage.getItem('theme') || '{self.default_theme}';
setTheme(savedTheme);

themeToggle.addEventListener('click', () => {{
    const current = document.documentElement.getAttribute('data-theme');
    setTheme(current === 'light' ? 'dark' : 'light');
}});
"""


@dataclass
class ReadingProgress:
    """Reading progress bar component."""

    def render(self) -> str:
        return """
<div class="progress-bar">
    <div class="progress-bar-fill" id="progress"></div>
</div>
"""

    def render_script(self) -> str:
        return """
const progressBar = document.getElementById('progress');
window.addEventListener('scroll', () => {
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const progress = (scrollTop / docHeight) * 100;
    progressBar.style.width = progress + '%';
});
"""

    def render_css(self) -> str:
        return """
.progress-bar {
    position: fixed;
    top: 0;
    left: 280px;
    right: 0;
    height: 3px;
    background: var(--bg-tertiary);
    z-index: 200;
}

.progress-bar-fill {
    height: 100%;
    background: var(--accent-color);
    width: 0%;
    transition: width 0.1s ease;
}
"""


@dataclass
class BackToTop:
    """Back to top button component."""

    def render(self) -> str:
        return """
<button class="back-to-top" id="back-to-top">↑</button>
"""

    def render_script(self) -> str:
        return """
const backToTop = document.getElementById('back-to-top');
window.addEventListener('scroll', () => {
    if (window.scrollY > 300) {
        backToTop.classList.add('visible');
    } else {
        backToTop.classList.remove('visible');
    }
});
backToTop.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
});
"""

    def render_css(self) -> str:
        return """
.back-to-top {
    position: fixed;
    bottom: 32px;
    right: 32px;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: var(--accent-color);
    color: white;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    visibility: hidden;
    transition: all 0.2s ease;
    font-size: 20px;
}

.back-to-top.visible {
    opacity: 1;
    visibility: visible;
}

.back-to-top:hover {
    background: var(--accent-hover);
    transform: translateY(-2px);
}
"""


@dataclass
class TocItem:
    """Table of contents item."""

    id: str
    title: str
    level: int = 1


@dataclass
class Sidebar:
    """Sidebar navigation component."""

    title: str = ""
    version: str = ""
    logo_path: str = None
    items: List[TocItem] = None

    def __post_init__(self):
        if self.items is None:
            self.items = []

    def render(self) -> str:
        items_html = ""
        for item in self.items:
            indent = "  " * (item.level - 1)
            items_html += f'''
<li class="toc-item toc-level-{item.level}" data-chapter="{item.id}">
    <a class="toc-link" href="#{item.id}">{indent}{item.title}</a>
</li>
'''

        logo_html = ""
        if self.logo_path:
            logo_html = f'<img src="{self.logo_path}" alt="Logo" class="sidebar-logo">'

        return f"""
<nav class="sidebar" id="sidebar">
    <div class="sidebar-header">
        {logo_html}
        <div class="sidebar-title">{self.title}</div>
        {f'<div class="sidebar-version">Version {self.version}</div>' if self.version else ""}
    </div>
    <ul class="toc">
        {items_html}
    </ul>
</nav>
"""

    def render_script(self) -> str:
        return """
const tocItems = document.querySelectorAll('.toc-item');
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            tocItems.forEach(item => item.classList.remove('active'));
            const id = entry.target.id;
            const tocItem = document.querySelector(`.toc-item[data-chapter="${id}"]`);
            if (tocItem) tocItem.classList.add('active');
        }
    });
}, { rootMargin: '-80px 0px -70% 0px' });

document.querySelectorAll('.chapter, h2[id], h3[id]').forEach(section => {
    observer.observe(section);
});
"""

    def render_css(self) -> str:
        return """
.sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: 280px;
    height: 100vh;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    overflow-y: auto;
    padding: 24px 0;
    z-index: 100;
}

.sidebar-header {
    padding: 0 20px 20px;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 16px;
}

.sidebar-logo {
    max-width: 120px;
    height: auto;
    margin-bottom: 12px;
}

.sidebar-title {
    font-family: var(--font-heading);
    font-size: 15px;
    font-weight: 500;
    color: var(--text-primary);
}

.sidebar-version {
    font-size: 12px;
    color: var(--text-muted);
}

.toc {
    list-style: none;
    padding: 0;
    margin: 0;
}

.toc-item {
    border-left: 2px solid transparent;
}

.toc-item.active {
    border-left-color: var(--accent-color);
    background: var(--accent-light);
}

.toc-link {
    display: block;
    padding: 8px 20px;
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 14px;
    transition: all 0.15s ease;
}

.toc-link:hover {
    color: var(--accent-color);
    background: var(--bg-tertiary);
}

.toc-item.active .toc-link {
    color: var(--accent-color);
    font-weight: 500;
}

.toc-level-2 .toc-link {
    padding-left: 32px;
    font-size: 13px;
}

.toc-level-3 .toc-link {
    padding-left: 44px;
    font-size: 12px;
}
"""
