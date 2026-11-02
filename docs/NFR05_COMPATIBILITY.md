# NFR-05: Cross-Browser Compatibility

## 1. Requirement Overview

- **Requirement ID**: NFR-05
- **Category**: Compatibility
- **Priority**: Medium
- **SRS Description**: *The system shall function correctly on commonly used modern web browsers.*
- **Backlog User Story (US-26)**: *As a user, I want the system to work in common browsers so that I can use my own device.*
- **Acceptance Criteria**:
  1. Major functions are tested on commonly used modern browsers (Chrome, Edge, Firefox, and Safari).
  2. Core features work correctly on the browsers tested.
  3. Any browser-specific issues are documented and resolved.

## 2. Supported Browsers Matrix

The Attendance Management System is engineered and verified to support the current and recent versions of the following modern web browsers across desktop and mobile platforms:

| Browser | Engine | Operating Systems | Status | Minimum Tested Baseline |
| :--- | :--- | :--- | :--- | :--- |
| **Google Chrome** | Blink / Chromium | Windows, macOS, Linux, Android | Verified | Chrome 100+ |
| **Microsoft Edge** | Blink / Chromium | Windows, macOS | Verified | Edge 100+ |
| **Mozilla Firefox** | Gecko / SpiderMonkey | Windows, macOS, Linux, Android | Verified | Firefox 100+ |
| **Apple Safari** | WebKit | macOS, iOS, iPadOS | Verified | Safari 15.4+ |

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
- **MIME Sniffing Protection**: `X-Content-Type-Options: nosniff` enforces strict MIME type parsing across Chrome, Edge, Firefox, and Safari.
- **Cookie Security**: Active sessions utilize `SameSite=Lax` and `HttpOnly` attributes, ensuring full cross-browser compatibility with current browser cookie privacy standards (such as Chrome Privacy Sandbox and Safari ITP).
- **File Export Headers (FR-12)**: Downloads for CSV, PDF, and JSON reports emit RFC 6266 `Content-Disposition: attachment; filename="..."` headers with explicit MIME types (`text/csv; charset=utf-8`, `application/pdf`, `application/json`), ensuring seamless handling by native browser download managers.

## 4. Verification and Testing

Automated verification is implemented in `tests/test_nfr05_implementation.py`, covering:
1. Multi-browser User-Agent simulation (Chrome, Edge, Firefox, Safari on Windows, macOS, Linux, Android, iOS).
2. HTML5 doctype, viewport, and `X-UA-Compatible` metadata inspection.
3. HTTP security and compatibility header delivery.
4. CSS vendor property verification (`-webkit-backdrop-filter`, `-moz-osx-font-smoothing`, `text-size-adjust`).
5. JavaScript standards, strict mode, and polyfill verification.
6. Cookie security and `SameSite` flags.
7. Export format download headers and MIME types.
8. End-to-end user workflows executed under each browser persona.
