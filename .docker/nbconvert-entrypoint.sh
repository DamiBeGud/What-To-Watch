#!/bin/sh
set -eu

WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"
OUTPUT_DIR="${OUTPUT_DIR:-$WORKSPACE_DIR/.pdf}"

usage() {
  cat <<'EOF'
Usage:
  notebook_pdf [notebook.ipynb ...]

Behavior:
  - With no arguments, converts every .ipynb file in /workspace.
  - With arguments, converts only the specified notebooks.
  - PDFs are written under /workspace/.pdf by default.
EOF
}

resolve_path() {
  case "$1" in
    /*) printf '%s\n' "$1" ;;
    *) printf '%s/%s\n' "$WORKSPACE_DIR" "$1" ;;
  esac
}

convert_one() {
  notebook_path="$1"

  if [ ! -f "$notebook_path" ]; then
    echo "Notebook not found: $notebook_path" >&2
    return 1
  fi

  case "$notebook_path" in
    *.ipynb) ;;
    *)
      echo "Expected an .ipynb file: $notebook_path" >&2
      return 1
      ;;
  esac

  rel_path="${notebook_path#$WORKSPACE_DIR/}"
  if [ "$rel_path" = "$notebook_path" ]; then
    rel_path="$(basename "$notebook_path")"
  fi

  rel_dir="$(dirname "$rel_path")"
  notebook_name="$(basename "$notebook_path" .ipynb)"
  target_dir="$OUTPUT_DIR"

  if [ "$rel_dir" != "." ]; then
    target_dir="$OUTPUT_DIR/$rel_dir"
  fi

  mkdir -p "$target_dir"
  echo "Converting $rel_path -> ${target_dir#$WORKSPACE_DIR/}/$notebook_name.pdf"

  jupyter nbconvert \
    --to webpdf \
    --WebPDFExporter.disable_sandbox=True \
    --output-dir "$target_dir" \
    --output "$notebook_name" \
    "$notebook_path"
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

mkdir -p "$OUTPUT_DIR"

if [ "$#" -eq 0 ]; then
  found_any=0

  while IFS= read -r notebook_path; do
    found_any=1
    convert_one "$notebook_path"
  done <<EOF
$(find "$WORKSPACE_DIR" -type f -name '*.ipynb' \
  ! -path '*/.ipynb_checkpoints/*' \
  ! -path '*/.git/*' \
  | LC_ALL=C sort)
EOF

  if [ "$found_any" -eq 0 ]; then
    echo "No notebooks found under $WORKSPACE_DIR" >&2
    exit 1
  fi

  exit 0
fi

for notebook_arg in "$@"; do
  convert_one "$(resolve_path "$notebook_arg")"
done
