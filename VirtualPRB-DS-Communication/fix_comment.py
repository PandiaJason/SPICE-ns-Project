import re

with open("ptb_wiley_manuscript.tex", "r") as f:
    text = f.read()

# Fix the stray comment left over from earlier refactoring
old_comment = r"% ── 4. Simulation ───────────────────────────────────────────────────────────\n\n\\subsection\{Hardware Realization"
new_comment = r"% ── 3.4 Hardware Realization ────────────────────────────────────────────────\n\n\\subsection{Hardware Realization"

text = re.sub(old_comment, new_comment, text)

with open("ptb_wiley_manuscript.tex", "w") as f:
    f.write(text)
