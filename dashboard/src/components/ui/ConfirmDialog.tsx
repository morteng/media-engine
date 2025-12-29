import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { AlertTriangle, Trash2, X } from 'lucide-react';

type ConfirmVariant = 'default' | 'danger' | 'warning';

// Shared variant styles - defined once at module level
const CONFIRM_VARIANT_STYLES: Record<ConfirmVariant, { button: string; icon: ReactNode }> = {
  default: {
    button: 'btn-primary',
    icon: null,
  },
  warning: {
    button: 'btn-warning',
    icon: <AlertTriangle className="w-6 h-6 text-warning" aria-hidden="true" />,
  },
  danger: {
    button: 'btn-error',
    icon: <Trash2 className="w-6 h-6 text-error" aria-hidden="true" />,
  },
};

interface ConfirmOptions {
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: ConfirmVariant;
  icon?: ReactNode;
}

interface ConfirmContextType {
  confirm: (options: ConfirmOptions) => Promise<boolean>;
}

const ConfirmContext = createContext<ConfirmContextType | null>(null);

/**
 * Hook to access the confirm dialog.
 *
 * @example
 * const { confirm } = useConfirm();
 *
 * const handleDelete = async () => {
 *   const confirmed = await confirm({
 *     title: "Delete script?",
 *     description: "This action cannot be undone.",
 *     variant: "danger",
 *   });
 *   if (confirmed) {
 *     deleteScript();
 *   }
 * };
 */
export function useConfirm() {
  const context = useContext(ConfirmContext);
  if (!context) {
    throw new Error('useConfirm must be used within a ConfirmProvider');
  }
  return context;
}

interface ConfirmState extends ConfirmOptions {
  isOpen: boolean;
  resolve: ((value: boolean) => void) | null;
}

/**
 * Provider for confirm dialogs. Wrap your app with this to enable
 * the useConfirm hook throughout the application.
 */
export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<ConfirmState>({
    isOpen: false,
    title: '',
    resolve: null,
  });

  const confirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      setState({
        isOpen: true,
        resolve,
        ...options,
      });
    });
  }, []);

  const handleConfirm = useCallback(() => {
    state.resolve?.(true);
    setState((prev) => ({ ...prev, isOpen: false, resolve: null }));
  }, [state.resolve]);

  const handleCancel = useCallback(() => {
    state.resolve?.(false);
    setState((prev) => ({ ...prev, isOpen: false, resolve: null }));
  }, [state.resolve]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleCancel();
      } else if (e.key === 'Enter') {
        handleConfirm();
      }
    },
    [handleCancel, handleConfirm]
  );

  const variant = state.variant || 'default';
  const styles = CONFIRM_VARIANT_STYLES[variant];

  return (
    <ConfirmContext.Provider value={{ confirm }}>
      {children}

      {/* Confirm Dialog */}
      {state.isOpen && (
        <div
          className="modal modal-open"
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="confirm-title"
          aria-describedby="confirm-description"
          onKeyDown={handleKeyDown}
        >
          <div className="modal-box max-w-sm">
            {/* Close button */}
            <button
              onClick={handleCancel}
              className="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
              aria-label="Close dialog"
            >
              <X size={16} aria-hidden="true" />
            </button>

            {/* Icon */}
            {(state.icon || styles.icon) && (
              <div className="flex justify-center mb-4">
                <div className={`p-3 rounded-full ${
                  variant === 'danger' ? 'bg-error/10' :
                  variant === 'warning' ? 'bg-warning/10' : 'bg-primary/10'
                }`}>
                  {state.icon || styles.icon}
                </div>
              </div>
            )}

            {/* Title */}
            <h3 id="confirm-title" className="font-bold text-lg text-center">
              {state.title}
            </h3>

            {/* Description */}
            {state.description && (
              <p id="confirm-description" className="text-base-content/70 text-center mt-2">
                {state.description}
              </p>
            )}

            {/* Actions */}
            <div className="modal-action justify-center gap-3">
              <button
                onClick={handleCancel}
                className="btn btn-ghost"
                aria-label={state.cancelText || 'Cancel'}
              >
                {state.cancelText || 'Cancel'}
              </button>
              <button
                onClick={handleConfirm}
                className={`btn ${styles.button}`}
                aria-label={state.confirmText || 'Confirm'}
                autoFocus
              >
                {state.confirmText || 'Confirm'}
              </button>
            </div>
          </div>

          {/* Backdrop */}
          <div
            className="modal-backdrop bg-black/50"
            onClick={handleCancel}
            aria-hidden="true"
          />
        </div>
      )}
    </ConfirmContext.Provider>
  );
}

/**
 * Standalone confirm dialog component for non-hook usage.
 */
export function ConfirmDialog({
  open,
  onConfirm,
  onCancel,
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'default',
  icon,
}: {
  open: boolean;
  onConfirm: () => void;
  onCancel: () => void;
} & ConfirmOptions) {
  const styles = CONFIRM_VARIANT_STYLES[variant];

  if (!open) return null;

  return (
    <div
      className="modal modal-open"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      aria-describedby={description ? "confirm-dialog-description" : undefined}
    >
      <div className="modal-box max-w-sm">
        <button
          onClick={onCancel}
          className="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
          aria-label="Close dialog"
        >
          <X size={16} aria-hidden="true" />
        </button>

        {(icon || styles.icon) && (
          <div className="flex justify-center mb-4">
            <div className={`p-3 rounded-full ${
              variant === 'danger' ? 'bg-error/10' :
              variant === 'warning' ? 'bg-warning/10' : 'bg-primary/10'
            }`}>
              {icon || styles.icon}
            </div>
          </div>
        )}

        <h3 id="confirm-dialog-title" className="font-bold text-lg text-center">
          {title}
        </h3>

        {description && (
          <p id="confirm-dialog-description" className="text-base-content/70 text-center mt-2">
            {description}
          </p>
        )}

        <div className="modal-action justify-center gap-3">
          <button onClick={onCancel} className="btn btn-ghost">
            {cancelText}
          </button>
          <button onClick={onConfirm} className={`btn ${styles.button}`} autoFocus>
            {confirmText}
          </button>
        </div>
      </div>

      <div className="modal-backdrop bg-black/50" onClick={onCancel} aria-hidden="true" />
    </div>
  );
}
