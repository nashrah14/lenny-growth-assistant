# UI/UX Design System & Product Design Specification

## Project: The Lenny Growth Assistant
**Document**: `design.md`  
**Aesthetic Vision**: Modern, sleek, high-density professional AI workspace tailored for product and growth leaders.

---

## 1. UX Principles & Aesthetic Foundation

1. **High Information Density with Visual Clarity**: Growth leaders process complex multi-faceted data. The UI presents deep citations, rich Markdown formatting, and rendered artifacts without visual clutter.
2. **Instant Grounding Transparency**: Every factual answer prominently displays its evidence chain. Citations are first-class citizens, represented as clickable source badges that reveal transcript snippets and source links.
3. **Seamless Artifact Co-presence**: Artifacts (calculators, frameworks, essays) render in a dedicated right-hand side panel adjacent to the chat, enabling side-by-side analysis without context switching.
4. **Resilient Feedback & Diagnostic Visibility**: The interface transparently communicates retrieval latency, active model status, and graceful degradation states.

---

## 2. Information Architecture & Layout Structure

```
+---------------------------------------------------------------------------------------------------------+
| [⚡ The Lenny Growth Assistant]                                      [Model: 🤖 Gemini 1.5 Flash ▾] [Status 🟢] |
+-----------------------+---------------------------------------------------+-----------------------------+
| SIDEBAR               | MAIN CONVERSATION AREA                            | ARTIFACT VIEWER (Collapsible)|
|                       |                                                   |                             |
| [+ New Chat]          | 💬 Welcome to The Lenny Growth Assistant          | 📄 Growth Model Calculator  |
|                       |    Ask anything about Lenny's 300+ podcast eps.   | [Preview] [Raw Source] [📋] |
| 🗂️ SESSIONS           |                                                   | --------------------------- |
| • Superhuman PMF      | 👤 User: How does the Superhuman PMF engine work? | [ Interactive Sandboxed   ] |
| • PLG Loops Strategy  |                                                   | [ HTML/CSS / JS Calculator] |
| • B2B Pricing Teardown| 🤖 Assistant: Rahul Vohra's framework focuses on  | [ Component               ] |
| • Brian Chesky 11-Star|    the 40% "very disappointed" metric...          |                             |
|                       |                                                   |                             |
|                       | 📚 SOURCES (2 cited)                              |                             |
|                       | [Rahul Vohra - Superhuman PMF] [Lenny Rachitsky]  |                             |
|                       |                                                   |                             |
|                       | ------------------------------------------------- |                             |
|                       | [ Ask a growth question or generate an essay... ] |                             |
+-----------------------+---------------------------------------------------+-----------------------------+
```

---

## 3. Design Tokens & Visual Hierarchy

### 3.1 Color Palette
- **Background Primary**: `#0B0F17` (Deep Obsidian Dark Mode)
- **Surface Elevation 1 (Cards/Panels)**: `#131B2A`
- **Surface Elevation 2 (Hover/Active)**: `#1E293B`
- **Border Subtle**: `rgba(255, 255, 255, 0.08)`
- **Accent Primary (Lenny Amber/Gold)**: `#F59E0B` (`hsl(38, 92%, 50%)`)
- **Accent Glow**: `rgba(245, 158, 11, 0.15)`
- **Secondary Accent (Cyan/Growth)**: `#06B6D4`
- **Success / Grounded**: `#10B981`
- **Warning / Degraded**: `#F59E0B`
- **Error / Unreachable**: `#EF4444`
- **Text Primary**: `#F8FAFC`
- **Text Secondary**: `#94A3B8`
- **Text Muted**: `#64748B`

### 3.2 Typography
- **Primary Interface Font**: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Code & Raw Artifact Font**: `"JetBrains Mono", "Fira Code", Consolas, monospace`
- **Heading Styles**: Crisp, geometric weighting (600/700) with subtle letter spacing (`-0.02em`).

---

## 4. Key Interaction States & Component Specs

### 4.1 Empty / Onboarding State
- Prompts user with 4 curated quick-start prompts:
  1. *"How did Superhuman measure and optimize Product-Market Fit?"*
  2. *"Write a Ship 30 for 30 essay on Elena Verna's B2B PLG loops."*
  3. *"Create an interactive HTML CAC payback and LTV calculator artifact."*
  4. *"What is Brian Chesky's 11-star experience framework?"*

### 4.2 Streaming & Processing State
- Multi-stage progress indicator showing real-time pipeline status:
  - `Searching 300+ transcripts (Dense + BM25)...`
  - `Reranking top candidates...`
  - `Synthesizing grounded response...`

### 4.3 Grounded Citations Drawer
- Clicking any `[Source: Episode Title]` pill opens an inspection drawer showing:
  - Full Episode Title and Guest Name
  - YouTube URL with timestamp seek link
  - Exact retrieved transcript snippet that grounded the claim
  - Relevance ranking and cosine match score

### 4.4 In-App Artifact Viewer
- **Split-Screen Panel**: 400px–600px resizable or toggleable side panel.
- **Tabs**:
  - **Live Preview**: Sandboxed `<iframe>` rendering HTML/CSS/JS or formatted Markdown.
  - **Raw Code**: Monospace editor view with syntax highlighting and line numbers.
- **Action Toolbar**:
  - `Copy Code` (with visual feedback icon)
  - `Download File` (`.html` or `.md`)
  - `Open in New Tab` (safe blob URL)
  - `Close / Collapse Panel`

### 4.5 No-Evidence & Error States
- Clear, respectful UI banner when a query cannot be answered from the transcripts:
  > *"I couldn't find sufficient evidence in the Lenny transcript knowledge base to answer this reliably. Try asking about product management, growth loops, pricing, or leadership topics discussed on the podcast."*

---

## 5. Accessibility (a11y) & Keyboard Navigation

- **WCAG 2.1 AA Compliance**: All text-to-background contrast ratios exceed `4.5:1` (normal text) and `3:1` (large text/icons).
- **Keyboard Shortcuts**:
  - `Enter`: Send message
  - `Shift + Enter`: New line in composer
  - `Ctrl/Cmd + K`: Focus search / New Chat
  - `Esc`: Close source drawer / Close artifact panel
- **ARIA Attributes**: Proper `role="log"`, `aria-live="polite"`, and `aria-expanded` attributes on all dynamic panels and dropdowns.

---

## 6. Responsive Breakpoints

- **Desktop (> 1280px)**: 3-column full view (Sidebar: 260px, Chat: 1fr, Artifact Viewer: 480px).
- **Tablet (768px – 1279px)**: 2-column view with collapsible sidebar and slide-over artifact panel.
- **Mobile (< 768px)**: Single column with bottom sheet navigation and modal artifact viewer.
