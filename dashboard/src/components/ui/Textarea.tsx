import * as React from 'react';
import clsx from 'clsx';

let textareaIdCounter = 0;
function generateTextareaId() {
  return `textarea-${++textareaIdCounter}`;
}

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /**
   * Description text that provides additional context for the textarea.
   * Creates an aria-describedby relationship for screen readers.
   */
  description?: string;
  /**
   * Error message to display when the textarea is in an error state.
   * Sets aria-invalid="true" and creates aria-describedby relationship.
   */
  error?: string;
  /**
   * Whether to render the description and error elements.
   * Set to false if you want to manage these externally.
   * @default true
   */
  renderMessages?: boolean;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, id, description, error, renderMessages = true, 'aria-describedby': ariaDescribedBy, ...props }, ref) => {
    // Generate a stable ID if not provided
    const generatedId = React.useMemo(() => id || generateTextareaId(), [id]);
    const descriptionId = `${generatedId}-description`;
    const errorId = `${generatedId}-error`;

    // Build aria-describedby from description, error, and any passed aria-describedby
    const describedByParts: string[] = [];
    if (ariaDescribedBy) describedByParts.push(ariaDescribedBy);
    if (description) describedByParts.push(descriptionId);
    if (error) describedByParts.push(errorId);
    const describedBy = describedByParts.length > 0 ? describedByParts.join(' ') : undefined;

    return (
      <>
        <textarea
          id={generatedId}
          className={clsx(
            'textarea textarea-bordered w-full',
            error && 'textarea-error',
            className
          )}
          ref={ref}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          {...props}
        />
        {renderMessages && description && !error && (
          <p id={descriptionId} className="mt-1 text-sm text-base-content/70">
            {description}
          </p>
        )}
        {renderMessages && error && (
          <p id={errorId} className="mt-1 text-sm text-error" role="alert">
            {error}
          </p>
        )}
      </>
    );
  }
);
Textarea.displayName = 'Textarea';

export { Textarea };
