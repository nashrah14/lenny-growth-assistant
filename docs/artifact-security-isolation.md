# Artifact Security & Sandbox Isolation Architecture

## 1. Overview & Threat Model

The Lenny Growth Assistant supports dynamic synthesis of two categories of artifacts:
1. **Interactive HTML/CSS/JavaScript components** (e.g., CAC payback calculators, retention curve visualizers, growth matrix models).
2. **Comprehensive Markdown strategy documents** (e.g., product launch playbooks, frameworks teardowns).

### Threat Model: Untrusted LLM-Generated Markup
Because generated HTML/JS originates from LLM generation (which could be influenced by prompt injection, malicious transcript excerpts, or hallucinations), **all generated markup is treated as untrusted**.

Without rigorous multi-layer isolation, untrusted HTML rendered in the client's browser could lead to:
- **Cross-Site Scripting (XSS)**: Execution of malicious scripts in the application's origin context.
- **Session & Token Exfiltration**: Accessing `document.cookie` (session tokens) or `localStorage`.
- **API Impersonation (CSRF / Stolen Context)**: Issuing authenticated `fetch()` requests to `/api/v1/*` using the user's active session.
- **Parent Window Hijacking**: Redirecting the top-level tab to a phishing or malicious landing page via `window.top.location`.
- **Data Exfiltration / Phone-Home**: Making unauthorized outbound network connections to attacker-controlled command-and-control servers.

---

## 2. Multi-Layer Defense-in-Depth Isolation Strategy

We implement a three-tier defense-in-depth architecture:

```
+-------------------------------------------------------------------------+
| Layer 1: Backend Bleach Sanitization & CSP Meta Injection                |
| - Strips <object>, <embed>, <iframe>, and `javascript:` URIs            |
| - Neutralizes inline `on*` event handlers (onerror, onload, etc.)       |
| - Injects strict Content-Security-Policy (CSP) meta header              |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| Layer 2: Frontend HTML5 Sandboxed <iframe> (`origin: null`)             |
| - Rendered via <iframe sandbox="allow-scripts" srcdoc={...} />          |
| - STRICTLY OMITS `allow-same-origin`                                    |
| - STRICTLY OMITS `allow-top-navigation`                                 |
| - STRICTLY OMITS `allow-popups` & `allow-modals`                        |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| Layer 3: Content Security Policy (CSP) Policy Enforcement               |
| - default-src 'none'                                                    |
| - connect-src 'none' (blocks outbound fetch / XHR / beacon)             |
| - style-src 'unsafe-inline' https://fonts.googleapis.com                |
| - font-src https://fonts.gstatic.com                                    |
| - img-src data: https: blob:                                            |
| - script-src 'unsafe-inline'                                            |
+-------------------------------------------------------------------------+
```

---

## 3. Specification: What the Viewer Permits, Blocks, and Why

### A. What the Viewer Permits

| Capability | Permitted Scope | Technical Rationale |
| :--- | :--- | :--- |
| **HTML5 Layout & Tables** | `div`, `span`, `p`, `h1`-`h6`, `table`, `ul`, `ol`, `section`, `article`, etc. | Allows rich product dashboards, matrices, and teardown layouts. |
| **Interactive Form Controls** | `input`, `button`, `select`, `option`, `textarea`, `label`, `progress`, `meter` | Required for interactive calculation inputs (e.g., CAC, ARPU, churn sliders). |
| **Local Interactivity & Calculation** | Inline `<script>` execution restricted to the sandboxed DOM. | Enables instant calculation and UI reactivity (e.g. updating calculated ROI on input change). |
| **Vector & Canvas Graphics** | `<svg>`, `<canvas>`, `<path>`, `<circle>`, `<rect>` | Enables dynamic charts, growth curves, and diagrams. |
| **Modern Dark-Mode Styling** | Inline CSS, CSS variables, Google Fonts (`fonts.googleapis.com`). | Ensures artifacts blend seamlessly into the aesthetic UI. |
| **Markdown Rendering** | GitHub-Flavored Markdown (GFM) via `react-markdown`. | Safe formatting of text documents, tables, lists, and code blocks. |

---

### B. What the Viewer Blocks

| Attack Vector / Capability | Status | Enforcement Mechanism | Security Rationale |
| :--- | :--- | :--- | :--- |
| **Parent DOM & Cookie Access** | **BLOCKED** | Omitting `allow-same-origin` on `<iframe>` sandbox | The iframe receives a distinct `null` origin. Even if malicious script runs, `window.parent.document` and `document.cookie` throw `DOMException: Blocked a frame with origin "null" from accessing a cross-origin frame`. |
| **Session Token Theft** | **BLOCKED** | `null` origin + `HttpOnly` JWT Cookies | JavaScript in the sandbox cannot read `localStorage` or `HttpOnly` auth cookies. |
| **Authenticated API Abuse** | **BLOCKED** | `null` origin + CSP `connect-src 'none'` | Sandboxed scripts cannot make valid authenticated requests to `/api/v1/*` because cookies are not shared with `null` origin and network connectivity is blocked. |
| **Top-Level Navigation Hijack** | **BLOCKED** | Omitting `allow-top-navigation` on `<iframe>` sandbox | Prevents `window.top.location = "http://evil.com"` from redirecting the user away from the app. |
| **Outbound Data Exfiltration** | **BLOCKED** | `connect-src 'none'` inside injected CSP header | Prevents `fetch()`, `XMLHttpRequest`, `WebSocket`, or `navigator.sendBeacon()` from sending user input to external servers. |
| **Plugin Vulnerabilities** | **BLOCKED** | Server-side Bleach stripping of `<object>`, `<embed>`, `<iframe>` + `default-src 'none'` | Eliminates Flash, ActiveX, and nested iframe exploits. |
| **Malicious URI Protocols** | **BLOCKED** | Regex / Bleach stripping of `javascript:` protocol links | Prevents link-based script invocation. |

---

## 4. Evaluator Verification Steps

1. **Visual Inspection**:
   - In the frontend chat, ask for an artifact (e.g., *"Create an interactive CAC Payback Calculator in HTML"* or click **Generate Artifact**).
   - The Artifact Viewer opens automatically in the right pane beside the conversation.
   - Click the green **Sanitized Sandbox** badge in the viewer header to view the live security breakdown.
   - Switch between **Live Preview** and **Raw Source** tabs, or click **Copy** / **Export**.

2. **Security Automated Tests**:
   - Run backend security tests:
     ```bash
     python -m pytest backend/tests/test_sanitizer.py
     ```
   - Tests verify that `<script>` tags in markdown are stripped, `onerror` event handlers are removed, `javascript:` pseudo-protocols are blocked, and CSP meta headers are injected.
