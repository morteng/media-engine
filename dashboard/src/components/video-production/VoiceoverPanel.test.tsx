import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { VoiceoverPanel } from './VoiceoverPanel';

// Mock the hooks
vi.mock('@/hooks/useVideoApi', () => ({
  useVoiceoverStatus: vi.fn(),
  useGenerateVoiceover: vi.fn(),
}));

import { useVoiceoverStatus, useGenerateVoiceover } from '@/hooks/useVideoApi';

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

// Mock implementations
const mockMutate = vi.fn();
const defaultMutationReturn = {
  mutate: mockMutate,
  isPending: false,
  isError: false,
  isSuccess: false,
  data: null,
  error: null,
};

describe('VoiceoverPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock returns
    (useVoiceoverStatus as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: false,
      refetch: vi.fn(),
    });
    (useGenerateVoiceover as ReturnType<typeof vi.fn>).mockReturnValue(defaultMutationReturn);
  });

  it('shows placeholder when no script is selected', () => {
    render(<VoiceoverPanel />, { wrapper: createWrapper() });
    expect(screen.getByText('Select a script to manage voiceover')).toBeInTheDocument();
  });

  it('shows loading state when checking status', () => {
    (useVoiceoverStatus as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: true,
      refetch: vi.fn(),
    });

    render(<VoiceoverPanel scriptId="test-script" />, { wrapper: createWrapper() });
    expect(screen.getByText('Checking status...')).toBeInTheDocument();
  });

  it('shows voiceover exists status', () => {
    (useVoiceoverStatus as ReturnType<typeof vi.fn>).mockReturnValue({
      data: {
        has_voiceover: true,
        has_props: true,
        audio_path: '/path/to/audio.mp3',
        audio_size: 1024000,
        audio_modified: '2024-01-15T10:00:00Z',
      },
      isLoading: false,
      refetch: vi.fn(),
    });

    render(<VoiceoverPanel scriptId="test-script" />, { wrapper: createWrapper() });

    expect(screen.getByText('Voiceover exists')).toBeInTheDocument();
    expect(screen.getByText('Props generated')).toBeInTheDocument();
    expect(screen.getByText(/1000\.0 KB/)).toBeInTheDocument();
  });

  it('shows no voiceover warning', () => {
    (useVoiceoverStatus as ReturnType<typeof vi.fn>).mockReturnValue({
      data: {
        has_voiceover: false,
        has_props: false,
        audio_path: null,
        audio_size: null,
        audio_modified: null,
      },
      isLoading: false,
      refetch: vi.fn(),
    });

    render(<VoiceoverPanel scriptId="test-script" />, { wrapper: createWrapper() });
    expect(screen.getByText('No voiceover generated yet')).toBeInTheDocument();
  });

  it('renders generation mode options', () => {
    render(<VoiceoverPanel scriptId="test-script" />, { wrapper: createWrapper() });

    expect(screen.getByText('Mock (Silent)')).toBeInTheDocument();
    expect(screen.getByText('macOS TTS')).toBeInTheDocument();
    expect(screen.getByText('ElevenLabs')).toBeInTheDocument();
  });

  it('can select generation mode', () => {
    render(<VoiceoverPanel scriptId="test-script" />, { wrapper: createWrapper() });

    const elevenlabsRadio = screen.getByLabelText(/elevenlabs/i);
    fireEvent.click(elevenlabsRadio);

    expect(elevenlabsRadio).toBeChecked();
  });

  it('renders force regenerate checkbox', () => {
    render(<VoiceoverPanel scriptId="test-script" />, { wrapper: createWrapper() });

    expect(screen.getByText('Force regenerate')).toBeInTheDocument();
    expect(screen.getByRole('checkbox')).toBeInTheDocument();
  });

  it('can toggle force regenerate', () => {
    render(<VoiceoverPanel scriptId="test-script" />, { wrapper: createWrapper() });

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).not.toBeChecked();

    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();
  });

  it('renders generate button', () => {
    render(<VoiceoverPanel scriptId="test-script" />, { wrapper: createWrapper() });

    expect(screen.getByRole('button', { name: /generate voiceover/i })).toBeInTheDocument();
  });

  it('shows regenerate when voiceover exists', () => {
    (useVoiceoverStatus as ReturnType<typeof vi.fn>).mockReturnValue({
      data: {
        has_voiceover: true,
        has_props: true,
        audio_path: '/path/to/audio.mp3',
        audio_size: 1024,
        audio_modified: '2024-01-15T10:00:00Z',
      },
      isLoading: false,
      refetch: vi.fn(),
    });

    render(<VoiceoverPanel scriptId="test-script" />, { wrapper: createWrapper() });
    expect(screen.getByRole('button', { name: /regenerate voiceover/i })).toBeInTheDocument();
  });

  it('calls generate mutation on button click', () => {
    render(<VoiceoverPanel scriptId="test-script" />, { wrapper: createWrapper() });

    const generateButton = screen.getByRole('button', { name: /generate voiceover/i });
    fireEvent.click(generateButton);

    expect(mockMutate).toHaveBeenCalledWith(
      { scriptId: 'test-script', mode: 'mock', force: false },
      expect.any(Object)
    );
  });

  it('shows loading state during generation', () => {
    (useGenerateVoiceover as ReturnType<typeof vi.fn>).mockReturnValue({
      ...defaultMutationReturn,
      isPending: true,
    });

    render(<VoiceoverPanel scriptId="test-script" />, { wrapper: createWrapper() });
    expect(screen.getByText('Generating...')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('shows error message on failure', () => {
    (useGenerateVoiceover as ReturnType<typeof vi.fn>).mockReturnValue({
      ...defaultMutationReturn,
      isError: true,
      error: new Error('Generation failed'),
    });

    render(<VoiceoverPanel scriptId="test-script" />, { wrapper: createWrapper() });
    expect(screen.getByText(/failed to generate voiceover/i)).toBeInTheDocument();
  });

  it('shows success message after generation', () => {
    (useGenerateVoiceover as ReturnType<typeof vi.fn>).mockReturnValue({
      ...defaultMutationReturn,
      isSuccess: true,
      data: { status: 'generating', job_id: 'job-123', audio_path: '/path/to/audio.mp3' },
    });

    render(<VoiceoverPanel scriptId="test-script" />, { wrapper: createWrapper() });
    expect(screen.getByText(/voiceover generation started/i)).toBeInTheDocument();
  });

  it('applies className prop correctly', () => {
    const { container } = render(
      <VoiceoverPanel scriptId="test-script" className="custom-class" />,
      { wrapper: createWrapper() }
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('calls onGenerated callback after successful generation', () => {
    const onGenerated = vi.fn();
    const refetchMock = vi.fn();

    (useVoiceoverStatus as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: false,
      refetch: refetchMock,
    });

    // Capture the onSuccess callback
    let capturedOnSuccess: () => void = () => {};
    (useGenerateVoiceover as ReturnType<typeof vi.fn>).mockReturnValue({
      ...defaultMutationReturn,
      mutate: (_params: unknown, options?: { onSuccess?: () => void }) => {
        capturedOnSuccess = options?.onSuccess || (() => {});
      },
    });

    render(<VoiceoverPanel scriptId="test-script" onGenerated={onGenerated} />, {
      wrapper: createWrapper(),
    });

    // Trigger the generation
    const generateButton = screen.getByRole('button', { name: /generate voiceover/i });
    fireEvent.click(generateButton);

    // Simulate successful generation
    capturedOnSuccess();

    expect(refetchMock).toHaveBeenCalled();
    expect(onGenerated).toHaveBeenCalled();
  });
});
