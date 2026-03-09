# Phase 3: Layout System - Research

**Researched:** 2026-03-09
**Domain:** Next.js 14 App Router layouts, responsive sidebar, split panels
**Confidence:** HIGH

## Summary

Phase 3 focuses on building a responsive app shell with sidebar navigation, top status bar, route groups for marketing/console separation, and a draggable split panel layout. The project already has Phase 1 (design tokens) and Phase 2 (component library) complete, providing a solid foundation.

**Primary recommendation:** Use shadcn/ui's Sidebar component for navigation, react-resizable-panels for split layouts, and Next.js route groups `(marketing)` and `(console)` to separate public and authenticated sections with different layouts.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LAYT-01 | Responsive sidebar navigation | shadcn/ui Sidebar with collapsible="icon" for desktop, Sheet/drawer pattern for tablet |
| LAYT-02 | Top status bar | Custom header component using existing Card/Button components, sticky positioning |
| LAYT-03 | Route grouping (marketing/console) | Next.js route groups `(marketing)` and `(console)` with separate layout.tsx files |
| LAYT-04 | Root layout Provider wrapping | Consolidate existing providers (ThemeProvider, QueryClientProvider, Toaster) in root layout |
| LAYT-05 | Draggable split panel layout | shadcn/ui Resizable component (built on react-resizable-panels) |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| shadcn/ui Sidebar | Latest | Collapsible sidebar with menu components | Composable, themeable, matches project aesthetic |
| react-resizable-panels | ^2.x | Split panel layouts | Used by shadcn/ui Resizable, accessible, SSR-safe |
| next-themes | ^0.4.6 | Theme management (already installed) | Already in use, proven pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | ^0.363.0 | Sidebar icons | Already installed, consistent iconography |
| @radix-ui/react-slot | ^1.2.4 | Polymorphic components | Already installed, used by sidebar menu buttons |

### Installation
```bash
# Add shadcn/ui sidebar component
npx shadcn@latest add sidebar

# Add shadcn/ui resizable component
npx shadcn@latest add resizable
```

## Architecture Patterns

### Recommended Project Structure
```
src/app/
├── layout.tsx              # Root layout with providers only
├── providers.tsx           # All context providers (existing)
├── globals.css             # Global styles (existing)
├── (marketing)/            # Public routes group
│   ├── layout.tsx          # Marketing layout (minimal header)
│   └── page.tsx            # Home page
├── (console)/              # Authenticated routes group
│   ├── layout.tsx          # Console layout (sidebar + header)
│   └── console/
│       └── page.tsx        # Console page
└── console/                # Keep existing for backward compat during migration

src/components/
├── ui/
│   ├── sidebar.tsx         # shadcn/ui sidebar component
│   └── resizable.tsx       # shadcn/ui resizable component
├── layout/
│   ├── app-sidebar.tsx     # Main sidebar composition
│   ├── header.tsx          # Top status bar
│   └── split-panel.tsx     # Draggable split layout wrapper
├── theme-provider.tsx      # (existing)
└── theme-toggle.tsx        # (existing)
```

### Pattern 1: Route Groups for Layout Separation
**What:** Use `(groupName)` folders to create separate layouts without affecting URLs
**When to use:** When different sections need different UI shells (marketing vs console)

```typescript
// src/app/(marketing)/layout.tsx
export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen">
      <header className="border-b">{/* Minimal header */}</header>
      <main>{children}</main>
    </div>
  )
}

// src/app/(console)/layout.tsx
import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/layout/app-sidebar'
import { Header } from '@/components/layout/header'

export default function ConsoleLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="flex-1">
        <Header />
        {children}
      </main>
    </SidebarProvider>
  )
}
```

Source: https://nextjs.org/docs/app/getting-started/project-structure

### Pattern 2: Sidebar with Collapsible Icons
**What:** Sidebar collapses to icon-only mode on desktop, uses Sheet on mobile
**When to use:** Desktop/tablet app shells with navigation

```typescript
// src/components/layout/app-sidebar.tsx
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
} from '@/components/ui/sidebar'
import { Home, Settings, Terminal } from 'lucide-react'

const navItems = [
  { title: 'Console', url: '/console', icon: Terminal },
  { title: 'Settings', url: '/settings', icon: Settings },
]

export function AppSidebar() {
  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg">
              <Home className="h-4 w-4" />
              <span>StructureClaw</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild tooltip={item.title}>
                    <a href={item.url}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}
```

Source: https://ui.shadcn.com/docs/components/sidebar

### Pattern 3: Split Panel Layout with Resizable
**What:** Draggable divider between content areas
**When to use:** Console with input/output panels, editor layouts

```typescript
// src/components/layout/split-panel.tsx
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable'

interface SplitPanelProps {
  left: React.ReactNode
  right: React.ReactNode
  defaultLayout?: number[]
}

export function SplitPanel({ left, right, defaultLayout = [50, 50] }: SplitPanelProps) {
  return (
    <ResizablePanelGroup
      direction="horizontal"
      defaultLayout={defaultLayout}
      className="h-full"
    >
      <ResizablePanel defaultSize={defaultLayout[0]} minSize={30}>
        {left}
      </ResizablePanel>
      <ResizableHandle withHandle />
      <ResizablePanel defaultSize={defaultLayout[1]} minSize={30}>
        {right}
      </ResizablePanel>
    </ResizablePanelGroup>
  )
}
```

Source: https://github.com/bvaughn/react-resizable-panels

### Pattern 4: Provider Composition in Root Layout
**What:** Single Providers component wrapping all context providers
**When to use:** Root layout needs multiple providers (theme, query, toast)

```typescript
// src/app/providers.tsx (existing - extend this)
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from '@/components/theme-provider'
import { Toaster } from '@/components/ui/toast'
import { SidebarProvider } from '@/components/ui/sidebar'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () => new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 60 * 1000,
          refetchOnWindowFocus: false,
        },
      },
    })
  )

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        {children}
        <Toaster />
      </ThemeProvider>
    </QueryClientProvider>
  )
}
```

### Anti-Patterns to Avoid
- **Don't nest SidebarProvider in route layouts:** Place it at the appropriate level - root for global sidebar, route group for section-specific
- **Don't create multiple root layouts with conflicting html/body tags:** Only one root layout should have `<html>` and `<body>` tags
- **Don't forget suppressHydrationWarning:** Required on `<html>` tag when using next-themes
- **Don't use client components unnecessarily:** Keep layouts as Server Components when possible

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Collapsible sidebar | Custom useState + animation | shadcn/ui Sidebar | Built-in keyboard shortcuts, mobile handling, cookie persistence |
| Split panel resizing | Custom drag handlers | react-resizable-panels | Accessibility, keyboard support, edge cases |
| Route-based layouts | Conditional rendering | Next.js route groups | Cleaner separation, no URL pollution |
| Sidebar state persistence | Manual localStorage | SidebarProvider cookies | SSR-safe, built into component |

**Key insight:** Layout components are deceptively complex - accessibility, keyboard navigation, responsive behavior, and state management all add up. Use battle-tested solutions.

## Common Pitfalls

### Pitfall 1: Multiple Root Layout Conflict
**What goes wrong:** Creating multiple layouts with `<html>` and `<body>` tags causes Next.js errors
**Why it happens:** Next.js requires exactly one root layout with these tags
**How to avoid:** Use route groups for different layouts, but keep single root layout.tsx with html/body tags
**Warning signs:** "Multiple root layouts detected" error in build

### Pitfall 2: Theme Flash on SSR
**What goes wrong:** Page briefly shows wrong theme before JavaScript loads
**Why it happens:** Theme preference not available during SSR
**How to avoid:** Use `suppressHydrationWarning` on html tag, `disableTransitionOnChange` on ThemeProvider
**Warning signs:** White flash on dark mode pages during load

### Pitfall 3: Sidebar Not Persisting State
**What goes wrong:** Sidebar resets to default state on page navigation
**Why it happens:** Sidebar state not persisted across routes
**How to avoid:** Use SidebarProvider's cookie-based persistence with `defaultOpen` from cookies
**Warning signs:** Sidebar always opens/closes on refresh

### Pitfall 4: Resizable Panel Layout Shift
**What goes wrong:** Panels jump to different sizes on initial render
**Why it happens:** Default layout not matching stored preferences, SSR mismatch
**How to avoid:** Use `defaultLayout` prop and consider storing preferences in cookies/localStorage
**Warning signs:** Visible layout shift during page load

### Pitfall 5: Mobile Sidebar Not Accessible
**What goes wrong:** Sidebar unusable on tablet/mobile viewports
**Why it happens:** Desktop-only implementation without mobile considerations
**How to avoid:** Use Sidebar's built-in mobile handling (Sheet component), test at 768px breakpoint
**Warning signs:** Sidebar content cut off or unreachable on smaller screens

## Code Examples

### Complete Console Layout with Sidebar and Header

```typescript
// src/app/(console)/layout.tsx
import { SidebarProvider, SidebarTrigger, SidebarInset } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/layout/app-sidebar'
import { Header } from '@/components/layout/header'
import { cookies } from 'next/headers'

export default async function ConsoleLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const cookieStore = await cookies()
  const defaultOpen = cookieStore.get('sidebar_state')?.value === 'true'

  return (
    <SidebarProvider defaultOpen={defaultOpen}>
      <AppSidebar />
      <SidebarInset>
        <Header />
        <main className="flex-1 p-4">
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
```

### Header with Status Bar Pattern

```typescript
// src/components/layout/header.tsx
'use client'

import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import { ThemeToggle } from '@/components/theme-toggle'
import { usePathname } from 'next/navigation'

export function Header() {
  const pathname = usePathname()

  return (
    <header className="flex h-14 items-center gap-4 border-b px-4">
      <SidebarTrigger />
      <Separator orientation="vertical" className="h-6" />
      <div className="flex-1">
        <h1 className="text-sm font-medium">
          {pathname === '/console' ? 'Agent Console' : 'StructureClaw'}
        </h1>
      </div>
      <ThemeToggle />
    </header>
  )
}
```

### Split Panel for Console Input/Output

```typescript
// Example usage in console page
import { SplitPanel } from '@/components/layout/split-panel'
import { InputPanel } from '@/components/console/input-panel'
import { OutputPanel } from '@/components/console/output-panel'

export default function ConsolePage() {
  return (
    <div className="h-[calc(100vh-3.5rem)]">
      <SplitPanel
        left={<InputPanel />}
        right={<OutputPanel />}
        defaultLayout={[40, 60]}
      />
    </div>
  )
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pages Router _app.js | App Router layout.tsx | Next.js 13+ | Nested layouts, server components |
| Custom sidebar state | SidebarProvider context | shadcn/ui 2024 | Built-in persistence, keyboard shortcuts |
| react-split-pane | react-resizable-panels | 2023+ | Better accessibility, smaller bundle |
| Client-only layouts | Server Component layouts | Next.js 13+ | Better performance, SEO |

**Deprecated/outdated:**
- react-split-pane: Use react-resizable-panels instead (better accessibility, maintained)
- Custom sidebar implementations: Use shadcn/ui Sidebar (composable, feature-complete)

## Open Questions

1. **Should sidebar be visible on marketing pages?**
   - What we know: Marketing pages typically have minimal navigation
   - What's unclear: Whether to use a completely different header or just hide sidebar
   - Recommendation: Use separate layouts via route groups - marketing gets simple header, console gets sidebar

2. **What breakpoint for tablet sidebar behavior?**
   - What we know: shadcn/ui Sidebar uses 768px (md) as default mobile breakpoint
   - What's unclear: Project-specific requirements for tablet vs desktop
   - Recommendation: Use default 768px, test on actual tablet devices during implementation

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.0.18 |
| Config file | vitest.config.ts |
| Quick run command | `npm run test` |
| Full suite command | `npm run test:run` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LAYT-01 | Sidebar collapses/expands on desktop | unit | `vitest run tests/layout/sidebar.test.tsx` | No - Wave 0 |
| LAYT-01 | Sidebar accessible on tablet (Sheet) | unit | `vitest run tests/layout/sidebar.test.tsx` | No - Wave 0 |
| LAYT-02 | Header displays current context | unit | `vitest run tests/layout/header.test.tsx` | No - Wave 0 |
| LAYT-03 | Route groups separate marketing/console | integration | `vitest run tests/layout/route-groups.test.tsx` | No - Wave 0 |
| LAYT-04 | All providers wrapped in root layout | unit | `vitest run tests/layout/providers.test.tsx` | No - Wave 0 |
| LAYT-05 | Split panel supports draggable resize | unit | `vitest run tests/layout/split-panel.test.tsx` | No - Wave 0 |

### Sampling Rate
- **Per task commit:** `npm run test -- --reporter=dot`
- **Per wave merge:** `npm run test:run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/layout/sidebar.test.tsx` - sidebar collapse/expand, mobile behavior
- [ ] `tests/layout/header.test.tsx` - header context display, navigation
- [ ] `tests/layout/split-panel.test.tsx` - resizable panel behavior
- [ ] `tests/layout/route-groups.test.tsx` - layout switching between groups
- [ ] `tests/layout/providers.test.tsx` - provider composition verification
- [ ] Framework setup: Existing Vitest config sufficient, add layout test directory

## Sources

### Primary (HIGH confidence)
- [shadcn/ui Sidebar Documentation](https://ui.shadcn.com/docs/components/sidebar) - component API, usage patterns, theming
- [Next.js Project Structure](https://nextjs.org/docs/app/getting-started/project-structure) - route groups, layout conventions
- [react-resizable-panels GitHub](https://github.com/bvaughn/react-resizable-panels) - API reference, props documentation

### Secondary (MEDIUM confidence)
- [Next.js Route Groups API Reference](https://nextjs.org/docs/app/api-reference/file-conventions/route-groups) - official route group docs
- [Next.js Layouts and Pages](https://nextjs.org/docs/app/getting-started/layouts-and-pages) - layout patterns
- [shadcn/ui Resizable](https://ui.shadcn.com/docs/components/resizable) - wrapper for react-resizable-panels

### Tertiary (LOW confidence)
- Various blog tutorials on Next.js layout patterns (used for cross-validation only)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - shadcn/ui and react-resizable-panels are well-documented, actively maintained
- Architecture: HIGH - Next.js route groups are a core feature, patterns are established
- Pitfalls: HIGH - common issues are well-documented in official sources and community discussions

**Research date:** 2026-03-09
**Valid until:** 30 days - stable patterns, but check for shadcn/ui sidebar updates
