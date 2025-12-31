/**
 * Utility function to highlight text and return HTML string.
 * Useful when you need to set innerHTML or use with dangerouslySetInnerHTML.
 *
 * Note: Be careful with XSS when using this with user-provided content.
 * Always sanitize the text and highlight parameters before use.
 *
 * @example
 * ```tsx
 * const html = highlightText("Hello World", "world");
 * // Returns: "Hello <mark class=\"...\">World</mark>"
 * ```
 */
export function highlightText(
  text: string,
  highlight: string,
  options: {
    highlightClassName?: string;
    caseSensitive?: boolean;
    highlightAll?: boolean;
  } = {}
): string {
  const {
    highlightClassName = 'bg-warning/30 text-warning-content rounded-sm px-0.5',
    caseSensitive = false,
    highlightAll = true,
  } = options;

  if (!highlight?.trim() || !text) {
    return text;
  }

  const searchTerm = highlight.trim();
  const escapedTerm = searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const flags = caseSensitive ? (highlightAll ? 'g' : '') : (highlightAll ? 'gi' : 'i');
  const regex = new RegExp(`(${escapedTerm})`, flags);

  return text.replace(regex, `<mark class="${highlightClassName}">$1</mark>`);
}

/**
 * Escape special regex characters in a string
 */
export function escapeRegex(string: string): string {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
