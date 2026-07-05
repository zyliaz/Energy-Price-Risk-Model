#!/usr/bin/env bash
# UserPromptSubmit hook — when the user asks to add/onboard a data source,
# inject the New-Source Checklist so it is followed from the start.
input=$(cat)
prompt=$(printf '%s' "$input" | python3 -c "import sys,json;print(json.load(sys.stdin).get('prompt',''))" 2>/dev/null)
printf '%s' "$prompt" | grep -Eiq \
  'new (data )?source|add (a )?(new )?(scraper|extractor|parser|dataset|data ?source|pipeline)|onboard.*(source|dataset|data)|extract .*(new|another) (dataset|source)' \
  || exit 0
cl="$CLAUDE_PROJECT_DIR/00_knowledge_base/engineering/new-source-checklist.md"
[ -f "$cl" ] || exit 0
python3 - "$cl" <<'PY'
import json,sys
body=open(sys.argv[1]).read()
ctx="A data-source task was detected. Follow this New-Source Checklist "\
    "(00_knowledge_base/engineering/new-source-checklist.md) and honor CLAUDE.md §8 "\
    "(update the wiki on every addition):\n\n"+body
print(json.dumps({"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":ctx}}))
PY
exit 0
