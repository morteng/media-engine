import { describe, it, expect, vi } from 'vitest';
import { render, screen, within } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { DataTable, type Column } from './DataTable';

interface TestItem {
  id: string;
  name: string;
  status: string;
  count: number;
}

const testData: TestItem[] = [
  { id: '1', name: 'Item One', status: 'active', count: 10 },
  { id: '2', name: 'Item Two', status: 'inactive', count: 20 },
  { id: '3', name: 'Item Three', status: 'active', count: 30 },
];

const columns: Column<TestItem>[] = [
  { key: 'name', header: 'Name', render: (item) => item.name, sortable: true },
  { key: 'status', header: 'Status', render: (item) => item.status },
  { key: 'count', header: 'Count', render: (item) => item.count, align: 'right' },
];

describe('DataTable', () => {
  it('renders data correctly', () => {
    render(
      <DataTable
        data={testData}
        columns={columns}
        getRowId={(item) => item.id}
      />
    );

    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Count')).toBeInTheDocument();

    expect(screen.getByText('Item One')).toBeInTheDocument();
    expect(screen.getByText('Item Two')).toBeInTheDocument();
    expect(screen.getByText('Item Three')).toBeInTheDocument();
  });

  it('shows loading state with skeleton', () => {
    render(
      <DataTable
        data={[]}
        columns={columns}
        getRowId={(item) => item.id}
        isLoading
      />
    );

    // SkeletonTable renders skeleton elements
    const skeletons = document.querySelectorAll('.skeleton');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('shows empty state when no data', () => {
    render(
      <DataTable
        data={[]}
        columns={columns}
        getRowId={(item) => item.id}
      />
    );

    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  it('shows custom empty state', () => {
    render(
      <DataTable
        data={[]}
        columns={columns}
        getRowId={(item) => item.id}
        emptyState={<div>Custom empty message</div>}
      />
    );

    expect(screen.getByText('Custom empty message')).toBeInTheDocument();
  });

  it('handles row click', async () => {
    const user = userEvent.setup();
    const handleRowClick = vi.fn();

    render(
      <DataTable
        data={testData}
        columns={columns}
        getRowId={(item) => item.id}
        onRowClick={handleRowClick}
      />
    );

    await user.click(screen.getByText('Item One'));

    expect(handleRowClick).toHaveBeenCalledWith(testData[0]);
  });

  it('supports row selection with checkboxes', async () => {
    const user = userEvent.setup();
    const handleSelectionChange = vi.fn();
    const selectedIds = new Set<string>();

    render(
      <DataTable
        data={testData}
        columns={columns}
        getRowId={(item) => item.id}
        selectedIds={selectedIds}
        onSelectionChange={handleSelectionChange}
      />
    );

    // Find checkboxes (one for header + one per row)
    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes).toHaveLength(4); // 1 header + 3 rows

    // Click on first row checkbox
    await user.click(checkboxes[1]);

    expect(handleSelectionChange).toHaveBeenCalledWith(new Set(['1']));
  });

  it('supports select all functionality', async () => {
    const user = userEvent.setup();
    const handleSelectionChange = vi.fn();
    const selectedIds = new Set<string>();

    render(
      <DataTable
        data={testData}
        columns={columns}
        getRowId={(item) => item.id}
        selectedIds={selectedIds}
        onSelectionChange={handleSelectionChange}
      />
    );

    const checkboxes = screen.getAllByRole('checkbox');
    // Click select all (first checkbox)
    await user.click(checkboxes[0]);

    expect(handleSelectionChange).toHaveBeenCalledWith(new Set(['1', '2', '3']));
  });

  it('handles sorting when sortable', async () => {
    const user = userEvent.setup();
    const handleSortChange = vi.fn();

    render(
      <DataTable
        data={testData}
        columns={columns}
        getRowId={(item) => item.id}
        sortable
        onSortChange={handleSortChange}
      />
    );

    // Click on sortable column header
    await user.click(screen.getByText('Name'));

    expect(handleSortChange).toHaveBeenCalledWith({
      column: 'name',
      direction: 'asc',
    });
  });

  it('cycles through sort directions', async () => {
    const user = userEvent.setup();
    const handleSortChange = vi.fn();

    const { rerender } = render(
      <DataTable
        data={testData}
        columns={columns}
        getRowId={(item) => item.id}
        sortable
        sortState={{ column: 'name', direction: 'asc' }}
        onSortChange={handleSortChange}
      />
    );

    // Click again to go to desc
    await user.click(screen.getByText('Name'));

    expect(handleSortChange).toHaveBeenCalledWith({
      column: 'name',
      direction: 'desc',
    });

    // Rerender with desc state and click to clear
    rerender(
      <DataTable
        data={testData}
        columns={columns}
        getRowId={(item) => item.id}
        sortable
        sortState={{ column: 'name', direction: 'desc' }}
        onSortChange={handleSortChange}
      />
    );

    await user.click(screen.getByText('Name'));

    expect(handleSortChange).toHaveBeenCalledWith({
      column: null,
      direction: null,
    });
  });

  it('renders striped rows when enabled', () => {
    render(
      <DataTable
        data={testData}
        columns={columns}
        getRowId={(item) => item.id}
        striped
      />
    );

    const rows = screen.getAllByRole('row');
    // First row is header, so data rows start at index 1
    // Second data row (index 2) should have striped class
    expect(rows[2]).toHaveClass('bg-base-200/50');
  });

  it('renders pagination when provided', () => {
    const handlePageChange = vi.fn();

    render(
      <DataTable
        data={testData}
        columns={columns}
        getRowId={(item) => item.id}
        pagination={{
          page: 0,
          pageSize: 10,
          total: 50,
          onPageChange: handlePageChange,
        }}
      />
    );

    // Pagination shows based on pageSize, not data length
    expect(screen.getByText(/Showing 1 to 10 of 50 results/)).toBeInTheDocument();
    expect(screen.getByLabelText('Previous page')).toBeInTheDocument();
    expect(screen.getByLabelText('Next page')).toBeInTheDocument();
  });

  it('handles pagination navigation', async () => {
    const user = userEvent.setup();
    const handlePageChange = vi.fn();

    render(
      <DataTable
        data={testData}
        columns={columns}
        getRowId={(item) => item.id}
        pagination={{
          page: 1,
          pageSize: 10,
          total: 50,
          onPageChange: handlePageChange,
        }}
      />
    );

    await user.click(screen.getByLabelText('Next page'));
    expect(handlePageChange).toHaveBeenCalledWith(2);

    await user.click(screen.getByLabelText('Previous page'));
    expect(handlePageChange).toHaveBeenCalledWith(0);
  });

  it('disables previous button on first page', () => {
    render(
      <DataTable
        data={testData}
        columns={columns}
        getRowId={(item) => item.id}
        pagination={{
          page: 0,
          pageSize: 10,
          total: 50,
          onPageChange: vi.fn(),
        }}
      />
    );

    expect(screen.getByLabelText('Previous page')).toBeDisabled();
    expect(screen.getByLabelText('Next page')).not.toBeDisabled();
  });

  it('disables next button on last page', () => {
    render(
      <DataTable
        data={testData}
        columns={columns}
        getRowId={(item) => item.id}
        pagination={{
          page: 4,
          pageSize: 10,
          total: 50,
          onPageChange: vi.fn(),
        }}
      />
    );

    expect(screen.getByLabelText('Previous page')).not.toBeDisabled();
    expect(screen.getByLabelText('Next page')).toBeDisabled();
  });

  it('applies column alignment', () => {
    render(
      <DataTable
        data={testData}
        columns={columns}
        getRowId={(item) => item.id}
      />
    );

    // Get the table
    const table = screen.getByRole('table');

    // Find the Count column header and cell - they should have text-right
    const headerCells = within(table).getAllByRole('columnheader');
    const countHeader = headerCells[2]; // Third column
    expect(countHeader).toHaveClass('text-right');
  });

  it('highlights selected rows', () => {
    const selectedIds = new Set(['2']);

    render(
      <DataTable
        data={testData}
        columns={columns}
        getRowId={(item) => item.id}
        selectedIds={selectedIds}
        onSelectionChange={vi.fn()}
      />
    );

    const rows = screen.getAllByRole('row');
    // Row with id '2' is the second data row (index 2 including header)
    expect(rows[2]).toHaveClass('bg-primary/10');
  });

  it('applies cursor-pointer class when onRowClick is provided', () => {
    render(
      <DataTable
        data={testData}
        columns={columns}
        getRowId={(item) => item.id}
        onRowClick={vi.fn()}
      />
    );

    const rows = screen.getAllByRole('row');
    // Data rows should have cursor-pointer
    expect(rows[1]).toHaveClass('cursor-pointer');
  });

  it('renders custom header content', () => {
    const columnsWithCustomHeader: Column<TestItem>[] = [
      {
        key: 'name',
        header: <span data-testid="custom-header">Custom Name</span>,
        render: (item) => item.name,
      },
    ];

    render(
      <DataTable
        data={testData}
        columns={columnsWithCustomHeader}
        getRowId={(item) => item.id}
      />
    );

    expect(screen.getByTestId('custom-header')).toBeInTheDocument();
  });
});
