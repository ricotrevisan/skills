#!/usr/bin/env bash
# Lighthouse, 3 runs x mobile/desktop per page; keeps the median run's score image and HTML report.
#   lighthouse.sh OUT_IMG_DIR name=https://url [name=https://url ...]
# Writes OUT_IMG_DIR/lighthouse-<name>-<mobile|desktop>.png and -report.html; prints a score table.
set -euo pipefail
out=$(realpath -m "$1"); shift
work=$(mktemp -d /tmp/wha-lh.XXXXXX); mkdir -p "$out"
export CHROME_PATH=${CHROME_PATH:-/usr/bin/chromium}
for pair in "$@"; do
  name=${pair%%=*}; url=${pair#*=}
  for n in 1 2 3; do for f in mobile desktop; do
    extra=(); [ $f = desktop ] && extra=(--preset=desktop)
    npx -y lighthouse@13.6.0 "$url" "${extra[@]}" --output=json --output=html \
      --output-path="$work/$name-$f-$n" --chrome-flags="--headless=new --no-sandbox --disable-gpu" --quiet \
      >"$work/$name-$f-$n.log" 2>&1 || echo "run failed: $name $f $n (see $work)"
    sleep 5
  done; done
done
# Pick the median run by performance score, screenshot its score header.
python3 -I - "$work" "$out" "$@" <<'EOF'
import json, os, shutil, subprocess, sys
work, out, pairs = sys.argv[1], sys.argv[2], sys.argv[3:]
for pair in pairs:
    name = pair.split('=', 1)[0]
    for f in ('mobile', 'desktop'):
        runs = []
        for n in (1, 2, 3):
            p = f'{work}/{name}-{f}-{n}.report.json'
            if os.path.exists(p):
                r = json.load(open(p)); runs.append((r['categories']['performance']['score'] or 0, n, r))
        if not runs: continue
        runs.sort(key=lambda x: x[0]); _, n, r = runs[len(runs) // 2]
        scores = {k: (round(c['score'] * 100) if c['score'] is not None else None) for k, c in r['categories'].items()}
        perf = sorted(round(x[0] * 100) for x in runs)
        a = r['audits']
        print(f"{name} {f} median run {n}: {scores} | perf across runs {perf} | "
              f"FCP {a['first-contentful-paint']['displayValue']} LCP {a['largest-contentful-paint']['displayValue']} "
              f"weight {a['total-byte-weight']['displayValue']}")
        for c in r['categories'].values():
            for x in c['auditRefs']:
                au = a.get(x['id'], {})
                if au.get('score') is not None and au['score'] < 0.9 and au.get('scoreDisplayMode') in ('binary', 'numeric', 'metricSavings'):
                    print(f"    {c['title']}: {au['title']} {au.get('displayValue', '')}")
        html = f'{out}/lighthouse-{name}-{f}-report.html'
        shutil.copy(f'{work}/{name}-{f}-{n}.report.html', html)
        full = f'{work}/{name}-{f}-full.png'
        subprocess.run([os.environ['CHROME_PATH'], '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
                        '--force-device-scale-factor=2', '--window-size=1000,640', '--virtual-time-budget=8000',
                        f'--screenshot={full}', f'file://{html}'], check=True, capture_output=True)
        subprocess.run(['uv', 'run', '-q', '--with', 'pillow', 'python', '-I', '-c',
                        f"from PIL import Image; Image.open('{full}').crop((380,70,1620,310)).save('{out}/lighthouse-{name}-{f}.png')"],
                       check=True)
print('raw runs:', work)
EOF
