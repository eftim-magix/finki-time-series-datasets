#!/usr/bin/env bash
# Render a Markdown file to PDF next to it: pandoc (Markdown -> HTML) + headless Chrome (HTML -> PDF).
#   tools/md2pdf.sh datasets/mepso/docs/README_data_quality.md
set -euo pipefail
md="$1"
pdf="${md%.md}.pdf"
chrome="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cat > "$tmp/style.css" <<'CSS'
body { font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 11pt; line-height: 1.45; max-width: 100%; margin: 0; color: #1d2126; }
h1 { font-size: 20pt; } h2 { font-size: 15pt; margin-top: 1.4em; } h3 { font-size: 12.5pt; }
table { border-collapse: collapse; font-size: 9pt; margin: 0.6em 0; }
th, td { border: 1px solid #c8c8c8; padding: 3px 6px; vertical-align: top; }
th { background: #f0f2f5; }
code { font-size: 9pt; background: #f4f4f4; padding: 0 2px; }
pre { background: #f4f4f4; padding: 8px; font-size: 8.5pt; white-space: pre-wrap; }
a { color: #0300c0; }
@page { size: A4; margin: 16mm 14mm; }
CSS
# pandoc 3 calls it --embed-resources, pandoc 2 --self-contained
embed=--self-contained; pandoc --help | grep -q -- --embed-resources && embed=--embed-resources
pandoc "$md" --standalone "$embed" --css "$tmp/style.css" \
  --metadata pagetitle="$(basename "${md%.md}")" --resource-path "$(dirname "$md")" -o "$tmp/doc.html"
"$chrome" --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="$pdf" "file://$tmp/doc.html" 2>/dev/null
echo "wrote $pdf"
