#!/usr/bin/env bash
# SessionStart hook — detect repo changes made OUTSIDE a session (committed since last
# seen, or uncommitted) under the content dirs, and prompt a wiki reconcile (CLAUDE.md §8).
root="$CLAUDE_PROJECT_DIR"
cd "$root" 2>/dev/null || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0            # not a git repo → skip
dirs=(01_data 02_scripts 03_notebooks 04_jobs)
state="$root/.claude/.wiki_sync_state"
cur=$(git rev-parse HEAD 2>/dev/null)
last=$(cat "$state" 2>/dev/null)

{
  git status --porcelain -- "${dirs[@]}" 2>/dev/null | sed 's/^...//'
  if [ -n "$last" ] && [ "$last" != "$cur" ]; then
    git diff --name-only "$last" "$cur" -- "${dirs[@]}" 2>/dev/null
  fi
} | grep -vE '\.DS_Store|__pycache__|\.ipynb_checkpoints' | sort -u > /tmp/_wiki_drift.$$

echo "$cur" > "$state"                                        # advance the marker
[ -s /tmp/_wiki_drift.$$ ] || { rm -f /tmp/_wiki_drift.$$; exit 0; }

python3 - /tmp/_wiki_drift.$$ <<'PY'
import json,sys
files=[l.strip() for l in open(sys.argv[1]) if l.strip()]
lst="\n".join("  - "+f for f in files[:40])
extra="" if len(files)<=40 else f"\n  …and {len(files)-40} more"
ctx=("Repo files under content dirs changed outside a session (committed since last seen, "
     "or uncommitted):\n"+lst+extra+"\n\nPer CLAUDE.md §8, reconcile the wiki before other "
     "work: update the relevant catalog (extraction-scripts / notebook-catalog / "
     "ercot-data-products), then index.md + a log.md line.")
print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":ctx}}))
PY
rm -f /tmp/_wiki_drift.$$
exit 0
