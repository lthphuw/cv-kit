# Scoping a new or vague task

Write no code and pick no model until the user has approved a brief. If the superpowers brainstorming skill is
installed, use it for the conversation and take only the extra questions below.

1. **Ask**, one question at a time, only what the request leaves open: the task and the decision it supports; the
   data (size, labels, domain, privacy); the success metric and its target; latency and hardware; licence and
   commercial use; what was tried or ruled out. For a CV task, name the dataset and split the metric is read on.
2. **Write it back** in a few lines: purpose, constraints, success criteria, with what the user said apart from what
   you assume. Ask what is wrong or missing.
3. **Propose two or three approaches**, recommend one, and cut whatever the task does not need. A model choice
   goes to `/cv-kit:research`.
4. **Split** an approved plan into work packages: package, inputs, output, files touched, depends on. A package is
   independent only if it shares no file and needs no other package's output; the rest stay in order. Route the
   packages as `routing.md` says, after the user's yes.
