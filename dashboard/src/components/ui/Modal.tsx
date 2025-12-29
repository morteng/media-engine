/**
 * Modal - Reusable modal dialog component
 * Built on DaisyUI's modal styling with consistent patterns
 *
 * Features:
 * - Focus trap (Tab cycles within modal)
 * - Auto-focus first interactive element
 * - Returns focus to trigger element on close
 * - Keyboard navigation (Escape to close)
 * - ARIA attributes for screen readers
 */

import { useEffect, useCallback, useRef, useId, type ReactNode } from 'react';
import { X } from 'lucide-react';
import clsx from 'clsx';

// Focusable element selectors
const FOCUSABLE_SELECTORS = [
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  'a[href]',
  '[tabindex]:not([tabindex="-1"])',
].join(', ');

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: ReactNode;
  children: ReactNode;
  actions?: ReactNode;
  /** Modal size variant */
  size?: 'sm' | 'md' | 'lg' | 'full';
  /** Close on backdrop click (default: true) */
  closeOnBackdrop?: boolean;
  /** Close on Escape key (default: true) */
  closeOnEscape?: boolean;
  /** Show close button in header (default: true) */
  showCloseButton?: boolean;
  /** Additional class for modal-box */
  className?: string;
}

const sizeClasses = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-3xl',
  full: 'max-w-full w-11/12',
};

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  actions,
  size = 'md',
  closeOnBackdrop = true,
  closeOnEscape = true,
  showCloseButton = true,
  className,
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);
  const titleId = useId();

  // Handle keyboard events (Escape and Tab for focus trap)
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Close on Escape
      if (closeOnEscape && event.key === 'Escape') {
        onClose();
        return;
      }

      // Focus trap - cycle through focusable elements
      if (event.key === 'Tab' && modalRef.current) {
        const focusable = modalRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTORS);
        const firstFocusable = focusable[0];
        const lastFocusable = focusable[focusable.length - 1];

        if (event.shiftKey) {
          // Shift+Tab: if on first element, go to last
          if (document.activeElement === firstFocusable) {
            event.preventDefault();
            lastFocusable?.focus();
          }
        } else {
          // Tab: if on last element, go to first
          if (document.activeElement === lastFocusable) {
            event.preventDefault();
            firstFocusable?.focus();
          }
        }
      }
    },
    [closeOnEscape, onClose]
  );

  useEffect(() => {
    if (isOpen) {
      // Store currently focused element to restore later
      previousActiveElement.current = document.activeElement as HTMLElement;

      // Add keyboard listener
      document.addEventListener('keydown', handleKeyDown);

      // Prevent body scroll
      document.body.style.overflow = 'hidden';

      // Focus first focusable element in modal (after render)
      requestAnimationFrame(() => {
        if (modalRef.current) {
          const focusable = modalRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTORS);
          const firstFocusable = focusable[0];
          firstFocusable?.focus();
        }
      });
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';

      // Restore focus to previously focused element
      if (previousActiveElement.current && isOpen) {
        previousActiveElement.current.focus();
      }
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  return (
    <div
      className="modal modal-open"
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? titleId : undefined}
    >
      <div
        ref={modalRef}
        className={clsx('modal-box', sizeClasses[size], className)}
      >
        {/* Header with title and close button */}
        {(title || showCloseButton) && (
          <div className="flex items-start justify-between mb-4">
            {title && (
              <h3 id={titleId} className="font-bold text-lg">{title}</h3>
            )}
            {showCloseButton && (
              <button
                onClick={onClose}
                className="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
                aria-label="Close modal"
              >
                <X size={16} aria-hidden="true" />
              </button>
            )}
          </div>
        )}

        {/* Content */}
        <div>{children}</div>

        {/* Actions */}
        {actions && (
          <div className="modal-action">{actions}</div>
        )}
      </div>

      {/* Backdrop */}
      <div
        className="modal-backdrop"
        onClick={closeOnBackdrop ? onClose : undefined}
        aria-hidden="true"
      />
    </div>
  );
}

/**
 * Pre-styled confirmation modal variant
 */
export interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: ReactNode;
  confirmText?: string;
  cancelText?: string;
  variant?: 'default' | 'danger' | 'warning';
  isLoading?: boolean;
}

const variantStyles = {
  default: {
    titleClass: '',
    buttonClass: 'btn-primary',
  },
  danger: {
    titleClass: 'text-error',
    buttonClass: 'btn-error',
  },
  warning: {
    titleClass: 'text-warning',
    buttonClass: 'btn-warning',
  },
};

export function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'default',
  isLoading = false,
}: ConfirmModalProps) {
  const styles = variantStyles[variant];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={<span className={styles.titleClass}>{title}</span>}
      actions={
        <>
          <button onClick={onClose} className="btn btn-ghost">
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={clsx('btn', styles.buttonClass)}
          >
            {isLoading && <span className="loading loading-spinner loading-sm" />}
            {confirmText}
          </button>
        </>
      }
    >
      <div className="text-base-content/60">{message}</div>
    </Modal>
  );
}
