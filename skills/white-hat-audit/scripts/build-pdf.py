"""Build the branded PDF report.

uv run -q --with markdown-it-py python -I build-pdf.py REPORT.md OUT.pdf \
    --site example.com --for "Managing Director<br>Example BV" \
    [--subtitle "..."] [--date "20 November 2026"]

The report's H1 + **Date:**/**Scope:** lines become the cover; its closing italic
line becomes the colophon. Images are referenced as img/... next to REPORT.md.
Brand (name, logo, preparer block) comes from ~/.config/white-hat-audit/brand.json;
without it the cover shows no preparer. Fonts are fetched once into
~/.cache/white-hat-audit/fonts.
"""
import argparse, base64, json, os, re, subprocess, sys, tempfile, urllib.request
from markdown_it import MarkdownIt

ap = argparse.ArgumentParser()
ap.add_argument("report"); ap.add_argument("out")
ap.add_argument("--site", required=True)
ap.add_argument("--for", dest="for_", required=True, help="recipient, HTML allowed (<br>)")
ap.add_argument("--subtitle", default="Is it safe, can people find it, and do visitors get the idea?")
ap.add_argument("--date")
a = ap.parse_args()

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
FONTS = os.path.expanduser("~/.cache/white-hat-audit/fonts")
FONT_CSS = "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600&display=swap"

def ensure_fonts():
    local = os.path.join(FONTS, "local.css")
    if os.path.exists(local):
        return open(local).read()
    os.makedirs(FONTS, exist_ok=True)
    req = urllib.request.Request(FONT_CSS, headers={"User-Agent": UA})
    css = urllib.request.urlopen(req, timeout=30).read().decode()
    urls = list(dict.fromkeys(re.findall(r"url\((https://[^)]+\.woff2)\)", css)))
    for i, u in enumerate(urls):
        path = os.path.join(FONTS, f"f{i}.woff2")
        urllib.request.urlretrieve(u, path)
        css = css.replace(u, f"f{i}.woff2")
    open(local, "w").write(css)
    return css

brand_path = os.path.expanduser("~/.config/white-hat-audit/brand.json")
brand = json.load(open(brand_path)) if os.path.exists(brand_path) else {}
brand_name = brand.get("name", "")
logo_file = os.path.expanduser(brand.get("logo", ""))
logo = base64.b64encode(open(logo_file, "rb").read()).decode() if logo_file and os.path.exists(logo_file) else ""
logo_img = f'<img src="data:image/png;base64,{logo}" alt="">' if logo else ""

md = open(a.report, encoding="utf-8").read()
m = re.match(r"\A# .*?\n\n\*\*Date:\*\*\s*(.*?)\n\*\*Scope:\*\*.*?\n", md, flags=re.S)
if not m:
    sys.exit("report must start with '# <site>: website check', a blank line, **Date:** and **Scope:** lines")
date = a.date or m.group(1).strip()
md = md[m.end():]
colophon = ""
c = re.search(r"\n---\n\n\*(.+?)\*\s*\Z", md, flags=re.S)
if c:
    colophon, md = c.group(1), md[:c.start()] + "\n"

body = MarkdownIt("commonmark").enable("table").render(md)
body = re.sub(r"<hr />\s*(?=<h2>Part)", '<div class="pb"></div>', body)
body = body.replace("<hr />", '<hr class="rule" />')
md_dir = os.path.dirname(os.path.abspath(a.report))
body = body.replace('src="img/', f'src="file://{md_dir}/img/')

fonts_css = re.sub(r"url\((f\d+\.woff2)\)", lambda x: f"url(file://{FONTS}/{x.group(1)})", ensure_fonts())
stem, dot, tld = a.site.rpartition(".")
title_html = f"{stem}<em>.{tld}</em>" if dot else a.site
site = a.site
prepared = brand.get("prepared_by_html", "")
prepared_dd = f'<div><dt>Prepared by</dt><dd>{prepared}</dd></div>' if prepared else ""
colophon_html = (f'<div class="colophon">{logo_img}<p>{colophon}<small>{brand_name}</small></p></div>'
                 if colophon else "")

html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>{site}: website check</title>
<style>
{fonts_css}
:root {{
  --ink:#1c1917; --muted:#57534e; --line:#d6d3d1; --soft:#f5f5f4; --paper:#fff;
  --accent:oklch(66.58% 0.157 58.3); --accent-soft:#fed7aa;
  --serif:"Instrument Serif", Georgia, serif; --sans:"Inter", system-ui, sans-serif;
}}
@page {{
  size:A4; margin:22mm 20mm 20mm 20mm;
  @bottom-left {{ content:"{brand_name} · {site} website check"; font:500 8pt var(--sans); color:#a8a29e; }}
  @bottom-right {{ content:counter(page) " / " counter(pages); font:500 8pt var(--sans); color:#a8a29e; }}
}}
@page cover {{ margin:0; @bottom-left {{ content:none }} @bottom-right {{ content:none }} }}
* {{ box-sizing:border-box; }}
html {{ -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
body {{ margin:0; font:400 10pt/1.55 var(--sans); color:var(--ink); }}

.cover {{ page:cover; height:297mm; padding:22mm 20mm; background:var(--soft);
  display:flex; flex-direction:column; break-after:page; position:relative; overflow:hidden; }}
.cover::after {{ content:""; position:absolute; right:-60mm; top:-60mm; width:170mm; height:170mm;
  border-radius:50%; background:var(--accent-soft); opacity:.55; }}
.brand {{ display:flex; align-items:center; gap:10px; position:relative; z-index:1; }}
.brand img {{ width:34px; height:34px; }}
.brand span {{ font:600 12pt var(--sans); letter-spacing:-.01em; }}
.cover-main {{ margin-top:auto; position:relative; z-index:1; }}
.kicker {{ font:600 8.5pt var(--sans); text-transform:uppercase; letter-spacing:.14em; color:var(--accent); }}
.cover h1 {{ font:400 58pt/1 var(--serif); letter-spacing:-.02em; margin:10px 0 14px; }}
.cover h1 em {{ color:var(--accent); }}
.cover .sub {{ font:italic 400 20pt/1.25 var(--serif); color:var(--muted); max-width:135mm; margin:0; }}
.cover-meta {{ margin-top:22mm; padding-top:6mm; border-top:1px solid var(--line);
  display:grid; grid-template-columns:repeat(3,1fr); gap:6mm; position:relative; z-index:1; }}
.cover-meta dt {{ font:600 7.5pt var(--sans); text-transform:uppercase; letter-spacing:.12em; color:#a8a29e; margin-bottom:3px; }}
.cover-meta dd {{ margin:0; font:500 9.5pt/1.4 var(--sans); }}
.cover-meta a {{ color:inherit; text-decoration:none; }}

main h2 {{ font:400 24pt/1.15 var(--serif); letter-spacing:-.01em; margin:12mm 0 4mm; break-after:avoid; }}
main h2:first-child {{ margin-top:0; }}
main h3 {{ font:600 11.5pt/1.35 var(--sans); margin:8mm 0 2.5mm; padding-left:9px;
  border-left:3px solid var(--accent); break-after:avoid; }}
main p {{ margin:0 0 3mm; }}
main ul, main ol {{ margin:0 0 3mm; padding-left:5.5mm; }}
main li {{ margin-bottom:1.2mm; break-inside:avoid; }}
main ol li::marker {{ color:var(--accent); font-weight:600; }}
main strong {{ font-weight:600; }}
main em {{ color:var(--muted); }}
main code {{ font:9pt ui-monospace, "DejaVu Sans Mono", monospace; background:var(--soft);
  padding:1px 4px; border-radius:3px; word-break:break-all; }}
.pb {{ break-after:page; }}
main hr.rule {{ border:0; border-top:1px solid var(--line); margin:10mm 0 0; }}
main table {{ width:100%; border-collapse:collapse; margin:3mm 0 5mm; font-size:8.8pt; }}
main th {{ text-align:left; font:600 7.5pt var(--sans); text-transform:uppercase; letter-spacing:.08em;
  color:var(--muted); border-bottom:1.5px solid var(--ink); padding:2mm 2mm 2mm 0; }}
main td {{ border-bottom:1px solid var(--line); padding:2mm 2mm 2mm 0; vertical-align:top; }}
main tr {{ break-inside:avoid; }}
main thead {{ display:table-header-group; }}
main h2 + table {{ break-before:avoid; }}
main h3 + p, main h2 + p {{ break-before:avoid; }}

main p > img {{ display:block; width:100%; border:1px solid var(--line); border-radius:6px; margin:1mm 0 2mm; break-inside:avoid; }}
.colophon {{ margin-top:12mm; padding:6mm 7mm; background:var(--soft); border-radius:6px;
  display:flex; align-items:center; gap:12px; break-inside:avoid; }}
.colophon img {{ width:30px; height:30px; }}
.colophon p {{ margin:0; font:italic 400 13pt/1.3 var(--serif); }}
.colophon small {{ display:block; font:500 8pt var(--sans); color:var(--muted); font-style:normal; margin-top:2px; }}
</style></head><body>
<section class="cover">
  <div class="brand">{logo_img}<span>{brand_name}</span></div>
  <div class="cover-main">
    <div class="kicker">Website check</div>
    <h1>{title_html}</h1>
    <p class="sub">{a.subtitle}</p>
  </div>
  <dl class="cover-meta">
    <div><dt>Prepared for</dt><dd>{a.for_}</dd></div>
    <div><dt>Date</dt><dd>{date}</dd></div>
    {prepared_dd}
  </dl>
</section>
<main>
{body}
{colophon_html}
</main>
</body></html>"""

with tempfile.TemporaryDirectory() as tmp:
    page = os.path.join(tmp, "report.html")
    open(page, "w", encoding="utf-8").write(html)
    chrome = os.environ.get("CHROME_PATH", "chromium")
    subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu", "--allow-file-access-from-files",
                    "--no-pdf-header-footer", "--virtual-time-budget=5000",
                    f"--print-to-pdf={os.path.abspath(a.out)}", f"file://{page}"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(a.out)
