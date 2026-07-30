#!/usr/bin/env bash
# Stage every REAL change, skipping the repo's known CRLF-only churn.
#
# Why this exists: `git add -A` is unsafe here — ~473 files (the byte-frozen
# V1.34 parity goldens plus a few test modules) are committed with CRLF while
# .gitattributes demands LF, so they show as modified forever and `-A` would
# rewrite all of them. The historical workaround was explicit pathspecs, which
# silently DROPS files: `scripts/check_touched_coverage.py` was lost that way
# (macOS case-insensitivity indexed it under `Scripts/`, so a lowercase
# `git add scripts/...` matched nothing and CI failed on a missing file).
#
# This script stages exactly the files whose content differs ignoring CR, plus
# all untracked files, and reports anything skipped so a drop is never silent.
#
#   ./scripts/stage_real_changes.sh          # stage + report
#   ./scripts/stage_real_changes.sh --dry-run
#
# Note the case trap: if a new file is reported untracked under a
# differently-cased directory than the one you expect, stage it by blob hash:
#   BLOB=$(git hash-object -w <path>)
#   git update-index --add --cacheinfo 100644,$BLOB,<canonical/lowercase/path>

set -euo pipefail

DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

cd "$(git rev-parse --show-toplevel)"

real=()
churn=0

while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    if git diff --ignore-cr-at-eol --quiet -- "$file" 2>/dev/null; then
        churn=$((churn + 1))
    else
        real+=("$file")
    fi
done < <(git diff --name-only 2>/dev/null)

untracked=()
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    untracked+=("$file")
done < <(git ls-files --others --exclude-standard 2>/dev/null)

echo "real content changes : ${#real[@]}"
echo "untracked files      : ${#untracked[@]}"
echo "CRLF-only churn      : ${churn} (skipped by design)"

for file in "${real[@]}" "${untracked[@]}"; do
    echo "  + ${file}"
done

if (( DRY_RUN )); then
    echo "(dry run — nothing staged)"
    exit 0
fi

if (( ${#real[@]} == 0 && ${#untracked[@]} == 0 )); then
    echo "nothing to stage"
    exit 0
fi

for file in "${real[@]}" "${untracked[@]}"; do
    git add -- "$file"
done

# Verify every intended file actually landed in the index — the check that
# would have caught the dropped-script incident at stage time.
missing=()
for file in "${real[@]}" "${untracked[@]}"; do
    git ls-files --error-unmatch -- "$file" >/dev/null 2>&1 || missing+=("$file")
done

if (( ${#missing[@]} )); then
    echo "ERROR: these files did not land in the index (case-folding?):" >&2
    printf '  %s\n' "${missing[@]}" >&2
    echo "Stage them by blob hash — see the header comment." >&2
    exit 1
fi

echo "staged ${#real[@]} modified + ${#untracked[@]} untracked file(s); verified in index"
