# NFR-05: Cross-Browser Compatibility

## 1. Requirement Overview

- **Requirement ID**: NFR-05
- **Category**: Compatibility
- **Priority**: Medium
- **SRS Description**: *The system shall function correctly on commonly used modern web browsers.*
- **Backlog User Story (US-26)**: *As a user, I want the system to work in common browsers so that I can use my own device.*
- **Backlog acceptance criterion (US-26)**: *Works correctly in current Chrome, Edge and Firefox.*
- **GitHub issue #20 acceptance criteria**:
  1. Major functions are tested on commonly used modern browsers.
  2. Core features work correctly on the browsers tested.
  3. Any browser-specific issues are documented and resolved.

## 2. Supported Browsers Matrix

US-26 names the target browsers: current Chrome, Edge and Firefox. Each one is
exercised in its real engine by `tests/test_nfr05_browser_compatibility.py`.

| Browser | Engine | How it is tested | Where it runs |
| :--- | :--- | :--- | :--- |
| **Google Chrome** (current stable) | Blink | Playwright channel `chrome` | Locally and in GitHub Actions |
| **Microsoft Edge** (current stable) | Blink | Playwright channel `msedge` | Locally and in GitHub Actions |
| **Mozilla Firefox** (current, Playwright build) | Gecko | Playwright `firefox` | GitHub Actions (and locally where it can be installed) |

Safari is not part of the SRS or backlog criteria and is not tested. The CSS
`-webkit-` prefixes below are kept for WebKit, but Safari support is not
claimed.

## 3. Compatibility Design & Implementation Standards

### 3.1 HTML5 & Document Standards
- **Standard HTML5 Doctype**: All server-rendered templates (`base.html`, `login.html`) begin with `<!DOCTYPE html>` ensuring browsers trigger W3C standards mode rather than quirks mode.
- **Character Encoding**: `<meta charset="UTF-8">` is specified in `<head>`, and the backend emits `Content-Type: text/html; charset=utf-8` on all HTML responses to prevent encoding heuristics from misinterpreting characters across different browser locales.
- **Responsive Viewport**: `<meta name="viewport" content="width=device-width, initial-scale=1.0">` ensures proper scaling and touch interactions on desktop, tablet, and mobile browsers.
- **Edge Standards Mode**: `<meta http-equiv="X-UA-Compatible" content="IE=edge">` and the HTTP header `X-UA-Compatible: IE=edge` prevent Microsoft Edge / Chromium from falling back into legacy emulation modes.
- **Semantic Structure**: All pages utilize standardized semantic landmarks (`<aside>`, `<header>`, `<main>`, `<nav>`, `<dialog>`, `<template>`) fully recognized by modern browser accessibility trees and layout engines.

### 3.2 Cross-Browser CSS Techniques
- **Font Smoothing**: Configured with both WebKit and Gecko declarations:
  - `-webkit-font-smoothing: antialiased;` (Chrome, Edge, Safari)
  - `-moz-osx-font-smoothing: grayscale;` (Firefox on macOS)
- **Text Size Adjustment**: Configured with both vendor-prefixed and standard declarations:
  - `-webkit-text-size-adjust: 100%;`
  - `text-size-adjust: 100%;`
- **Backdrop Filters**: Translucent navigation elements and dialog backdrops apply both `-webkit-backdrop-filter` and `backdrop-filter` to support WebKit/Safari as well as Blink and modern Gecko engines.
- **Fluid Layout**: Modern CSS Grid and Flexbox layouts adhere strictly to W3C specifications without legacy box-model hacks.
- **Keyboard & Motion Accessibility**: Interactive elements utilize `:focus-visible` for keyboard navigation and respect `@media (prefers-reduced-motion: reduce)` across all conforming browsers.

### 3.3 Cross-Browser JavaScript (ECMAScript 2020+)
- **Strict Mode**: `"use strict";` is enforced across all client scripts (`common.js`, `login.js`, `admin.js`, `teacher.js`, `student.js`).
- **Standard Fetch API**: All REST communication uses `window.fetch()` with `credentials: "same-origin"` and standard JSON payloads, supported natively by 100% of modern browsers.
- **DOM Polyfills & Guards**:
  - `Element.prototype.replaceChildren`: Polyfilled for older browser baselines to cleanly swap DOM nodes without innerHTML risks.
  - `Element.prototype.toggleAttribute`: Polyfilled to ensure standard boolean attribute toggling (`aria-invalid`, etc.).
- **Dialog Modal Handling**: The native HTML5 `<dialog>` element is utilized for confirmation prompts and password changes, with defensive guards checking `typeof dialog.showModal === "function"` and providing attribute-based fallbacks where necessary.
- **Timezone-Agnostic Date Construction**: ISO 8601 date strings (`YYYY-MM-DD`) are decomposed into discrete numerical components `[year, month, day]` when creating `Date` objects, preventing Safari and Firefox timezone-offset parsing discrepancies.

### 3.4 HTTP Headers & Security Alignment
- **Content-Security-Policy (CSP)**: `default-src 'self'; frame-ancestors 'none'` ensures that all JavaScript, CSS, SVGs, and fonts load from the application origin, eliminating cross-origin script blocking or mixed-content errors in strict browsers.
- **MIME Sniffing Protection**: `X-Content-Type-Options: nosniff` enforces strict MIME type parsing across Chrome, Edge, Firefox, and Firefox.
- **Fixed script and style types**: the app's `after_request` hook sets static `.js` responses to `text/javascript` (RFC 9239) and `.css` to `text/css` (`STATIC_MIME_TYPES` in `app/__init__.py`). Without this, Flask takes these types from the host's MIME table (`/etc/mime.types` or the Windows registry), which differs between machines: GitHub Actions served `application/javascript` while the tests expect `text/javascript`. A host that maps `.js` to `text/plain` would make every browser refuse the scripts because of `nosniff`. `test_nfr05_static_types_do_not_depend_on_host_mime_table` simulates that broken mapping.
- **Cookie Security**: Active sessions utilize `SameSite=Lax` and `HttpOnly` attributes, ensuring full cross-browser compatibility with current browser cookie privacy standards (such as Chrome Privacy Sandbox and Safari ITP).
- **File Export Headers (FR-12)**: Downloads for CSV, PDF, and JSON reports emit RFC 6266 `Content-Disposition: attachment; filename="..."` headers with explicit MIME types (`text/csv; charset=utf-8`, `application/pdf`, `application/json`), ensuring seamless handling by native browser download managers.

## 4. Verification and Testing

### 4.1 Real-browser tests (primary evidence)

`tests/test_nfr05_browser_compatibility.py` starts the real application on a
local port and drives Chrome, Edge and Firefox through Playwright. The same
tests run in every browser:

| Test | Major function exercised |
| :--- | :--- |
| `test_login_page_validation_and_role_redirect` | Standards mode, UTF-8, empty-form validation, password toggle, wrong-password error, `fetch` login and role redirect |
| `test_teacher_marks_corrects_attendance_and_logs_out` | Hash navigation, `<select>` and `<input type="date">`, marking a roster, saving (checked in SQLite), correcting a record in a `<dialog>`, logging out through the confirm dialog, protected page after logout |
| `test_student_views_own_attendance` | Overview percentage (3 of 4 = 75%), counts and history table |
| `test_admin_creates_user_through_dialog` | New-user form dialog and the stored user |
| `test_dashboard_layout_has_no_horizontal_overflow` | 1280px desktop and 375px phone widths, mobile menu toggle |
| `test_report_tested_browser_versions` | Confirms every selected browser actually ran and prints its version |

Every test also fails if the page throws an uncaught JavaScript error or logs a
console error in that browser.

```bash
python -m playwright install chromium firefox chrome msedge
python -m pytest tests/test_nfr05_browser_compatibility.py -v -s
# Run a subset, e.g. where one browser cannot be installed:
NFR05_BROWSERS=chrome,edge python -m pytest tests/test_nfr05_browser_compatibility.py -v -s
```

GitHub Actions installs Firefox and uses the Chrome and Edge builds on the
runner (installing them if missing), so all three browsers run on every push
and pull request.

### 4.2 HTTP-level checks

`tests/test_nfr05_implementation.py` checks the markup, headers, assets and
API through Flask's test client, covering:
1. Requests sent with different browser User-Agent strings get the same responses. These are simulations, not real browsers.
2. HTML5 doctype, viewport, and `X-UA-Compatible` metadata inspection.
3. HTTP security and compatibility header delivery.
4. CSS vendor property verification (`-webkit-backdrop-filter`, `-moz-osx-font-smoothing`, `text-size-adjust`).
5. JavaScript standards, strict mode, and polyfill verification.
6. Cookie security and `SameSite` flags.
7. Export format download headers and MIME types.
8. End-to-end user workflows executed under each browser persona.

## 5. Assumptions and Limitations

- "Current" Chrome, Edge and Firefox means the stable releases available when
  the tests run. The tests print the exact versions, and older versions are
  not covered.
- Safari, mobile browser apps and assistive technology are not covered by the
  SRS or backlog criteria and are not tested here. The 375px test checks the
  responsive layout in desktop engines, not on real phones.
- No browser-specific defects were found in the real-browser runs. One
  host-specific issue was found and fixed: the served type of `.js` files
  depended on the host's MIME table (see section 3.4).
