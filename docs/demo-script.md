# Hiring Demo Video Script (2-3 Minutes)

## The Lenny Growth Assistant
**Presenter**: Candidate (Forward Deployed Engineer)  
**Format**: 2–3 Minute Screen Recording with Camera Enabled  
**Goal**: Demonstrate customer/product judgment, robust technical execution, RAG grounding, Ship 30 essay generation, and sandboxed artifact rendering.

---

## ⏱️ Video Timeline Breakdown

| Timestamp | Phase | Screen View | Spoken Talking Points & Actions |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:30** | **Discovery & Problem Framing** | Camera + UI Overview (`http://localhost:5173`) | *"Hi, I'm presenting The Lenny Growth Assistant. Growth leaders and PMs often spend hours sifting through podcast episodes to find actionable playbooks. I built this full-stack assistant to turn 300+ Lenny's Podcast transcripts into instant, strictly grounded answers, Ship 30 essays, and live interactive artifacts without prompt friction."* |
| **0:30 – 1:00** | **Grounded RAG & Source Traceability** | Conversation Screen | *Click quick prompt or type: "How did Superhuman measure and optimize Product-Market Fit?"*<br>*"Notice the real-time hybrid retrieval combining dense semantic search, BM25 keyword matching, Reciprocal Rank Fusion, and cross-encoder reranking. The answer accurately quotes Rahul Vohra's 40% rule. When I click this source badge, we see the exact transcript snippet, guest name, and timestamped YouTube link."* |
| **1:00 – 1:40** | **Ship 30 Skill & Sandboxed Artifacts** | Split Screen (Chat + Artifact Viewer) | *Type: "Generate an interactive CAC payback and LTV calculator artifact for a B2B SaaS startup."*<br>*"The assistant deterministically routes to the Artifact skill and generates an interactive tool. Look at the right panel—the artifact renders natively inside a sandboxed iframe with strict CSP and server-side Bleach sanitization to prevent XSS. I can toggle between Live Preview and Raw Code, copy it, or export it."* |
| **1:40 – 2:15** | **Model Abstraction & Local Ollama** | Model Switcher in Header | *"In the top bar, I can toggle between Google Gemini and our local/remote Ollama model without touching code. Let's switch to Ollama and ask a follow-up. The provider abstraction ensures seamless fallback and identical grounding guarantees across cloud and local inference."* |
| **2:15 – 2:45** | **Technical Trade-off & Architecture** | Architecture Diagram / Terminal | *"One key architectural trade-off I made was using Reciprocal Rank Fusion (RRF) over direct score summation. In podcast transcripts, dense models excel at conceptual themes like 'retention loops', while BM25 nails guest names and company jargon like 'Elena Verna PLG'. RRF normalizes both ranking distributions without arbitrary coefficient tuning. Everything is backed by PostgreSQL for state and Qdrant Cloud for vectors."* |
| **2:45 – 3:00** | **Wrap Up** | Camera | *"The repository is fully reproducible via Docker Compose and single-command local setup, with 100% test coverage for critical paths. Thank you!"* |
