/**
 * Toggle - Accessible toggle/switch component
 *
 * Features:
 * - DaisyUI styling
 * - Proper accessibility (role="switch", aria-checked)
 * - Label and description support
 * - Keyboard support (Space to toggle)
 */

import * as React from 'react';
import clsx from 'clsx';

export interface ToggleProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  /** Visual variant */
  variant?: 'default' | 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'error';
  /** Toggle size */
  size?: 'xs' | 'sm' | 'md' | 'lg';
  /** Label text */
  label?: React.ReactNode;
  /** Description text below label */
  description?: string;
  /** Label position relative to toggle */
  labelPosition?: 'left' | 'right';
}

const variantClasses = {
  default: '',
  primary: 'toggle-primary',
  secondary: 'toggle-secondary',
  accent: 'toggle-accent',
  success: 'toggle-success',
  warning: 'toggle-warning',
  error: 'toggle-error',
};

const sizeClasses = {
  xs: 'toggle-xs',
  sm: 'toggle-sm',
  md: 'toggle-md',
  lg: 'toggle-lg',
};

export const Toggle = React.forwardRef<HTMLInputElement, ToggleProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      label,
      description,
      labelPosition = 'right',
      id,
      disabled,
      checked,
      ...props
    },
    ref
  ) => {
    const descriptionId = description ? `${id}-description` : undefined;

    const toggle = (
      <input
        ref={ref}
        type="checkbox"
        role="switch"
        id={id}
        disabled={disabled}
        checked={checked}
        aria-checked={checked}
        aria-describedby={descriptionId}
        className={clsx(
          'toggle',
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      />
    );

    if (!label && !description) {
      return toggle;
    }

    return (
      <div className="form-control">
        <label
          className={clsx(
            'label cursor-pointer justify-start gap-3',
            labelPosition === 'left' && 'flex-row-reverse justify-end',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          {toggle}
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

Toggle.displayName = 'Toggle';

/**
 * ToggleGroup - Group of related toggles
 */
export interface ToggleGroupProps {
  /** Group label */
  label?: string;
  /** Description below label */
  description?: string;
  /** Direction of toggles */
  orientation?: 'horizontal' | 'vertical';
  /** Children (Toggle components) */
  children: React.ReactNode;
  /** Additional className */
  className?: string;
}

export function ToggleGroup({
  label,
  description,
  orientation = 'vertical',
  children,
  className,
}: ToggleGroupProps) {
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
