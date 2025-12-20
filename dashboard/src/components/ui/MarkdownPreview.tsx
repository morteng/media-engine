import { useEffect, useRef } from 'react';
import './MarkdownPreview.css';

interface MarkdownPreviewProps {
  html: string;
  className?: string;
}

export function MarkdownPreview({ html, className = '' }: MarkdownPreviewProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Process images to use proper URLs
    if (containerRef.current) {
      const images = containerRef.current.querySelectorAll('img');
      images.forEach(img => {
        const src = img.getAttribute('src');
        if (src && !src.startsWith('http') && !src.startsWith('/')) {
          // Relative path - prepend /media/ or /api/assets/
          img.setAttribute('src', `/api/assets/${src}`);
        }
      });

      // Add syntax highlighting classes
      const codeBlocks = containerRef.current.querySelectorAll('pre code');
      codeBlocks.forEach(block => {
        block.classList.add('hljs');
      });
    }
  }, [html]);

  return (
    <div
      ref={containerRef}
      className={`markdown-preview ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
