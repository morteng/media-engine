import * as React from 'react';
import clsx from 'clsx';

export interface SearchHighlightProps {
  /**
   * The text content to display and potentially highlight
   */
  text: string;
  /**
   * The search term to highlight within the text
   * If empty or undefined, text is rendered without highlighting
   */
  highlight?: string;
  /**
   * Additional class names for the container span
   */
  className?: string;
  /**
   * Class names for the highlighted mark elements
   * @default 'bg-warning/30 text-warning-content rounded-sm px-0.5'
   */
  highlightClassName?: string;
  /**
   * Whether to perform case-sensitive matching
   * @default false
   */
  caseSensitive?: boolean;
  /**
   * Whether to highlight all occurrences or just the first
   * @default true
   */
  highlightAll?: boolean;
}

/**
 * Component that highlights matching text within content.
 * Wraps matching portions in <mark> tags for visual distinction.
 *
 * @example
 * ```tsx
 * <SearchHighlight text="Hello World" highlight="world" />
 * // Renders: Hello <mark>World</mark>
 *
 * <SearchHighlight
 *   text="The quick brown fox"
 *   highlight="quick"
 *   highlightClassName="bg-primary/30"
 * />
 * ```
 */
export function SearchHighlight({
  text,
  highlight,
  className,
  highlightClassName = 'bg-warning/30 text-warning-content rounded-sm px-0.5',
  caseSensitive = false,
  highlightAll = true,
}: SearchHighlightProps) {
  // If no highlight term or empty text, return plain text
  if (!highlight?.trim() || !text) {
    return <span className={className}>{text}</span>;
  }

  const searchTerm = highlight.trim();

  // Escape special regex characters in the search term
  const escapedTerm = searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

  // Create regex with appropriate flags
  const flags = caseSensitive ? (highlightAll ? 'g' : '') : (highlightAll ? 'gi' : 'i');
  const regex = new RegExp(`(${escapedTerm})`, flags);

  // Split text by the search term, preserving the matched parts
  const parts = text.split(regex);

  // If no match found, return plain text
  if (parts.length === 1) {
    return <span className={className}>{text}</span>;
  }

  return (
    <span className={className}>
      {parts.map((part, index) => {
        // Check if this part matches the search term
        const isMatch = caseSensitive
          ? part === searchTerm
          : part.toLowerCase() === searchTerm.toLowerCase();

        if (isMatch) {
          return (
            <mark
              key={index}
              className={clsx('font-inherit', highlightClassName)}
            >
              {part}
            </mark>
          );
        }

        return <React.Fragment key={index}>{part}</React.Fragment>;
      })}
    </span>
  );
}
