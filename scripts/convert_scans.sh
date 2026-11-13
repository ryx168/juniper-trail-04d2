#!/usr/bin/env bash
# Convert everything dropped into scans/ into site/models/<id>.glb.
#
# Accepted per scan (the id is the file or folder name, lower-cased, non-alphanumerics -> "-"):
#   a loose file   scans/fountain.usdz  .usd .usdc .usda .obj .glb .gltf .fbx .ply .stl
#   a folder       scans/fountain/      holding the .obj with its .mtl and textures
#   a zip          scans/fountain.zip   what KIRI Engine, Polycam and Scaniverse hand you on
#                                       Android: .obj + .mtl + .jpg, or a .glb, inside
# A loose .mtl/.jpg/.png next to a loose .obj is its sidecar and is skipped on its own.
# Env: BLENDER (default ~/blender/blender), OUT (default site/models), DECIMATE (ratio or empty).
set -euo pipefail
BLENDER=${BLENDER:-$HOME/blender/blender}
OUT=${OUT:-site/models}; mkdir -p "$OUT"
DECIMATE=${DECIMATE:-}
shopt -s nullglob nocaseglob

slug() { printf '%s' "$1" | tr -c 'A-Za-z0-9_-' '-' | tr 'A-Z' 'a-z'; }

# first model file under a directory, by preference; skips macOS resource forks
pick() {
  local d=$1 e f
  for e in glb gltf usdz usdc usda usd obj fbx ply stl; do
    f=$(find "$d" -type f -iname "*.$e" ! -iname "._*" ! -path "*/__MACOSX/*" | head -1)
    if [ -n "$f" ]; then printf '%s\n' "$f"; return 0; fi
  done
  return 1
}

convert() {
  local src=$1 id=$2 extra=()
  [ -n "$DECIMATE" ] && extra=(--decimate "$DECIMATE")
  echo "== $src -> $OUT/$id.glb"
  "$BLENDER" -b --python scripts/convert_scan.py -- "$src" "$OUT/$id.glb" "${extra[@]}" 2>&1 \
    | grep -E "model height|decimated|WROTE|Error|Traceback" || true
  [ -s "$OUT/$id.glb" ] || { echo "!! $src: conversion produced no GLB"; FAILED=1; }
}

FAILED=0
TMP=$(mktemp -d)
for f in scans/*; do
  [ -e "$f" ] || continue
  name=$(basename "$f"); lower=${name,,}
  case "$lower" in .*|readme*|*.md|*.txt) continue;; esac
  id=$(slug "${name%.*}")
  if [ -d "$f" ]; then
    src=$(pick "$f") || { echo "!! $f: no model file in the folder"; FAILED=1; continue; }
  elif [[ "$lower" == *.zip ]]; then
    d="$TMP/$id"; mkdir -p "$d"
    unzip -qo "$f" -d "$d"
    src=$(pick "$d") || { echo "!! $f: no model file inside the zip"; FAILED=1; continue; }
  else
    case "$lower" in
      *.usdz|*.usd|*.usdc|*.usda|*.obj|*.glb|*.gltf|*.fbx|*.ply|*.stl) src=$f;;
      *.mtl|*.jpg|*.jpeg|*.png) continue;;
      *) echo "!! $f: unsupported file type"; FAILED=1; continue;;
    esac
  fi
  convert "$src" "$id"
done
rm -rf "$TMP"
exit $FAILED
