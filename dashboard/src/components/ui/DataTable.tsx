/**
 * DataTable - Generic typed table component with sorting, selection, and pagination
 *
 * Features:
 * - Generic type support for any data type
 * - Column definitions with custom renderers
 * - Sorting (ascending/descending)
 * - Multi-select with checkbox column
 * - Loading state with skeleton
 * - Empty state
 * - Pagination
 * - Responsive horizontal scroll
 * - Striped rows option
 * - Row click handling
 */

import * as React from 'react';
import clsx from 'clsx';
import { ChevronUp, ChevronDown, ChevronsUpDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { Checkbox } from './Checkbox';
import { SkeletonTable } from './Skeleton';
import { EmptyState } from './EmptyState';

export interface Column<T> {
  /** Unique key for the column */
  key: string;
  /** Header content (string or ReactNode) */
  header: string | React.ReactNode;
  /** Render function for cell content */
  render: (item: T) => React.ReactNode;
  /** Whether this column is sortable */
  sortable?: boolean;
  /** Column width (CSS value) */
  width?: string;
  /** Text alignment */
  align?: 'left' | 'center' | 'right';
}

export interface PaginationConfig {
  /** Current page (0-indexed) */
  page: number;
  /** Number of items per page */
  pageSize: number;
  /** Total number of items */
  total: number;
  /** Callback when page changes */
  onPageChange: (page: number) => void;
}

export type SortDirection = 'asc' | 'desc' | null;

export interface SortState {
  /** Column key being sorted */
  column: string | null;
  /** Sort direction */
  direction: SortDirection;
}

export interface DataTableProps<T> {
  /** Array of data items */
  data: T[];
  /** Column definitions */
  columns: Column<T>[];
  /** Loading state - shows skeleton */
  isLoading?: boolean;
  /** Custom empty state content */
  emptyState?: React.ReactNode;
  /** Row click handler */
  onRowClick?: (item: T) => void;
  /** Set of selected item IDs */
  selectedIds?: Set<string>;
  /** Selection change callback */
  onSelectionChange?: (ids: Set<string>) => void;
  /** Function to extract unique ID from item */
  getRowId: (item: T) => string;
  /** Enable sorting functionality */
  sortable?: boolean;
  /** Controlled sort state */
  sortState?: SortState;
  /** Sort change callback */
  onSortChange?: (state: SortState) => void;
  /** Pagination configuration */
  pagination?: PaginationConfig;
  /** Show striped rows */
  striped?: boolean;
  /** Additional class name */
  className?: string;
  /** Number of skeleton rows to show when loading */
  skeletonRows?: number;
}

function SortIcon({ direction }: { direction: SortDirection }) {
  if (direction === 'asc') {
    return <ChevronUp size={14} className="text-primary" />;
  }
  if (direction === 'desc') {
    return <ChevronDown size={14} className="text-primary" />;
  }
  return <ChevronsUpDown size={14} className="text-base-content/40" />;
}

function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
}: PaginationConfig) {
  const totalPages = Math.ceil(total / pageSize);
  const startItem = page * pageSize + 1;
  const endItem = Math.min((page + 1) * pageSize, total);

  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-base-300">
      <div className="text-sm text-base-content/60">
        Showing {startItem} to {endItem} of {total} results
      </div>
      <div className="join">
        <button
          className="join-item btn btn-sm"
          onClick={() => onPageChange(page - 1)}
          disabled={page === 0}
          aria-label="Previous page"
        >
          <ChevronLeft size={16} />
        </button>
        {Array.from({ length: Math.min(totalPages, 5) }).map((_, i) => {
          // Show pages around current page
          let pageNum: number;
          if (totalPages <= 5) {
            pageNum = i;
          } else if (page < 2) {
            pageNum = i;
          } else if (page > totalPages - 3) {
            pageNum = totalPages - 5 + i;
          } else {
            pageNum = page - 2 + i;
          }

          return (
            <button
              key={pageNum}
              className={clsx(
                'join-item btn btn-sm',
                page === pageNum && 'btn-active'
              )}
              onClick={() => onPageChange(pageNum)}
              aria-label={`Page ${pageNum + 1}`}
              aria-current={page === pageNum ? 'page' : undefined}
            >
              {pageNum + 1}
            </button>
          );
        })}
        <button
          className="join-item btn btn-sm"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages - 1}
          aria-label="Next page"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}

export function DataTable<T>({
  data,
  columns,
  isLoading = false,
  emptyState,
  onRowClick,
  selectedIds,
  onSelectionChange,
  getRowId,
  sortable = false,
  sortState,
  onSortChange,
  pagination,
  striped = false,
  className,
  skeletonRows = 5,
}: DataTableProps<T>) {
  // Internal sort state if not controlled
  const [internalSortState, setInternalSortState] = React.useState<SortState>({
    column: null,
    direction: null,
  });

  const currentSortState = sortState ?? internalSortState;
  const handleSortChange = onSortChange ?? setInternalSortState;

  // Selection handlers
  const hasSelection = selectedIds !== undefined && onSelectionChange !== undefined;
  const allSelected = hasSelection && data.length > 0 && data.every(item => selectedIds.has(getRowId(item)));
  const someSelected = hasSelection && data.some(item => selectedIds.has(getRowId(item)));

  const handleSelectAll = React.useCallback(() => {
    if (!onSelectionChange) return;

    if (allSelected) {
      // Deselect all current page items
      const newSelection = new Set(selectedIds);
      data.forEach(item => newSelection.delete(getRowId(item)));
      onSelectionChange(newSelection);
    } else {
      // Select all current page items
      const newSelection = new Set(selectedIds);
      data.forEach(item => newSelection.add(getRowId(item)));
      onSelectionChange(newSelection);
    }
  }, [data, selectedIds, allSelected, onSelectionChange, getRowId]);

  const handleSelectRow = React.useCallback((item: T) => {
    if (!onSelectionChange || !selectedIds) return;

    const id = getRowId(item);
    const newSelection = new Set(selectedIds);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    onSelectionChange(newSelection);
  }, [selectedIds, onSelectionChange, getRowId]);

  const handleSort = React.useCallback((columnKey: string) => {
    const newDirection: SortDirection =
      currentSortState.column === columnKey
        ? currentSortState.direction === 'asc'
          ? 'desc'
          : currentSortState.direction === 'desc'
            ? null
            : 'asc'
        : 'asc';

    handleSortChange({
      column: newDirection ? columnKey : null,
      direction: newDirection,
    });
  }, [currentSortState, handleSortChange]);

  const alignClasses = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
  };

  // Loading state
  if (isLoading) {
    return (
      <div className={clsx('overflow-x-auto', className)}>
        <SkeletonTable
          rows={skeletonRows}
          columns={columns.length + (hasSelection ? 1 : 0)}
          showHeader
        />
      </div>
    );
  }

  // Empty state
  if (data.length === 0) {
    return (
      <div className={className}>
        {emptyState || (
          <EmptyState
            title="No data available"
            description="There are no items to display"
            variant="compact"
          />
        )}
      </div>
    );
  }

  return (
    <div className={clsx('overflow-x-auto', className)}>
      <table className="table w-full">
        <thead>
          <tr>
            {hasSelection && (
              <th className="w-12">
                <Checkbox
                  checked={allSelected}
                  indeterminate={someSelected && !allSelected}
                  onChange={handleSelectAll}
                  aria-label="Select all rows"
                />
              </th>
            )}
            {columns.map((column) => {
              const isSortable = sortable && column.sortable !== false;
              const isSorted = currentSortState.column === column.key;

              return (
                <th
                  key={column.key}
                  className={clsx(
                    alignClasses[column.align ?? 'left'],
                    isSortable && 'cursor-pointer select-none hover:bg-base-200'
                  )}
                  style={{ width: column.width }}
                  onClick={isSortable ? () => handleSort(column.key) : undefined}
                  aria-sort={
                    isSorted
                      ? currentSortState.direction === 'asc'
                        ? 'ascending'
                        : 'descending'
                      : undefined
                  }
                >
                  <div className={clsx(
                    'flex items-center gap-1',
                    column.align === 'center' && 'justify-center',
                    column.align === 'right' && 'justify-end'
                  )}>
                    {column.header}
                    {isSortable && (
                      <SortIcon direction={isSorted ? currentSortState.direction : null} />
                    )}
                  </div>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {data.map((item, index) => {
            const rowId = getRowId(item);
            const isSelected = selectedIds?.has(rowId);

            return (
              <tr
                key={rowId}
                className={clsx(
                  onRowClick && 'cursor-pointer hover:bg-base-200',
                  striped && index % 2 === 1 && 'bg-base-200/50',
                  isSelected && 'bg-primary/10'
                )}
                onClick={onRowClick ? () => onRowClick(item) : undefined}
              >
                {hasSelection && (
                  <td
                    className="w-12"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Checkbox
                      checked={isSelected}
                      onChange={() => handleSelectRow(item)}
                      aria-label={`Select row ${rowId}`}
                    />
                  </td>
                )}
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={alignClasses[column.align ?? 'left']}
                    style={{ width: column.width }}
                  >
                    {column.render(item)}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
      {pagination && <Pagination {...pagination} />}
    </div>
  );
}

DataTable.displayName = 'DataTable';
