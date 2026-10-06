#!/bin/sh
# Launch GRIM, the STRESS desktop reaper.
#   ./grim.sh              normal haunting (quiz every 4-9 minutes)
#   ./grim.sh --test       rapid-fire demo
#   ./grim.sh --no-voice   silent mode
DIR="$(cd "$(dirname "$0")" && pwd)"
[ -f "$DIR/assets/reaper.png" ] || python3 "$DIR/make_sprites.py"
exec python3 "$DIR/reaper.py" "$@"
