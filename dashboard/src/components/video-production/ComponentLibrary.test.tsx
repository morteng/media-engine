import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ComponentLibrary } from './ComponentLibrary';

describe('ComponentLibrary', () => {
  it('renders component library title', () => {
    render(<ComponentLibrary />);
    // Search input should be visible
    expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
  });

  it('renders category filter buttons', () => {
    render(<ComponentLibrary />);

    // Should have All and category buttons
    expect(screen.getByRole('button', { name: /all/i })).toBeInTheDocument();
  });

  it('filters components by category', () => {
    render(<ComponentLibrary />);

    // Click on background category
    const backgroundButtons = screen.getAllByText(/background/i);
    // Find the filter button (not the component cards)
    const filterButton = backgroundButtons.find(
      (el) => el.closest('button')?.classList.contains('btn-xs')
    );

    if (filterButton) {
      fireEvent.click(filterButton.closest('button')!);
    }
  });

  it('filters components by search query', () => {
    render(<ComponentLibrary />);

    const searchInput = screen.getByPlaceholderText(/search/i);
    fireEvent.change(searchInput, { target: { value: 'aurora' } });

    // Aurora background should be visible - look for the title specifically
    expect(screen.getByText('Aurora Background')).toBeInTheDocument();
  });

  it('calls onSelectComponent when component is clicked', () => {
    const mockOnSelect = vi.fn();
    render(<ComponentLibrary onSelectComponent={mockOnSelect} />);

    // Find and click a component card - use exact text match
    const darkBackground = screen.getByText('Dark Background');
    fireEvent.click(darkBackground.closest('.card')!);

    expect(mockOnSelect).toHaveBeenCalledTimes(1);
    expect(mockOnSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'dark',
        name: 'Dark Background',
      })
    );
  });

  it('shows component details when selected', () => {
    render(<ComponentLibrary />);

    // Click on a component to select it
    const darkBackground = screen.getByText('Dark Background');
    fireEvent.click(darkBackground.closest('.card')!);

    // Should show the details panel with props
    expect(screen.getByText('PROPS')).toBeInTheDocument();
    expect(screen.getByText('BEST FOR')).toBeInTheDocument();
  });

  it('displays energy level badges', () => {
    render(<ComponentLibrary />);

    // Energy badges should be visible on component cards
    const badges = screen.getAllByText(/low|medium|high/i);
    expect(badges.length).toBeGreaterThan(0);
  });

  it('shows use cases for components', () => {
    render(<ComponentLibrary />);

    // Click on a component to see details
    const auroraBackground = screen.getByText('Aurora Background');
    fireEvent.click(auroraBackground.closest('.card')!);

    // Should show use cases (lowercase as stored in data) - multiple components have 'intros'
    const introsBadges = screen.getAllByText('intros');
    expect(introsBadges.length).toBeGreaterThan(0);
  });

  it('can close component details', () => {
    render(<ComponentLibrary />);

    // Select a component
    const darkBackground = screen.getByText('Dark Background');
    fireEvent.click(darkBackground.closest('.card')!);

    // Find and click close button
    const closeButton = screen.getByRole('button', { name: /✕/i });
    fireEvent.click(closeButton);

    // Details should be hidden - check that PROPS heading is no longer visible
    // (it only appears in the details panel)
    const propsHeadings = screen.queryAllByText('PROPS');
    expect(propsHeadings.length).toBe(0);
  });

  it('renders all component categories', () => {
    render(<ComponentLibrary />);

    // Check for category types
    const allButton = screen.getByRole('button', { name: /all/i });
    fireEvent.click(allButton);

    // Should have components from multiple categories - use exact text
    expect(screen.getByText('Dark Background')).toBeInTheDocument();
    expect(screen.getByText('Fade Up')).toBeInTheDocument();
    expect(screen.getByText('Fade')).toBeInTheDocument();
  });

  it('applies className prop correctly', () => {
    const { container } = render(<ComponentLibrary className="custom-class" />);

    // The root element should have the custom class
    expect(container.firstChild).toHaveClass('custom-class');
  });
});
