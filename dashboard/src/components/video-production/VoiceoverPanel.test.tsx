import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { VoiceoverPanel } from './VoiceoverPanel';

// Create a wrapper with QueryClient for tests
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('VoiceoverPanel', () => {
  it('renders voice selection section', () => {
    render(<VoiceoverPanel />, { wrapper: createWrapper() });
    expect(screen.getByText('Voice Selection')).toBeInTheDocument();
  });

  it('renders voice options', () => {
    render(<VoiceoverPanel />, { wrapper: createWrapper() });

    // Should have mock voices available
    expect(screen.getByText('Alex')).toBeInTheDocument();
    expect(screen.getByText('Sarah')).toBeInTheDocument();
  });

  it('can select a voice', () => {
    render(<VoiceoverPanel />, { wrapper: createWrapper() });

    // Click on Sarah voice
    const sarahButton = screen.getByText('Sarah').closest('button');
    fireEvent.click(sarahButton!);

    // Button should be highlighted (btn-primary class)
    expect(sarahButton).toHaveClass('btn-primary');
  });

  it('renders speed control', () => {
    render(<VoiceoverPanel />, { wrapper: createWrapper() });

    // Speed label should be visible
    expect(screen.getByText(/speed/i)).toBeInTheDocument();

    // Should have a range input for speed
    const speedSliders = screen.getAllByRole('slider');
    expect(speedSliders.length).toBeGreaterThan(0);
  });

  it('renders pitch control', () => {
    render(<VoiceoverPanel />, { wrapper: createWrapper() });

    // Pitch label should be visible
    expect(screen.getByText(/pitch/i)).toBeInTheDocument();
  });

  it('renders preview text area', () => {
    render(<VoiceoverPanel />, { wrapper: createWrapper() });

    // Preview text label should be visible
    expect(screen.getByText('Preview Text')).toBeInTheDocument();

    // Textarea should be visible
    const textarea = screen.getByPlaceholderText(/enter text to preview/i);
    expect(textarea).toBeInTheDocument();
  });

  it('can update preview text', () => {
    render(<VoiceoverPanel />, { wrapper: createWrapper() });

    const textarea = screen.getByPlaceholderText(/enter text to preview/i);
    fireEvent.change(textarea, { target: { value: 'Hello world' } });

    expect(textarea).toHaveValue('Hello world');
  });

  it('uses initial text prop', () => {
    render(<VoiceoverPanel text="Initial text content" />, { wrapper: createWrapper() });

    const textarea = screen.getByPlaceholderText(/enter text to preview/i);
    expect(textarea).toHaveValue('Initial text content');
  });

  it('renders preview button', () => {
    render(<VoiceoverPanel />, { wrapper: createWrapper() });

    const previewButton = screen.getByRole('button', { name: /preview/i });
    expect(previewButton).toBeInTheDocument();
  });

  it('disables preview button when no text', () => {
    render(<VoiceoverPanel />, { wrapper: createWrapper() });

    const previewButton = screen.getByRole('button', { name: /preview/i });
    expect(previewButton).toBeDisabled();
  });

  it('enables preview button when text is entered', () => {
    render(<VoiceoverPanel />, { wrapper: createWrapper() });

    const textarea = screen.getByPlaceholderText(/enter text to preview/i);
    fireEvent.change(textarea, { target: { value: 'Some preview text' } });

    const previewButton = screen.getByRole('button', { name: /preview/i });
    expect(previewButton).not.toBeDisabled();
  });

  it('shows word count', () => {
    render(<VoiceoverPanel text="one two three four five" />, { wrapper: createWrapper() });

    // Should show word count
    expect(screen.getByText(/5 words/i)).toBeInTheDocument();
  });

  it('shows estimated duration', () => {
    render(<VoiceoverPanel text="word" />, { wrapper: createWrapper() });

    // Should show estimated duration (format: ~X.Xs)
    const durationElement = screen.getByText(/~\d+\.\d+s/);
    expect(durationElement).toBeInTheDocument();
  });

  it('renders reset button', () => {
    render(<VoiceoverPanel />, { wrapper: createWrapper() });

    // Reset button should be present (has RefreshCw icon)
    const resetButton = screen.getByTitle(/reset to original/i);
    expect(resetButton).toBeInTheDocument();
  });

  it('resets text when reset button clicked', () => {
    render(<VoiceoverPanel text="Original text" />, { wrapper: createWrapper() });

    const textarea = screen.getByPlaceholderText(/enter text to preview/i);

    // Change the text
    fireEvent.change(textarea, { target: { value: 'Modified text' } });
    expect(textarea).toHaveValue('Modified text');

    // Click reset
    const resetButton = screen.getByTitle(/reset to original/i);
    fireEvent.click(resetButton);

    // Should reset to original
    expect(textarea).toHaveValue('Original text');
  });

  it('shows voice language and gender info', () => {
    render(<VoiceoverPanel />, { wrapper: createWrapper() });

    // Should show language info for voices
    expect(screen.getAllByText(/en-US|en-GB/i).length).toBeGreaterThan(0);
  });

  it('applies className prop correctly', () => {
    const { container } = render(
      <VoiceoverPanel className="custom-class" />,
      { wrapper: createWrapper() }
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('adjusts speed slider', () => {
    render(<VoiceoverPanel />, { wrapper: createWrapper() });

    const speedSliders = screen.getAllByRole('slider');
    const speedSlider = speedSliders[0];

    fireEvent.change(speedSlider, { target: { value: '1.5' } });
    expect(speedSlider).toHaveValue('1.5');
  });

  it('adjusts pitch slider', () => {
    render(<VoiceoverPanel />, { wrapper: createWrapper() });

    const pitchSliders = screen.getAllByRole('slider');
    const pitchSlider = pitchSliders[1];

    fireEvent.change(pitchSlider, { target: { value: '1.2' } });
    expect(pitchSlider).toHaveValue('1.2');
  });
});
