import * as React from 'react';
import { useCallback, useEffect, useRef, useState } from 'react';
import clsx from 'clsx';
import { Search, X } from 'lucide-react';
import { Spinner } from './Spinner';
import { Badge } from './Badge';
import { isMac } from '@/hooks/useKeyboardShortcuts';

export interface SearchInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange' | 'value'> {
  /**
   * Current search value
   */
  value: string;
  /**
   * Callback when search value changes (debounced by default)
   */
  onChange: (value: string) => void;
  /**
   * Callback when clear button is clicked
   */
  onClear?: () => void;
  /**
   * Whether search is in progress
   */
  isSearching?: boolean;
  /**
   * Number of results found (displayed as badge)
   */
  resultCount?: number;
  /**
   * Debounce delay in milliseconds
   * @default 300
   */
  debounceMs?: number;
  /**
   * Size variant
   * @default 'md'
   */
  size?: 'sm' | 'md' | 'lg';
  /**
   * Enable Cmd/Ctrl+F to focus this input
   * @default false
   */
  enableGlobalShortcut?: boolean;
  /**
   * Custom shortcut key (used with Cmd/Ctrl)
   * @default 'f'
   */
  shortcutKey?: string;
}

const sizeClasses: Record<string, string> = {
  sm: 'input-sm text-sm',
  md: 'input-md',
  lg: 'input-lg text-lg',
};

const iconSizeClasses: Record<string, number> = {
  sm: 14,
  md: 16,
  lg: 20,
};

let searchInputIdCounter = 0;
function generateSearchInputId() {
  return `search-input-${++searchInputIdCounter}`;
}

const SearchInput = React.forwardRef<HTMLInputElement, SearchInputProps>(
  (
    {
      value,
      onChange,
      onClear,
      isSearching = false,
      resultCount,
      debounceMs = 300,
      size = 'md',
      placeholder = 'Search...',
      enableGlobalShortcut = false,
      shortcutKey = 'f',
      className,
      id,
      disabled,
      ...props
    },
    ref
  ) => {
    const [internalValue, setInternalValue] = useState(value);
    const inputRef = useRef<HTMLInputElement>(null);
    const debounceTimerRef = useRef<ReturnType<typeof setTimeout>>();
    const generatedId = React.useMemo(() => id || generateSearchInputId(), [id]);

    // Sync external value changes
    useEffect(() => {
      setInternalValue(value);
    }, [value]);

    // Handle debounced onChange
    const handleChange = useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = e.target.value;
        setInternalValue(newValue);

        if (debounceTimerRef.current) {
          clearTimeout(debounceTimerRef.current);
        }

        if (debounceMs > 0) {
          debounceTimerRef.current = setTimeout(() => {
            onChange(newValue);
          }, debounceMs);
        } else {
          onChange(newValue);
        }
      },
      [onChange, debounceMs]
    );

    // Handle clear
    const handleClear = useCallback(() => {
      setInternalValue('');
      onChange('');
      onClear?.();
      inputRef.current?.focus();
    }, [onChange, onClear]);

    // Handle global keyboard shortcut
    useEffect(() => {
      if (!enableGlobalShortcut) return;

      const handleKeyDown = (e: KeyboardEvent) => {
        // Skip if user is typing in another input
        const target = e.target as HTMLElement;
        const isOtherInput =
          target !== inputRef.current &&
          (target.tagName === 'INPUT' ||
            target.tagName === 'TEXTAREA' ||
            target.isContentEditable);

        if (isOtherInput) return;

        // Check for Cmd/Ctrl + shortcutKey
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === shortcutKey.toLowerCase()) {
          e.preventDefault();
          inputRef.current?.focus();
          inputRef.current?.select();
        }
      };

      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }, [enableGlobalShortcut, shortcutKey]);

    // Cleanup debounce timer on unmount
    useEffect(() => {
      return () => {
        if (debounceTimerRef.current) {
          clearTimeout(debounceTimerRef.current);
        }
      };
    }, []);

    // Forward ref
    React.useImperativeHandle(ref, () => inputRef.current!);

    const hasValue = internalValue.length > 0;
    const iconSize = iconSizeClasses[size];
    const showResultCount = resultCount !== undefined && hasValue && !isSearching;
    const shortcutHint = enableGlobalShortcut ? (isMac() ? `\u2318${shortcutKey.toUpperCase()}` : `Ctrl+${shortcutKey.toUpperCase()}`) : undefined;

    return (
      <div className={clsx('relative flex items-center', className)}>
        {/* Search icon */}
        <div className="absolute left-3 flex items-center pointer-events-none text-base-content/50">
          {isSearching ? (
            <Spinner size="sm" />
          ) : (
            <Search size={iconSize} />
          )}
        </div>

        {/* Input */}
        <input
          ref={inputRef}
          id={generatedId}
          type="text"
          className={clsx(
            'input input-bordered w-full pl-10',
            sizeClasses[size],
            hasValue && 'pr-20',
            !hasValue && shortcutHint && 'pr-14',
            !hasValue && !shortcutHint && 'pr-3'
          )}
          placeholder={placeholder}
          value={internalValue}
          onChange={handleChange}
          disabled={disabled}
          aria-label={placeholder}
          {...props}
        />

        {/* Right side elements */}
        <div className="absolute right-2 flex items-center gap-1.5">
          {/* Result count badge */}
          {showResultCount && (
            <Badge
              variant={resultCount > 0 ? 'primary' : 'ghost'}
              size="sm"
              className="tabular-nums"
            >
              {resultCount}
            </Badge>
          )}

          {/* Shortcut hint (when empty) */}
          {!hasValue && shortcutHint && (
            <kbd className="kbd kbd-xs text-base-content/40">{shortcutHint}</kbd>
          )}

          {/* Clear button */}
          {hasValue && (
            <button
              type="button"
              className={clsx(
                'btn btn-ghost btn-circle',
                size === 'sm' ? 'btn-xs' : 'btn-sm'
              )}
              onClick={handleClear}
              aria-label="Clear search"
              disabled={disabled}
            >
              <X size={iconSize} />
            </button>
          )}
        </div>
      </div>
    );
  }
);
SearchInput.displayName = 'SearchInput';

export { SearchInput };
