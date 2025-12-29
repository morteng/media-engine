/**
 * useModal - Hook for managing modal state
 *
 * Features:
 * - Simple open/close state management
 * - Data passing to modal
 * - Multiple modal instances support
 * - TypeScript generics for typed data
 *
 * Usage:
 * ```tsx
 * const { isOpen, open, close, data } = useModal<ItemType>();
 *
 * // Open with data
 * <button onClick={() => open(item)}>Edit</button>
 *
 * // In modal
 * <Modal isOpen={isOpen} onClose={close}>
 *   {data && <EditForm item={data} />}
 * </Modal>
 * ```
 */

import { useState, useCallback } from 'react';

export interface UseModalReturn<T = undefined> {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Data passed when opening the modal */
  data: T | null;
  /** Open the modal, optionally with data */
  open: (data?: T) => void;
  /** Close the modal and clear data */
  close: () => void;
  /** Toggle the modal state */
  toggle: () => void;
}

export function useModal<T = undefined>(): UseModalReturn<T> {
  const [isOpen, setIsOpen] = useState(false);
  const [data, setData] = useState<T | null>(null);

  const open = useCallback((openData?: T) => {
    setData(openData ?? null);
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    // Clear data after a short delay to allow exit animations
    setTimeout(() => setData(null), 200);
  }, []);

  const toggle = useCallback(() => {
    setIsOpen(prev => !prev);
  }, []);

  return { isOpen, data, open, close, toggle };
}

/**
 * useConfirmModal - Hook for confirmation dialogs
 *
 * Usage:
 * ```tsx
 * const { confirm, ConfirmDialog } = useConfirmModal();
 *
 * const handleDelete = async () => {
 *   const confirmed = await confirm({
 *     title: 'Delete Item',
 *     message: 'Are you sure?',
 *     variant: 'danger',
 *   });
 *   if (confirmed) {
 *     // Perform delete
 *   }
 * };
 *
 * return (
 *   <>
 *     <button onClick={handleDelete}>Delete</button>
 *     <ConfirmDialog />
 *   </>
 * );
 * ```
 */

export interface ConfirmOptions {
  title: string;
  message: React.ReactNode;
  confirmText?: string;
  cancelText?: string;
  variant?: 'default' | 'danger' | 'warning';
}

export interface UseConfirmModalReturn {
  /** Show confirmation dialog and return promise */
  confirm: (options: ConfirmOptions) => Promise<boolean>;
  /** Current options */
  options: ConfirmOptions | null;
  /** Whether dialog is open */
  isOpen: boolean;
  /** Handle confirm action */
  handleConfirm: () => void;
  /** Handle cancel action */
  handleCancel: () => void;
}

export function useConfirmModal(): UseConfirmModalReturn {
  const [isOpen, setIsOpen] = useState(false);
  const [options, setOptions] = useState<ConfirmOptions | null>(null);
  const [resolveRef, setResolveRef] = useState<((value: boolean) => void) | null>(null);

  const confirm = useCallback((confirmOptions: ConfirmOptions): Promise<boolean> => {
    setOptions(confirmOptions);
    setIsOpen(true);

    return new Promise<boolean>((resolve) => {
      setResolveRef(() => resolve);
    });
  }, []);

  const handleConfirm = useCallback(() => {
    setIsOpen(false);
    resolveRef?.(true);
    setResolveRef(null);
  }, [resolveRef]);

  const handleCancel = useCallback(() => {
    setIsOpen(false);
    resolveRef?.(false);
    setResolveRef(null);
  }, [resolveRef]);

  return { confirm, options, isOpen, handleConfirm, handleCancel };
}

export default useModal;
