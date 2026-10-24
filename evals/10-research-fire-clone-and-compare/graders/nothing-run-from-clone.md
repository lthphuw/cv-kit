---
type: regex
target: trace
match: not_contains
pattern: '"name":"Bash","input":\{[^}]*"command":"[^"]*(?:pytest|pip3? install|setup\.py|npm (?:install|run)|cmake |make |\./install)'
---
