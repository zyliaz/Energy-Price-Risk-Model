#!/usr/bin/env bash
# PostToolUse hook — after a repo file changes OUTSIDE the wiki, remind to run the
# CLAUDE.md §8 sync (update the relevant catalog page, then index.md + log.md).
input=$(cat)
path=$(printf '%s' "$input" | python3 -c "import sys,json;print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)
[ -n "$path" ] || exit 0
case "$path" in
  */00_knowledge_base/*) exit 0 ;;                         # wiki edits themselves: skip
  */02_scripts/*)   page="[[extraction-scripts]] (+ [[ercot-data-products]] if new dataset)";;
  */03_notebooks/*) page="[[notebook-catalog]]";;
  */01_data/*)      page="[[ercot-data-products]] + [[analysis-workflow]] lineage + the driver page";;
  */04_jobs/*)      page="[[extraction-scripts]] (jobs section)";;
  *) exit 0 ;;
esac
msg="Repo addition outside the wiki: $path. Per CLAUDE.md §8, update $page this session, then finish with index.md + a log.md line."
python3 - "$msg" <<'PY'
import json,sys
print(json.dumps({"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":sys.argv[1]},"suppressOutput":True}))
PY
exit 0
