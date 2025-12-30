/**
 * Tests for Video API hooks
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import {
  useVideoScripts,
  useVideoScript,
  useRenderQueue,
  useScriptMutations,
  useVideoOverviewData,
  videoQueryKeys,
} from './useVideoApi';

// Mock the video API module
vi.mock('@/api/video', () => ({
  getVideoScripts: vi.fn(),
  getVideoScript: vi.fn(),
  getRenderQueue: vi.fn(),
  getVideoAssets: vi.fn(),
  getMotionComponents: vi.fn(),
  createVideoScript: vi.fn(),
  updateVideoScript: vi.fn(),
  deleteVideoScript: vi.fn(),
  duplicateVideoScript: vi.fn(),
  startRender: vi.fn(),
  downloadRender: vi.fn(),
}));

import * as videoApi from '@/api/video';

// Create wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

describe('videoQueryKeys', () => {
  it('has correct structure', () => {
    expect(videoQueryKeys.scripts).toEqual(['videoScripts']);
    expect(videoQueryKeys.script('test-id')).toEqual(['videoScript', 'test-id']);
    expect(videoQueryKeys.renderQueue).toEqual(['renderQueue']);
    expect(videoQueryKeys.assets).toEqual(['videoAssets']);
    expect(videoQueryKeys.motionComponents).toEqual(['motionComponents']);
  });
});

describe('useVideoScripts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches video scripts', async () => {
    const mockScripts = {
      scripts: [
        { id: 'script-1', name: 'Test Script', scenes: 3, path: '/scripts/test.yaml', language: 'en' },
      ],
      count: 1,
    };
    vi.mocked(videoApi.getVideoScripts).mockResolvedValue(mockScripts);

    const { result } = renderHook(() => useVideoScripts(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockScripts);
    expect(videoApi.getVideoScripts).toHaveBeenCalledOnce();
  });

  it('handles error state', async () => {
    vi.mocked(videoApi.getVideoScripts).mockRejectedValue(new Error('Failed'));

    const { result } = renderHook(() => useVideoScripts(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe('useVideoScript', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches single script when id provided', async () => {
    const mockScript = { id: 'script-1', content: 'test content' };
    vi.mocked(videoApi.getVideoScript).mockResolvedValue(mockScript as any);

    const { result } = renderHook(() => useVideoScript('script-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockScript);
    expect(videoApi.getVideoScript).toHaveBeenCalledWith('script-1');
  });

  it('does not fetch when id is null', () => {
    const { result } = renderHook(() => useVideoScript(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe('idle');
    expect(videoApi.getVideoScript).not.toHaveBeenCalled();
  });
});

describe('useRenderQueue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches render queue', async () => {
    const mockQueue = { jobs: [], active: 0, completed: 0, failed: 0 };
    vi.mocked(videoApi.getRenderQueue).mockResolvedValue(mockQueue);

    const { result } = renderHook(() => useRenderQueue(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockQueue);
  });

  it('enables polling when option set', async () => {
    const mockQueue = { jobs: [], active: 0, completed: 0, failed: 0 };
    vi.mocked(videoApi.getRenderQueue).mockResolvedValue(mockQueue);

    renderHook(() => useRenderQueue({ polling: true }), {
      wrapper: createWrapper(),
    });

    // Polling is configured but we won't test the interval here
    expect(videoApi.getRenderQueue).toHaveBeenCalled();
  });
});

describe('useVideoOverviewData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(videoApi.getVideoScripts).mockResolvedValue({ scripts: [], count: 0 });
    vi.mocked(videoApi.getRenderQueue).mockResolvedValue({ jobs: [], active: 0, completed: 0, failed: 0 });
    vi.mocked(videoApi.getVideoAssets).mockResolvedValue({
      demos: [],
      audio: [],
      graphics: [],
      outputs: [],
    });
  });

  it('combines data from multiple queries', async () => {
    const { result } = renderHook(() => useVideoOverviewData(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.scripts).toEqual([]);
    expect(result.current.queue).toEqual([]);
    expect(result.current.assets).toBeDefined();
    expect(result.current.error).toBeNull();
  });
});

describe('useScriptMutations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns mutation objects', () => {
    const { result } = renderHook(() => useScriptMutations(), {
      wrapper: createWrapper(),
    });

    expect(result.current.create).toBeDefined();
    expect(result.current.update).toBeDefined();
    expect(result.current.remove).toBeDefined();
    expect(result.current.duplicate).toBeDefined();
  });
});
