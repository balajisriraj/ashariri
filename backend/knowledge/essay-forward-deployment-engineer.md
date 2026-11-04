---
title: "What Does a Forward Deployment Engineer Do?"
url: "https://balajisriraj.com/writing/forward-deployment-engineer"
kind: "essay"
---

The short version: a forward deployment engineer takes something that works and
makes it work *there* - inside a specific business, with its specific data,
processes, constraints and people.

It is not support, and it is not consulting. Support fixes what is broken.
Consulting advises and leaves. Forward deployment builds the last mile, and the
last mile is usually longer than the rest of the road.

## Why the role exists at all

A product team optimises for the general case. That is correct - it is what
makes a product a product rather than a series of bespoke builds.

But the general case does not exist anywhere. Every business unit has a system
of record nobody documented, a process that works for reasons nobody remembers,
and a team whose trust you have not earned yet. Somebody has to stand in that
gap. If nobody does, you get the familiar outcome: a platform that demos
brilliantly and is used by four people.

## What the work actually looks like

**Weeks one to two - understand the real process.** Not the documented one. Sit
with the people doing the work and watch what they actually do, including the
spreadsheet they maintain on the side because the official system is too slow.

**Weeks three to six - make it fit.** Data mapping, edge cases, the integration
nobody scoped. This is where most of the engineering happens, and almost none of
it is glamorous.

**Weeks six onward - earn the handover.** Train the people who will own it.
Write down what breaks and how to tell. Leave behind something a team can run
without you, because a deployment that depends on you is not finished.

## The part people underestimate

Most of the difficulty is not technical.

You are asking a team to change how they work, usually while they are already
busy, on the strength of a promise from someone they met last month. That is a
trust problem before it is an engineering problem - which is why the best
forward deployment engineers I know are unusually good listeners and unusually
willing to say "that will not work here".

## Why I like it

You find out whether the thing was actually good.

A model that scores well and is never used has taught you nothing. Forward
deployment closes that loop in the least comfortable and most useful way
available: real people, real work, in production, telling you the truth.
