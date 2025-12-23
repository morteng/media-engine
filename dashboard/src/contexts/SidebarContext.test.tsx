import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { SidebarProvider, useSidebar } from './SidebarContext';
import type { ReactNode } from 'react';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock window.innerWidth
const mockWindowWidth = (width: number) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  });
};

const wrapper = ({ children }: { children: ReactNode }) => (
  <SidebarProvider>{children}</SidebarProvider>
);

describe('SidebarContext', () => {
  const originalInnerWidth = window.innerWidth;

  beforeEach(() => {
    localStorageMock.clear();
    vi.clearAllMocks();
    mockWindowWidth(1024); // Default to desktop
  });

  afterEach(() => {
    mockWindowWidth(originalInnerWidth);
  });

  describe('Initial State', () => {
    it('provides default values', () => {
      const { result } = renderHook(() => useSidebar(), { wrapper });

      expect(result.current.isCollapsed).toBe(false);
      expect(result.current.isMobileOpen).toBe(false);
    });

    it('detects desktop correctly', () => {
      mockWindowWidth(1024);
      const { result } = renderHook(() => useSidebar(), { wrapper });

      expect(result.current.isMobile).toBe(false);
    });

    it('detects mobile correctly', () => {
      mockWindowWidth(375);
      const { result } = renderHook(() => useSidebar(), { wrapper });

      expect(result.current.isMobile).toBe(true);
    });
  });

  describe('Desktop Sidebar Toggle', () => {
    it('toggles collapsed state', () => {
      mockWindowWidth(1024);
      const { result } = renderHook(() => useSidebar(), { wrapper });

      expect(result.current.isCollapsed).toBe(false);

      act(() => {
        result.current.toggleSidebar();
      });

      expect(result.current.isCollapsed).toBe(true);

      act(() => {
        result.current.toggleSidebar();
      });

      expect(result.current.isCollapsed).toBe(false);
    });

    it('setCollapsed sets specific value', () => {
      const { result } = renderHook(() => useSidebar(), { wrapper });

      act(() => {
        result.current.setCollapsed(true);
      });

      expect(result.current.isCollapsed).toBe(true);

      act(() => {
        result.current.setCollapsed(false);
      });

      expect(result.current.isCollapsed).toBe(false);
    });
  });

  describe('Mobile Menu', () => {
    it('opens mobile menu', () => {
      mockWindowWidth(375);
      const { result } = renderHook(() => useSidebar(), { wrapper });

      expect(result.current.isMobileOpen).toBe(false);

      act(() => {
        result.current.openMobileMenu();
      });

      expect(result.current.isMobileOpen).toBe(true);
    });

    it('closes mobile menu', () => {
      mockWindowWidth(375);
      const { result } = renderHook(() => useSidebar(), { wrapper });

      act(() => {
        result.current.openMobileMenu();
      });

      expect(result.current.isMobileOpen).toBe(true);

      act(() => {
        result.current.closeMobileMenu();
      });

      expect(result.current.isMobileOpen).toBe(false);
    });

    it('toggles mobile menu', () => {
      mockWindowWidth(375);
      const { result } = renderHook(() => useSidebar(), { wrapper });

      expect(result.current.isMobileOpen).toBe(false);

      act(() => {
        result.current.toggleMobileMenu();
      });

      expect(result.current.isMobileOpen).toBe(true);

      act(() => {
        result.current.toggleMobileMenu();
      });

      expect(result.current.isMobileOpen).toBe(false);
    });
  });

  describe('LocalStorage Persistence', () => {
    it('persists collapsed state to localStorage', () => {
      const { result } = renderHook(() => useSidebar(), { wrapper });

      act(() => {
        result.current.setCollapsed(true);
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'media-engine-sidebar-collapsed',
        'true'
      );
    });

    it('reads initial state from localStorage', () => {
      localStorageMock.getItem.mockReturnValue('true');

      // Render hook to trigger localStorage read
      renderHook(() => useSidebar(), { wrapper });

      // Initial state should be read from localStorage
      expect(localStorageMock.getItem).toHaveBeenCalledWith('media-engine-sidebar-collapsed');
    });
  });

  describe('Context Provider', () => {
    it('throws error when used outside provider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        renderHook(() => useSidebar());
      }).toThrow('useSidebar must be used within SidebarProvider');

      consoleSpy.mockRestore();
    });

    it('provides all required functions', () => {
      const { result } = renderHook(() => useSidebar(), { wrapper });

      expect(typeof result.current.toggleSidebar).toBe('function');
      expect(typeof result.current.setCollapsed).toBe('function');
      expect(typeof result.current.openMobileMenu).toBe('function');
      expect(typeof result.current.closeMobileMenu).toBe('function');
      expect(typeof result.current.toggleMobileMenu).toBe('function');
    });
  });
});
