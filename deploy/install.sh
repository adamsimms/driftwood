#!/usr/bin/env bash
# Install Driftwood to ~/driftwood on a Raspberry Pi (or any Linux host).
#
# Usage:
#   curl -fsSL .../install.sh | bash
#   ./deploy/install.sh
#   ./deploy/install.sh --from-source   # copy this repo instead of cloning
#
# Environment:
#   DRIFTWOOD_INSTALL_DIR  default: ~/driftwood
#   DRIFTWOOD_LEGACY_DIR   default: ~/logberry (renamed if present)
#   DRIFTWOOD_REPO_URL     default: https://github.com/adamsimms/driftwood.git
#   DRIFTWOOD_BRANCH       default: master

set -euo pipefail

REPO_URL="${DRIFTWOOD_REPO_URL:-https://github.com/adamsimms/driftwood.git}"
BRANCH="${DRIFTWOOD_BRANCH:-master}"
INSTALL_DIR="${DRIFTWOOD_INSTALL_DIR:-$HOME/driftwood}"
LEGACY_DIR="${DRIFTWOOD_LEGACY_DIR:-$HOME/logberry}"
FROM_SOURCE=0

if [[ "${1:-}" == "--from-source" ]]; then
  FROM_SOURCE=1
fi

log() {
  echo "[driftwood] $*"
}

migrate_legacy_csvs() {
  mkdir -p "$INSTALL_DIR/data" "$INSTALL_DIR/logs"

  if [[ -f "$INSTALL_DIR/scripts/tide_data.csv" ]]; then
    log "Moving scripts/tide_data.csv -> data/"
    mv "$INSTALL_DIR/scripts/tide_data.csv" "$INSTALL_DIR/data/"
  fi

  if [[ -f "$INSTALL_DIR/scripts/wave_status.csv" ]]; then
    log "Moving scripts/wave_status.csv -> data/"
    mv "$INSTALL_DIR/scripts/wave_status.csv" "$INSTALL_DIR/data/"
  fi
}

migrate_legacy_install_dir() {
  if [[ -d "$LEGACY_DIR" && "$LEGACY_DIR" != "$INSTALL_DIR" && ! -e "$INSTALL_DIR" ]]; then
    log "Renaming legacy install $LEGACY_DIR -> $INSTALL_DIR"
    mv "$LEGACY_DIR" "$INSTALL_DIR"
  fi
}

copy_tree() {
  local source="$1"
  local dest="$2"
  mkdir -p "$dest"
  cp -a "$source"/. "$dest"/
  rm -rf "$dest/.git"
  find "$dest" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
}

install_from_source() {
  local source_dir
  source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

  migrate_legacy_install_dir

  if [[ -d "$INSTALL_DIR/.git" ]]; then
    log "Updating existing install at $INSTALL_DIR from $source_dir"
    copy_tree "$source_dir" "$INSTALL_DIR"
  elif [[ -e "$INSTALL_DIR" ]]; then
    log "Refusing to overwrite existing path: $INSTALL_DIR"
    exit 1
  else
    log "Copying $source_dir -> $INSTALL_DIR"
    mkdir -p "$(dirname "$INSTALL_DIR")"
    copy_tree "$source_dir" "$INSTALL_DIR"
  fi
}

install_from_git() {
  migrate_legacy_install_dir

  if [[ -d "$INSTALL_DIR/.git" ]]; then
    log "Updating $INSTALL_DIR from $REPO_URL ($BRANCH)"
    git -C "$INSTALL_DIR" fetch origin
    git -C "$INSTALL_DIR" checkout "$BRANCH"
    git -C "$INSTALL_DIR" pull --ff-only origin "$BRANCH"
  elif [[ -e "$INSTALL_DIR" ]]; then
    log "Refusing to overwrite existing path: $INSTALL_DIR"
    exit 1
  else
    log "Cloning $REPO_URL ($BRANCH) -> $INSTALL_DIR"
    git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
  fi
}

if [[ "$FROM_SOURCE" -eq 1 ]]; then
  install_from_source
else
  install_from_git
fi

migrate_legacy_csvs

log "Installing Python dependencies"
pip3 install -r "$INSTALL_DIR/requirements.txt" --user

if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
  log "Installing sudoers rule for Pi reboot on unrecoverable motor errors"
  sudo cp "$INSTALL_DIR/deploy/sudoers.d/driftwood" /etc/sudoers.d/driftwood
  sudo chmod 440 /etc/sudoers.d/driftwood
else
  log "Skipping sudoers install (no passwordless sudo). To enable recovery reboot:"
  log "  sudo cp $INSTALL_DIR/deploy/sudoers.d/driftwood /etc/sudoers.d/driftwood"
  log "  sudo chmod 440 /etc/sudoers.d/driftwood"
fi

log "Installed at $INSTALL_DIR"
log "Enable services:"
log "  sudo cp $INSTALL_DIR/deploy/systemd/*.service /etc/systemd/system/"
log "  sudo systemctl daemon-reload"
log "  sudo systemctl enable --now driftwood-data driftwood-motors"
