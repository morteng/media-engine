/**
 * Checkbox - Accessible checkbox component
 *
 * Features:
 * - DaisyUI styling
 * - Indeterminate state support
 * - Proper accessibility (aria-checked, aria-describedby)
 * - Label and description support
 */

import * as React from 'react';
import clsx from 'clsx';

export interface CheckboxProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type' | 'size'> {
  /** Visual variant */
  variant?: 'default' | 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'error';
  /** Checkbox size */
  size?: 'xs' | 'sm' | 'md' | 'lg';
  /** Label text */
  label?: React.ReactNode;
  /** Description text below label */
  description?: string;
  /** Indeterminate state (partial selection) */
  indeterminate?: boolean;
}

const variantClasses = {
  default: '',
  primary: 'checkbox-primary',
  secondary: 'checkbox-secondary',
  accent: 'checkbox-accent',
  success: 'checkbox-success',
  warning: 'checkbox-warning',
  error: 'checkbox-error',
};

const sizeClasses = {
  xs: 'checkbox-xs',
  sm: 'checkbox-sm',
  md: 'checkbox-md',
  lg: 'checkbox-lg',
};

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      label,
      description,
      indeterminate,
      id,
      disabled,
      ...props
    },
    ref
  ) => {
    const inputRef = React.useRef<HTMLInputElement>(null);
    const descriptionId = description ? `${id}-description` : undefined;

    // Handle indeterminate state
    React.useEffect(() => {
      if (inputRef.current) {
        inputRef.current.indeterminate = indeterminate ?? false;
      }
    }, [indeterminate]);

    // Merge refs
    React.useImperativeHandle(ref, () => inputRef.current as HTMLInputElement);

    const checkbox = (
      <input
        ref={inputRef}
        type="checkbox"
        id={id}
        disabled={disabled}
        aria-describedby={descriptionId}
        className={clsx(
          'checkbox',
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      />
    );

    if (!label && !description) {
      return checkbox;
    }

    return (
      <div className="form-control">
        <label
          className={clsx(
            'label cursor-pointer justify-start gap-3',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          {checkbox}
          <div className="flex flex-col">
            {label && (
              <span className="label-text">{label}</span>
            )}
            {description && (
              <span
                id={descriptionId}
                className="label-text-alt text-base-content/60"
              >
                {description}
              </span>
            )}
          </div>
        </label>
      </div>
    );
  }
);

Checkbox.displayName = 'Checkbox';

/**
 * CheckboxGroup - Group of related checkboxes
 */
export interface CheckboxGroupProps {
  /** Group label */
  label?: string;
  /** Description below label */
  description?: string;
  /** Direction of checkboxes */
  orientation?: 'horizontal' | 'vertical';
  /** Children (Checkbox components) */
  children: React.ReactNode;
  /** Additional className */
  className?: string;
}

export function CheckboxGroup({
  label,
  description,
  orientation = 'vertical',
  children,
  className,
}: CheckboxGroupProps) {
  return (
    <fieldset className={className}>
      {label && (
        <legend className="label-text font-medium mb-2">{label}</legend>
      )}
      {description && (
        <p className="text-sm text-base-content/60 mb-3">{description}</p>
      )}
      <div
        className={clsx(
          orientation === 'horizontal' ? 'flex flex-wrap gap-4' : 'flex flex-col gap-2'
        )}
      >
        {children}
      </div>
    </fieldset>
  );
}
