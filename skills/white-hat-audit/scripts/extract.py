"""Visible text of a page as light Markdown: python3 -I extract.py page.html"""
import sys, html
from html.parser import HTMLParser
SKIP={'script','style','svg','template','noscript','head'}
VOID={'br','img','input','meta','link','hr','source','wbr','area','col','embed','track'}
GAP={'span','small','time','abbr','b','strong','em','i','data','output','meter'}
BLOCK={'p','div','section','li','h1','h2','h3','h4','header','footer','nav','main','article','form','label','button','a','tr','dd','dt','summary','figcaption','blockquote'}
class P(HTMLParser):
    def __init__(s): super().__init__(convert_charrefs=True); s.stack=[]; s.out=[]; s.cur=''
    def hidden(s): return any(h for _,h in s.stack)
    def flush(s):
        t=' '.join(s.cur.split());
        if t: s.out.append(t)
        s.cur=''
    def handle_starttag(s,tag,attrs):
        a=dict(attrs)
        if tag in VOID:
            if tag=='input' and not s.hidden() and a.get('type')!='hidden' and a.get('placeholder'): s.cur+=f" [field: {a['placeholder']}] "
            return
        hid = tag in SKIP or 'hidden' in a or a.get('aria-hidden')=='true' or bool(s.stack and s.stack[-1][1])
        s.stack.append((tag,hid))
        if tag in BLOCK or tag in('h1','h2','h3'): s.flush()
        if not hid and tag in ('h1','h2','h3'): s.cur='#'*int(tag[1])+' '
    def handle_endtag(s,tag):
        if tag in VOID: return
        while s.stack:
            t,_=s.stack.pop()
            if t==tag: break
        if tag in BLOCK: s.flush()
        elif tag in GAP and s.cur and not s.cur.endswith(' '): s.cur+=' '
    def handle_data(s,d):
        if not s.hidden(): s.cur+=d
p=P(); p.feed(open(sys.argv[1],encoding='utf-8').read()); p.flush()
out=[]; 
for l in p.out:
    if l.startswith('#'): out.append(''); out.append(l); out.append('')
    elif not out or out[-1]!=l: out.append(l)
print('\n'.join(out).strip())
