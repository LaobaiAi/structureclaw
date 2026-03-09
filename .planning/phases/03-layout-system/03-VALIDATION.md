---
phase: 03
slug: layout-system
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.0.18 |
| **Config file** | frontend/vitest.config.ts |
| **Quick run command** | `npm run test` |
| **Full suite command** | `npm run test:run` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npm run test`
- **After every plan wave:** Run `npm run test:run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | LAYT-01 | component | `npm run test -- sidebar` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | LAYT-02 | component | `npm run test -- header` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | LAYT-03 | integration | `npm run test -- route-groups` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 2 | LAYT-04 | integration | `npm run test -- providers` | ✅ exists | ⬜ pending |
| 03-03-01 | 03 | 3 | LAYT-05 | component | `npm run test -- split-panel` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/tests/components/sidebar.test.tsx` — stubs for LAYT-01
- [ ] `frontend/tests/components/header.test.tsx` — stubs for LAYT-02
- [ ] `frontend/tests/components/split-panel.test.tsx` — stubs for LAYT-05
- [ ] `frontend/tests/integration/route-groups.test.tsx` — stubs for LAYT-03
- [ ] `frontend/tests/integration/providers.test.tsx` — stubs for LAYT-04

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Sidebar collapse animation smoothness | LAYT-01 | Visual timing | Collapse sidebar, verify animation is smooth |
| Split panel drag responsiveness | LAYT-05 | Interaction feel | Drag panel divider, verify responsive feedback |
| Mobile sidebar gesture | LAYT-01 | Touch interaction | On tablet viewport, verify swipe opens sidebar |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
