/**
 * UnsavedChangesDialog - Confirmation dialog for unsaved changes
 *
 * Shows a warning dialog when user tries to navigate away with unsaved changes.
 * Provides options to save, discard, or cancel the navigation.
 */

import { AlertTriangle, Save } from 'lucide-react';
import { Modal } from './Modal';

export interface UnsavedChangesDialogProps {
  /**
   * Whether the dialog is open
   */
  isOpen: boolean;

  /**
   * Called when user chooses to proceed without saving (discard changes)
   */
  onConfirm: () => void;

  /**
   * Called when user chooses to stay on the page (cancel navigation)
   */
  onCancel: () => void;

  /**
   * Optional callback when user chooses to save then proceed
   * If not provided, the save button won't be shown
   */
  onSave?: () => void;

  /**
   * Custom title for the dialog
   */
  title?: string;

  /**
   * Custom message for the dialog
   */
  message?: string;

  /**
   * Whether save operation is in progress
   */
  isSaving?: boolean;
}

/**
 * A confirmation dialog shown when user tries to navigate away with unsaved changes.
 *
 * @example
 * ```tsx
 * <UnsavedChangesDialog
 *   isOpen={showDialog}
 *   onConfirm={() => {
 *     setShowDialog(false);
 *     navigate(pendingPath);
 *   }}
 *   onCancel={() => setShowDialog(false)}
 *   onSave={async () => {
 *     await save();
 *     setShowDialog(false);
 *     navigate(pendingPath);
 *   }}
 * />
 * ```
 */
export function UnsavedChangesDialog({
  isOpen,
  onConfirm,
  onCancel,
  onSave,
  title = 'Unsaved Changes',
  message = 'You have unsaved changes. Do you want to leave without saving?',
  isSaving = false,
}: UnsavedChangesDialogProps) {
  if (!isOpen) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onCancel}
      size="sm"
      closeOnBackdrop={false}
      closeOnEscape={!isSaving}
      showCloseButton={!isSaving}
    >
      <div className="flex flex-col items-center text-center">
        {/* Warning Icon */}
        <div className="flex justify-center mb-4">
          <div className="p-3 rounded-full bg-warning/10">
            <AlertTriangle className="w-6 h-6 text-warning" aria-hidden="true" />
          </div>
        </div>

        {/* Title */}
        <h3 className="font-bold text-lg mb-2">{title}</h3>

        {/* Message */}
        <p className="text-base-content/70 mb-6">{message}</p>

        {/* Actions */}
        <div className="flex flex-wrap justify-center gap-2 w-full">
          {/* Cancel - Stay on page */}
          <button
            onClick={onCancel}
            className="btn btn-ghost"
            disabled={isSaving}
            aria-label="Stay on this page"
          >
            Stay
          </button>

          {/* Discard - Leave without saving */}
          <button
            onClick={onConfirm}
            className="btn btn-warning btn-outline"
            disabled={isSaving}
            aria-label="Discard changes and leave"
          >
            Discard Changes
          </button>

          {/* Save - Save then leave (optional) */}
          {onSave && (
            <button
              onClick={onSave}
              className="btn btn-primary gap-1"
              disabled={isSaving}
              aria-label="Save changes and leave"
            >
              {isSaving ? (
                <span className="loading loading-spinner loading-sm" />
              ) : (
                <Save size={14} aria-hidden="true" />
              )}
              Save & Leave
            </button>
          )}
        </div>
      </div>
    </Modal>
  );
}

export default UnsavedChangesDialog;
