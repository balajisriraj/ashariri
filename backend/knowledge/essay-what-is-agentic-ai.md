---
title: "What Is Agentic AI?"
url: "https://balajisriraj.com/writing/what-is-agentic-ai"
kind: "essay"
---

Most explanations of agentic AI start with autonomy. I think that is the wrong
place to start, because autonomy is the consequence, not the idea.

The idea is simpler. A chatbot takes a question and returns text. An agent takes
a **goal** and returns a **changed world** - a ticket routed, a document filed, a
report produced, a refund issued. Between those two sentences sits almost every
hard problem in the field.

## The three things that make it an agent

An agent needs to decide what to do next, do it, and know whether it worked.

**Tools.** A model that can only write cannot change anything. Give it functions
it can call - query this database, create that ticket, send this email - and
suddenly the output is an action rather than a suggestion. Nearly all of the
engineering effort goes here, into making tools that are hard to misuse.

**Memory.** A single call is stateless. An agent working through a multi-step
task needs to remember what it already tried, what came back, and what it is
still waiting on. Not because memory is elegant, but because without it the
system repeats itself indefinitely.

**A loop with a stopping condition.** Plan, act, observe, decide whether to
continue. The loop is trivial to write and genuinely difficult to bound. An agent
that cannot tell it has failed will keep going until something else stops it.

## Where it actually gets hard

The interesting failures are not model failures.

> A demo has one happy path. Production has a thousand paths, and the model will
> find the ones you did not think about.

- **Partial failure.** Step three of seven succeeds, step four times out. What is
  the state of the world now? Most agent frameworks are much better at starting
  work than at reasoning about half-finished work.
- **Nondeterminism meeting process.** Enterprise processes assume a step either
  happened or did not. A probabilistic step is a category the process has no
  slot for.
- **Ownership.** When an agent gets something wrong, someone has to be
  accountable. Organisations answer this question far more slowly than they
  adopt the technology.

## What I would tell someone starting

Start with a task that is genuinely repetitive, where being wrong is cheap and
detectable. Instrument it heavily before you make it autonomous. Give it fewer
tools than you think it needs.

And measure the thing that matters - not whether the agent completed the loop,
but whether a person's work actually got easier.
