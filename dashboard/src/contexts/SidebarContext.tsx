import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';

interface SidebarContextType {
  isCollapsed: boolean;
  isMobileOpen: boolean;
  isMobile: boolean;
  toggleSidebar: () => void;
  setCollapsed: (collapsed: boolean) => void;
  openMobileMenu: () => void;
  closeMobileMenu: () => void;
  toggleMobileMenu: () => void;
}

const SidebarContext = createContext<SidebarContextType | null>(null);

const STORAGE_KEY = 'media-engine-sidebar-collapsed';
const MOBILE_BREAKPOINT = 768;
const TABLET_BREAKPOINT = 1024;

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [isCollapsed, setIsCollapsed] = useState(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === 'true';
  });
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== 'undefined' ? window.innerWidth < MOBILE_BREAKPOINT : false
  );

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < MOBILE_BREAKPOINT;
      const tablet = window.innerWidth < TABLET_BREAKPOINT;
      setIsMobile(mobile);

      // Auto-close mobile menu when resizing to desktop
      if (!mobile && isMobileOpen) {
        setIsMobileOpen(false);
      }

      // Auto-collapse on tablet if not already collapsed
      if (tablet && !mobile && !isCollapsed) {
        // Don't auto-collapse, let user control it
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize(); // Initial check
    return () => window.removeEventListener('resize', handleResize);
  }, [isMobileOpen, isCollapsed]);

  // Persist collapsed state and update CSS variable
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, String(isCollapsed));
    document.documentElement.style.setProperty(
      '--sidebar-width',
      isCollapsed ? '56px' : '180px'
    );
  }, [isCollapsed]);

  // Close mobile menu on navigation
  useEffect(() => {
    if (isMobileOpen) {
      document.body.classList.add('mobile-menu-open');
    } else {
      document.body.classList.remove('mobile-menu-open');
    }
  }, [isMobileOpen]);

  const toggleSidebar = useCallback(() => setIsCollapsed(prev => !prev), []);
  const setCollapsed = useCallback((collapsed: boolean) => setIsCollapsed(collapsed), []);
  const openMobileMenu = useCallback(() => setIsMobileOpen(true), []);
  const closeMobileMenu = useCallback(() => setIsMobileOpen(false), []);
  const toggleMobileMenu = useCallback(() => setIsMobileOpen(prev => !prev), []);

  return (
    <SidebarContext.Provider value={{
      isCollapsed,
      isMobileOpen,
      isMobile,
      toggleSidebar,
      setCollapsed,
      openMobileMenu,
      closeMobileMenu,
      toggleMobileMenu,
    }}>
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error('useSidebar must be used within SidebarProvider');
  }
  return context;
}
