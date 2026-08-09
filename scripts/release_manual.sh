#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RELEASE_VERSION="${RELEASE_VERSION:-}"
if [[ -z "$RELEASE_VERSION" ]]; then
  RELEASE_VERSION="$(awk -F= '/^APP_VERSION[[:space:]]*=/ {gsub(/[[:space:]]/,"",$2); print $2; exit}' makefile)"
fi

ALLOW_DIRTY="${ALLOW_DIRTY:-0}"
CONFIRM_RELEASE="${CONFIRM_RELEASE:-0}"
PUBLISH_LATEST="${PUBLISH_LATEST:-0}"
PUBLISH_STABLE="${PUBLISH_STABLE:-0}"

STATUS_DIR=".release-status"
mkdir -p "$STATUS_DIR"
STATUS_FILE="$STATUS_DIR/${RELEASE_VERSION}.txt"
: > "$STATUS_FILE"

echo "Manual release session"
echo "  version: $RELEASE_VERSION"
echo "  status file: $STATUS_FILE"

overall=0

run_step() {
  local name="$1"
  shift

  echo
  echo "==> $name"
  if "$@"; then
    echo "$name=PASS" | tee -a "$STATUS_FILE"
  else
    local rc=$?
    echo "$name=FAIL($rc)" | tee -a "$STATUS_FILE"
    overall=1
  fi
}

run_step "release-prepare" make release-prepare RELEASE_VERSION="$RELEASE_VERSION" ALLOW_DIRTY="$ALLOW_DIRTY"
run_step "release-docs" make release-docs RELEASE_VERSION="$RELEASE_VERSION"
run_step "release-package" make release-package RELEASE_VERSION="$RELEASE_VERSION"
run_step "release-demo-image" make release-demo-image RELEASE_VERSION="$RELEASE_VERSION" CONFIRM_RELEASE="$CONFIRM_RELEASE" PUBLISH_LATEST="$PUBLISH_LATEST" PUBLISH_STABLE="$PUBLISH_STABLE"
run_step "release-verify" make release-verify RELEASE_VERSION="$RELEASE_VERSION"

echo
echo "Release summary ($RELEASE_VERSION)"
cat "$STATUS_FILE"

if [[ "$overall" -ne 0 ]]; then
  echo
  echo "One or more steps failed. Fix the failed step and retry only that target."
  exit 1
fi

echo
echo "All release steps passed."
