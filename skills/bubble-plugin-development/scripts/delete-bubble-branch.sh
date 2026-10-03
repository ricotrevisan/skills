#!/usr/bin/env bash
# Delete Bubble app branches through the Bubble editor UI, driven by browserq.
#
# Usage: delete-bubble-branch.sh [--dry-run] <branch-name> [more names...]
#
# Requires: browserq (lab admission queue), BUBBLE_COOKIE (editor Cookie header,
# never printed), and the Buildprint CLI for the authoritative branch list.
# Env: BUBBLE_APP (default tiptap-plugin), BUILDPRINT_PROFILE (default ricowtf),
#      BROWSERQ_AGENT (default bubble-branch-cleanup).
#
# Safety: each name must appear in `buildprint branch list`; the editor's branch
# menu must show that branch's Buildprint ID before Delete is chosen; the
# confirmation dialog must name the branch. --dry-run stops at the dialog and
# closes it. Deletion is confirmed afterwards via `buildprint branch list`.
set -euo pipefail

APP="${BUBBLE_APP:-tiptap-plugin}"
export BUILDPRINT_PROFILE="${BUILDPRINT_PROFILE:-ricowtf}"
export BROWSERQ_AGENT="${BROWSERQ_AGENT:-bubble-branch-cleanup}"
BQ="${BROWSERQ:-browserq}"

DRY=0
if [[ "${1:-}" == "--dry-run" ]]; then DRY=1; shift; fi
(($#)) || { echo "usage: $0 [--dry-run] <branch-name>..." >&2; exit 64; }
[[ -n "${BUBBLE_COOKIE:-}" ]] || { echo "BUBBLE_COOKIE is not set" >&2; exit 64; }
for n in "$@"; do
  [[ "$n" =~ ^[A-Za-z0-9_-]{1,64}$ ]] || { echo "invalid branch name: $n" >&2; exit 64; }
  case "${n,,}" in main|test|live) echo "refusing to delete $n" >&2; exit 64;; esac
done

branch_id() { # name -> Buildprint branch id, empty if not listed
  buildprint branch list "$APP" | sed -n "s/.*─ $1 (\([a-z0-9]*\))\$/\1/p"
}

JOB=$("$BQ" start --engine chrome --label bubble-branches --wait 5m)
trap '"$BQ" close "$JOB" >/dev/null 2>&1 || true' EXIT
bx() { "$BQ" exec "$JOB" --timeout "${T:-60s}" -- "$@"; }
q() { bx "$@" >/dev/null; }
js() { bx eval "$1" | tr -d '"'; }
click_xy() { q mouse move "$1" "$2"; q mouse down; q mouse up; }
ref_of() { # extended regex over the interactive snapshot -> first ref
  bx snapshot -i | grep -E -- "$1" | grep -o 'ref=e[0-9]*' | head -1 | cut -d= -f2
}
# Centre "x,y" of the first visible element whose own text is exactly $1
# (optionally inside the CSS selector $2), or "none".
xy_of_text() {
  js "(() => { const root = document.querySelector('${2:-body}'); if (!root) return 'none';
    const hit = [...root.querySelectorAll('*')].find(e => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim() === '$1'); });
    if (!hit) return 'none'; const r = hit.getBoundingClientRect();
    return Math.round(r.x + r.width / 2) + ',' + Math.round(r.y + r.height / 2); })()"
}
# Centre of the red Delete button inside the confirmation dialog, or "none".
dialog_delete_xy() {
  js "(() => { const hit = [...document.querySelectorAll('body *')].find(e => {
      const r = e.getBoundingClientRect(); if (!(r.width > 0 && r.height > 0)) return false;
      if (![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim() === 'Delete')) return false;
      let a = e; for (let i = 0; i < 8 && a; i++, a = a.parentElement)
        if (a.innerText && a.innerText.includes('Are you sure you want to delete')) return true;
      return false; });
    if (!hit) return 'none'; const r = hit.getBoundingClientRect();
    return Math.round(r.x + r.width / 2) + ',' + Math.round(r.y + r.height / 2); })()"
}
page_has() { [[ "$(js "document.body.innerText.includes('$1')")" == true ]]; }
wait_loaded() {
  for _ in $(seq 40); do page_has 'We are loading' || return 0; sleep 3; done
  echo "editor still loading after 120s" >&2; return 1
}
# The panel is position:fixed and only present in the DOM while open.
panel_open() { [[ "$(js "(document.querySelector('.sidepanel.version-control')?.getBoundingClientRect().width || 0) > 0")" == true ]]; }
open_panel() {
  panel_open && return 0
  q click "@$(ref_of 'button "Main( / [^"]*)?" ')"; q wait 3000
  panel_open || { echo "branch panel did not open" >&2; return 1; }
}
shot() { bx screenshot "$1" 2>&1 >/dev/null | sed -n 's/^browserq: artifact /  screenshot: /p'; }

# Log in with the editor cookie; values go to browserq via stdin, never argv.
for d in bubble.io app.bubble.io; do
  printf '%s' "$BUBBLE_COOKIE" | "$BQ" cookies import "$JOB" - --domain "$d" >/dev/null
done
q set viewport 1700 1050
T=120s q open "https://bubble.io/page?id=$APP&tab=Design"
q wait 5000
wait_loaded
[[ "$(bx get title)" == *"Bubble Editor"* ]] || { echo "not in the Bubble editor (login cookie expired?)" >&2; shot login-failed.png; exit 1; }

status=0
for name in "$@"; do
  echo "=== $name"
  id=$(branch_id "$name")
  if [[ -z "$id" ]]; then echo "  not listed by buildprint, skipping"; continue; fi
  open_panel
  xy=$(xy_of_text "$name" '.sidepanel.version-control')
  if [[ "$xy" == none ]]; then echo "  not shown in the editor branch panel, skipping"; status=1; continue; fi
  click_xy "${xy%,*}" "${xy#*,}"
  q wait 3000; wait_loaded; q wait 6000
  open_panel
  if [[ "$(js "document.querySelector('.sidepanel.version-control h4')?.innerText.trim()")" != "$name" ]]; then
    echo "  editor did not switch to $name, skipping"; shot "switch-failed-$name.png"; status=1; continue
  fi
  click_xy 276 66   # "..." menu next to the branch title
  q wait 1500
  if ! page_has "ID: $id"; then
    echo "  branch menu does not show ID $id, aborting this branch"; shot "menu-mismatch-$name.png"
    q press Escape; status=1; continue
  fi
  q click "@$(ref_of 'option "Delete"')"
  q wait 1500
  if ! page_has "Delete $name"; then
    echo "  delete dialog for $name not found"; shot "dialog-missing-$name.png"; status=1; continue
  fi
  del_xy=$(dialog_delete_xy)
  if [[ "$del_xy" == none ]]; then
    echo "  red Delete button not found in the dialog"; shot "dialog-missing-$name.png"; status=1; continue
  fi
  if ((DRY)); then
    shot "dry-run-$name.png"
    echo "  dialog Delete button at $del_xy (not clicked)"
    q click "@$(ref_of '"Close" \[ref=')"
    echo "  dry run: reached the confirmation dialog for $name (id $id); closed it"
    continue
  fi
  q fill "@$(ref_of "textbox \"$name\"")" "$name"
  q wait 800
  click_xy "${del_xy%,*}" "${del_xy#*,}"
  q wait 10000
  shot "after-$name.png"
  if [[ -z "$(branch_id "$name")" ]]; then echo "  deleted (buildprint no longer lists $name)"
  else echo "  still listed by buildprint; NOT deleted"; status=1; fi
done
exit $status
