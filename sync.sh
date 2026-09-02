#!/bin/bash
# insights/feed.json -> сайт. Запускать после publish.py.
# Не пушит сам: запись уезжает к учителям, это решение человека.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SRC="${1:-$(dirname "$HERE")/insights/feed.json}"
[ -f "$SRC" ] || { echo "нет $SRC — publish.py ещё ничего не опубликовал"; exit 1; }
cp "$SRC" "$HERE/feed.json"
python3 "$HERE/build.py" "$HERE/feed.json"
cd "$HERE"
if [ -z "$(git status --porcelain)" ]; then echo "изменений нет"; exit 0; fi
git add -A && git status --short
echo
echo "Проверь и отправь:  cd $HERE && git commit -m 'feed: обновление' && git push"
