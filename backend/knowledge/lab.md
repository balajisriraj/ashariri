---
title: "The Lab"
url: "https://balajisriraj.com/#lab"
kind: "lab"
---

# About the Lab
Ten side products where I push agentic patterns past the demo, each in its own GitHub repository.

# Ashariri
Ashariri (Building) - A digital twin that talks and thinks like me. A personal twin that answers in my voice - grounded in my writing, work and opinions, with long-term memory and firm boundaries on what it will and won't say. It will power the chat on this site.
Orchestration: Persona router with specialist sub-agents. Memory: Episodic + semantic, consent-scoped. Evals: Persona fidelity and refusal tests. Stack: Claude, LangGraph, FastAPI, pgvector.

# PaperSensei
PaperSensei (Planned) - Understand any research paper in an evening. Upload a paper and an AI tutor rebuilds it as a guided lesson - plain-language walkthroughs, generated diagrams, a glossary, and a chat grounded in the paper's own sections.
Orchestration: Curriculum planner → explainer + visualiser. Memory: Section-level index of the paper. Evals: Grounding checks on every answer. Stack: Claude, FastAPI, React, Python.

# VibeLens
VibeLens (Planned) - Watch less. Know more. Paste a video link to get the transcript, a summary and the moments that matter - then chat with the video, and every answer jumps straight to its timestamp.
Orchestration: Linear pipeline + chat agent. Memory: Timestamped transcript chunks. Evals: Citation accuracy to the second. Stack: Claude, pgvector, FastAPI, React.

# TikGenie
TikGenie (Building) - Support that runs itself, where customers already are. An agentic ticketing suite. Customers raise and track tickets over WhatsApp and other messengers; agents triage, route and resolve the routine tail, and escalate the rest with full context.
Orchestration: Intake → triage → resolver graph. Memory: Ticket history + knowledge base. Evals: Resolution quality and SLA tracking. Stack: LangGraph, FastAPI, WhatsApp Cloud API, Postgres, Redis.

# FinGenie
FinGenie (Building) - Your books, in conversation. A PWA that sits on top of Tally Prime. Ask questions of your accounts, automate routine entries and get proactive alerts on cash, dues and anomalies - with a sync layer that repairs itself.
Orchestration: Analyst + alerts agents over SQL tools. Memory: Local ledger mirror. Evals: Numbers reconciled against source. Stack: TypeScript, React PWA, Python, SQLite.

# SkillSmith
SkillSmith (Planned) - Turn know-how into agent skills. A chat that interviews you about a workflow, then writes, tests and packages it as an Agent Skill bundle for Claude, Cowork, Gemini Enterprise and similar platforms.
Orchestration: Interviewer → drafter → tester loop. Memory: Your examples and documents. Evals: Generated test cases per skill. Stack: Claude Agent SDK, TypeScript, FastAPI, React.

# ClauseVault
ClauseVault (Planned) - Contract intelligence that never leaves your machine. A local-first contract lifecycle engine: intake, clause review against your own playbook, redlines, obligations and renewals - all on local models.
Orchestration: Clause, obligation and redline agents. Memory: Your playbook + contract register. Evals: Clause-level citations on every flag. Stack: Ollama, LangGraph, Python, SQLite.

# FlowMind
FlowMind (Planned) - Describe the process. Get the automation. Intelligent process automation by conversation. Explain a process in plain words and an agent designs the workflow, wires the tools, dry-runs it and deploys it with monitoring.
Orchestration: Analyst → designer with sandbox loop. Memory: Tool registry of MCP servers. Evals: Dry runs before any deploy. Stack: LangGraph, MCP, FastAPI, React.

# Charmly
Charmly (Planned) - Better replies, in your own voice. A browser companion for WhatsApp Web that reads the context and tone of a conversation and suggests playful, charming replies you can send, edit or ignore.
Orchestration: Context → tone → writer chain. Memory: Your past replies for style. Evals: Tone match and safety filter. Stack: Chrome MV3, TypeScript, Claude.

# DebateDojo
DebateDojo (Planned) - Spar with an AI that argues back. Pick a topic and a side; the AI takes the other and argues properly. Then it scores your reasoning, evidence and rebuttals, and shows exactly where to improve.
Orchestration: Opponent, fact-checker, judge and coach. Memory: Full debate log per session. Evals: Rubric scoring with explanations. Stack: Claude, LangGraph, FastAPI, React.
