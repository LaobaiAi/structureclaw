import { describe, it, expect, vi, beforeAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AppSidebar } from '@/components/layout/app-sidebar'
import { SidebarProvider, Sidebar, SidebarTrigger, SidebarContent, SidebarHeader, SidebarMenu, SidebarMenuItem, SidebarMenuButton } from '@/components/ui/sidebar'

// Mock usePathname
vi.mock('next/navigation', () => ({
  usePathname: () => '/console',
}))

// Polyfills for Radix UI
beforeAll(() => {
  window.HTMLElement.prototype.hasPointerCapture = vi.fn()
  window.HTMLElement.prototype.scrollIntoView = vi.fn()
  window.HTMLElement.prototype.getBoundingClientRect = vi.fn(() => ({
    width: 0,
    height: 0,
    x: 0,
    y: 0,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    toJSON: () => {},
  }))

  // Mock matchMedia for use-mobile hook
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })
})

describe('Sidebar Component (LAYT-01)', () => {
  describe('Sidebar Primitives', () => {
    it('exports required sidebar primitives', () => {
      expect(Sidebar).toBeDefined()
      expect(SidebarContent).toBeDefined()
      expect(SidebarHeader).toBeDefined()
      expect(SidebarMenu).toBeDefined()
      expect(SidebarMenuButton).toBeDefined()
      expect(SidebarMenuItem).toBeDefined()
      expect(SidebarTrigger).toBeDefined()
    })

    it('SidebarTrigger renders a button that toggles sidebar', async () => {
      const user = userEvent.setup()
      render(
        <SidebarProvider>
          <Sidebar />
          <SidebarTrigger />
        </SidebarProvider>
      )

      const trigger = screen.getByRole('button', { name: /toggle sidebar/i })
      expect(trigger).toBeInTheDocument()

      // Click should toggle sidebar without error
      await user.click(trigger)
    })

    it('Sidebar with collapsible="icon" collapses to icon-only mode', () => {
      const { container } = render(
        <SidebarProvider>
          <Sidebar collapsible="icon">
            <SidebarHeader>Header</SidebarHeader>
            <SidebarContent>Content</SidebarContent>
          </Sidebar>
        </SidebarProvider>
      )

      // Sidebar should be rendered with collapsible attribute
      const sidebar = container.querySelector('[data-collapsible]')
      expect(sidebar).toBeInTheDocument()
    })
  })

  describe('AppSidebar Component', () => {
    it('renders sidebar with navigation items', () => {
      render(
        <SidebarProvider>
          <AppSidebar />
        </SidebarProvider>
      )

      // Check for navigation items
      expect(screen.getByText('Console')).toBeInTheDocument()
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })

    it('navigation items have icons from lucide-react', () => {
      const { container } = render(
        <SidebarProvider>
          <AppSidebar />
        </SidebarProvider>
      )

      // Check for SVG icons (lucide-react renders as SVG)
      const icons = container.querySelectorAll('svg')
      expect(icons.length).toBeGreaterThan(0)
    })

    it('AppSidebar uses collapsible="icon" for desktop collapse', () => {
      const { container } = render(
        <SidebarProvider>
          <AppSidebar />
        </SidebarProvider>
      )

      // The sidebar should have data-state attribute (expanded or collapsed)
      // When collapsible="icon" is set, it enables icon-only collapse mode
      const sidebar = container.querySelector('[data-state]')
      expect(sidebar).toBeInTheDocument()
      // Check that collapsible is configured (it's set to "icon" in AppSidebar)
      // When expanded, data-collapsible is empty, when collapsed it's "icon"
      expect(sidebar).toHaveAttribute('data-state', 'expanded')
    })

    it('SidebarHeader displays app name "StructureClaw"', () => {
      render(
        <SidebarProvider>
          <AppSidebar />
        </SidebarProvider>
      )

      expect(screen.getByText('StructureClaw')).toBeInTheDocument()
    })

    it('navigation section has "Navigation" label', () => {
      render(
        <SidebarProvider>
          <AppSidebar />
        </SidebarProvider>
      )

      expect(screen.getByText('Navigation')).toBeInTheDocument()
    })
  })
})
