import { useEffect, useRef } from 'react';

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
      className={`prose prose-invert prose-sm max-w-none
        prose-headings:text-base-content prose-headings:font-semibold
        prose-p:text-base-content/80 prose-p:leading-relaxed
        prose-a:text-primary prose-a:no-underline hover:prose-a:underline
        prose-strong:text-base-content prose-strong:font-semibold
        prose-code:text-primary prose-code:bg-base-300 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:before:content-none prose-code:after:content-none
        prose-pre:bg-base-300 prose-pre:rounded-lg prose-pre:p-4
        prose-blockquote:border-l-primary prose-blockquote:bg-base-300/50 prose-blockquote:py-1 prose-blockquote:px-4 prose-blockquote:rounded-r
        prose-ul:text-base-content/80 prose-ol:text-base-content/80
        prose-li:marker:text-primary
        prose-hr:border-base-300
        prose-img:rounded-lg prose-img:shadow-md
        prose-table:text-base-content/80
        prose-th:bg-base-300 prose-th:p-2 prose-th:text-left
        prose-td:p-2 prose-td:border-b prose-td:border-base-300
        ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
