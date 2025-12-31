import * as React from 'react';
import clsx from 'clsx';

export interface VisuallyHiddenProps extends React.HTMLAttributes<HTMLElement> {
  /**
   * When true, the element becomes visible when focused (for skip links)
   */
  focusable?: boolean;
  /**
   * The HTML element to render
   */
  as?: 'span' | 'div';
}

/**
 * VisuallyHidden hides content visually but keeps it accessible to screen readers.
 * Use this for content that should be read by assistive technologies but not displayed visually.
 *
 * @example
 * // Hidden label for icon button
 * <button>
 *   <SearchIcon />
 *   <VisuallyHidden>Search</VisuallyHidden>
 * </button>
 *
 * @example
 * // Skip link that appears on focus
 * <VisuallyHidden focusable>
 *   <a href="#main-content">Skip to main content</a>
 * </VisuallyHidden>
 */
const VisuallyHidden = React.forwardRef<HTMLElement, VisuallyHiddenProps>(
  ({ className, focusable = false, as: Component = 'span', children, ...props }, ref) => {
    return (
      <Component
        ref={ref as React.Ref<HTMLSpanElement & HTMLDivElement>}
        className={clsx(
          // Base styles for screen reader only content
          'absolute w-px h-px p-0 -m-px overflow-hidden whitespace-nowrap border-0',
          // Clip to hide visually
          '[clip:rect(0,0,0,0)]',
          // When focusable, show on focus
          focusable && [
            'focus-within:static focus-within:w-auto focus-within:h-auto focus-within:m-0',
            'focus-within:overflow-visible focus-within:whitespace-normal focus-within:[clip:auto]',
          ],
          className
        )}
        {...props}
      >
        {children}
      </Component>
    );
  }
);

VisuallyHidden.displayName = 'VisuallyHidden';

export { VisuallyHidden };
