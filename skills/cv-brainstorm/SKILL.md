---
name: cv-brainstorm
description: Use when a computer-vision task or project is new or underspecified, before choosing a model or writing code, including when such a task should be split across subagents.
---

# Brainstorm a CV task, then split it

Do not pick a model or write code until the user has approved the brief.

## 1. Understand
Ask one question at a time, preferring multiple choice. Cover: the task and the decision it supports, the data (size, labels, domain, privacy), the success metric and target value, latency and hardware, licence and commercial use, and what has already been tried or ruled out. Skip any question the request already answers.

## 2. Write it back
Summarise purpose, constraints and success criteria in a short note, separating what the user said from your assumptions. Invite correction before going on.

## 3. Propose two or three approaches
Lead with a recommendation and trade-offs. Use `cv-model-selection` for model choices and `cv-deep-research` when the choice needs sourced evidence. Cut anything the task does not need.

## 4. Split into work packages
Make a table: package, inputs, output, files or folders it touches, depends on. A package is independent only if it shares no files and needs no other package's output. Packages that fail that test stay sequential.

## 5. Dispatch only after approval
Show the table and wait for the user's yes. Then, for each independent package, dispatch one subagent in a single message so they run in parallel. Each brief states the goal, the constraints, what is ruled out, and the exact files to read; the agent knows nothing else. When results return, check them against the package's stated output before merging.

If the superpowers plugin is installed, its brainstorming and writing-plans skills cover the generic workflow; this skill adds the CV-specific questions and the split.
