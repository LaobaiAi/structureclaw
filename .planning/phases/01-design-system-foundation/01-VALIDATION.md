---
phase: 1
slug: design-system-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest |
| **Config file** | vitest.config.ts (Wave 0 installs) |
| **Quick run command** | `npm run test -- --run` |
| **Full suite command** | `npm run test` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npm run test -- --run tests/<relevant-file>.test.ts`
- **After every plan wave:** Run `npm run test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | DSGN-01 | unit | `vitest run tests/design-tokens.test.ts` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | DSGN-03 | unit | `vitest run tests/tailwind-config.test.ts` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | DSGN-02 | unit | `vitest run tests/fonts.test.ts` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 1 | DSGN-04 | unit | `vitest run tests/cn-utility.test.ts` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 2 | DSGN-05 | integration | `vitest run tests/theme-switch.test.tsx` | ❌ W0 | ⬜ pending |
| 01-04-02 | 04 | 2 | DSGN-06 | unit | `vitest run tests/accent-color.test.ts` | ❌ W0 | ⬜ pending |
| 01-04-03 | 04 | 2 | DSGN-07 | unit | `vitest run tests/glassmorphism.test.ts` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `vitest.config.ts` — Vitest configuration for Next.js 14
- [ ] `tests/setup.ts` — Test setup with @testing-library/react
- [ ] `tests/design-tokens.test.ts` — CSS variable validation stubs
- [ ] `tests/fonts.test.ts` — Font loading test stubs
- [ ] `tests/tailwind-config.test.ts` — Tailwind config validation stubs
- [ ] `tests/cn-utility.test.ts` — cn() function test stubs
- [ ] `tests/theme-switch.test.tsx` — Theme switching integration test stubs
- [ ] `tests/accent-color.test.ts` — Accent color test stubs
- [ ] `tests/glassmorphism.test.ts` — Glassmorphism class test stubs
- [ ] Framework install: `npm install -D vitest @vitejs/plugin-react @testing-library/react @testing-library/jest-dom jsdom`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Theme flash prevention | DSGN-05 | Visual timing verification | Load page in dark mode, verify no white flash |
| Font rendering quality | DSGN-02 | Visual inspection | Compare Geist Sans/Mono rendering across browsers |
| System theme sync | DSGN-05 | OS integration | Change OS theme preference, verify app follows |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
