#!/usr/bin/env python3
"""يجمع أخبار التعليم الابتدائي من المصادر المحددة ويبني موقعًا ثابتًا في مجلد site/."""
import json, re, shutil, hashlib, html, datetime as dt
from pathlib import Path
from urllib.parse import urljoin, quote
import requests, feedparser, markdown
import extras
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
C = json.loads((ROOT / "config.json").read_text("utf-8"))
S = json.loads((ROOT / "sources.json").read_text("utf-8"))
DATA = ROOT / "data" / "items.json"
OUT = ROOT / "site"
H = {"User-Agent": "Mozilla/5.0 (compatible; EduNewsBot/1.0)"}
TODAY = dt.date.today().isoformat()
esc = html.escape


# ---------- جمع الأخبار ----------
def match(text):
    return any(k.lower() in text.lower() for k in S["keywords"])


def from_rss(src):
    feed = feedparser.parse(requests.get(src["url"], headers=H, timeout=30).content)
    for e in feed.entries[:40]:
        d = TODAY
        if e.get("published_parsed"):
            d = dt.date(*e.published_parsed[:3]).isoformat()
        pub = (e.get("source") or {}).get("title") or src["name"]
        yield {"title": e.title.strip(), "link": e.link, "source": pub, "date": d}


def from_html(src):
    soup = BeautifulSoup(requests.get(src["url"], headers=H, timeout=30).content, "html.parser")
    seen = set()
    for a in soup.find_all("a", href=True):
        t = a.get_text(" ", strip=True)
        link = urljoin(src["url"], a["href"])
        if len(t) < 25 or link in seen or not link.startswith("http"):
            continue
        seen.add(link)
        yield {"title": t, "link": link, "source": src["name"], "date": TODAY}


def collect():
    items = json.loads(DATA.read_text("utf-8")) if DATA.exists() else []
    known = {i["id"] for i in items}
    for src in S["sources"]:
        try:
            for it in (from_rss if src["type"] == "rss" else from_html)(src):
                if src.get("filter", True) and not match(it["title"]):
                    continue
                it["id"] = hashlib.sha1(it["link"].encode()).hexdigest()[:12]
                if it["id"] not in known:
                    known.add(it["id"])
                    items.append(it)
        except Exception as ex:  # مصدر واحد معطل لا يوقف البناء
            print("تخطي المصدر", src["name"], "→", ex)
    items.sort(key=lambda i: i["date"], reverse=True)
    items = items[:300]
    DATA.write_text(json.dumps(items, ensure_ascii=False, indent=1), "utf-8")
    return items


# ---------- المقالات اليدوية ----------
def load_posts():
    posts = []
    for f in sorted((ROOT / "posts").glob("*.md")):
        raw = f.read_text("utf-8")
        m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
        meta, body = {}, raw
        if m:
            for line in m.group(1).splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = m.group(2)
        posts.append({
            "slug": f.stem, "title": meta.get("title", f.stem), "date": meta.get("date", TODAY),
            "level": meta.get("level", ""), "subject": meta.get("subject", ""),
            "summary": meta.get("summary", ""),
            "html": markdown.markdown(body, extensions=["tables", "fenced_code"]),
        })
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


# ---------- القالب ----------
CSS = """:root{--p:#F4F8FC;--g:#DCE6F2;--i:#1B2A5C;--m:#52608A;--r:#D6453D;--y:#FFD84D;--c:#fff}
@media(prefers-color-scheme:dark){:root{--p:#121A33;--g:#1D2848;--i:#E8EEFF;--m:#A5B2D6;--c:#18224A}}
*{box-sizing:border-box}body{margin:0;font-family:Tajawal,system-ui,sans-serif;color:var(--i);line-height:1.9;background:var(--p) linear-gradient(var(--g) 1px,transparent 1px),linear-gradient(90deg,var(--g) 1px,transparent 1px);background-size:28px 28px}
a{color:inherit}.w{max-width:960px;margin:0 auto;padding:0 18px}
header{background:var(--p);border-bottom:2px solid var(--r)}.bar{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;padding:12px 0}
.logo{font-weight:800;font-size:1.4rem;text-decoration:none}.logo b{background:linear-gradient(transparent 55%,var(--y) 55%)}
nav a{margin-inline-end:16px;text-decoration:none;color:var(--m);font-weight:500}
h1{font-size:clamp(1.6rem,5vw,2.4rem);line-height:1.4}h2{font-size:1.4rem;margin-top:34px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
.card,.row{background:var(--c);border:2px solid var(--i);border-radius:8px;padding:12px 16px;border-inline-start:8px solid var(--r)}
.card h3{margin:2px 0 6px;font-size:1.05rem}.card a,.row a{text-decoration:none}.card a:hover,.row a:hover{text-decoration:underline}
small{color:var(--m)}.row{margin-bottom:10px}article{background:var(--c);border:2px solid var(--i);border-radius:8px;padding:8px 22px 22px}
article img{max-width:100%}table{border-collapse:collapse;max-width:100%;display:block;overflow-x:auto}td,th{border:1px solid var(--m);padding:6px 10px}
.ad{margin:22px 0;text-align:center}footer{margin-top:40px;border-top:2px solid var(--r);padding:20px 0;color:var(--m);background:var(--p)}
.lv{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}.lv a,button{padding:6px 14px;border:2px solid var(--i);border-radius:999px;text-decoration:none;background:var(--c);color:var(--i);font:inherit;cursor:pointer}
#q{width:100%;padding:12px;border:2px solid var(--i);border-radius:6px;font:inherit;background:var(--c);color:var(--i)}
@media print{header,footer,.ad,.noprint,.lv{display:none}body{background:#fff;color:#000}article{border:0}}"""

NAV = [("index.html", "الرئيسية"), ("articles.html", "المقالات"), ("news.html", "الأخبار الرسمية"),
       ("search.html", "بحث"), ("about.html", "من نحن"), ("contact.html", "اتصل بنا")]


def ad():
    if not (C["adsense_client"] and C["adsense_slot"]):
        return ""
    return (f'<div class="ad"><ins class="adsbygoogle" style="display:block" data-ad-client="{C["adsense_client"]}" '
            f'data-ad-slot="{C["adsense_slot"]}" data-ad-format="auto" data-full-width-responsive="true"></ins>'
            '<script>(adsbygoogle=window.adsbygoogle||[]).push({});</script></div>')


def page(name, title, desc, body, head=""):
    head_ad = (f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={C["adsense_client"]}" '
               'crossorigin="anonymous"></script>') if C["adsense_client"] else ""
    nav = "".join(f'<a href="{h}">{t}</a>' for h, t in NAV)
    url = f'{C["base_url"].rstrip("/")}/{quote(name)}'
    doc = f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} – {esc(C["site_name"])}</title>
<meta name="description" content="{esc(desc)}"><link rel="canonical" href="{url}"><link rel="alternate" type="application/rss+xml" href="feed.xml">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="website"><meta property="og:locale" content="ar_MA">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">{head_ad}{head}</head><body>
<header><div class="w bar"><a class="logo" href="index.html"><b>{esc(C["site_name"].split()[0])}</b> {esc(" ".join(C["site_name"].split()[1:]))}</a><nav>{nav}</nav></div></header>
<main class="w">{body}</main>
<footer><div class="w"><a href="privacy.html">سياسة الخصوصية</a> · <a href="terms.html">شروط الاستخدام</a> · <a href="contact.html">اتصل بنا</a>
<p>© {dt.date.today().year} {esc(C["site_name"])}. المواد الإخبارية تُنسب لأصحابها وتحيل إلى مصادرها الأصلية.</p></div></footer></body></html>"""
    (OUT / name).write_text(doc, "utf-8")


def post_card(p):
    return (f'<div class="card"><small>{esc(p["date"])} · {esc(p["level"])} · {esc(p["subject"])}</small>'
            f'<h3><a href="{quote(p["slug"])}.html">{esc(p["title"])}</a></h3><small>{esc(p["summary"])}</small></div>')


def news_row(i):
    summ = f'<br>{esc(i["summary"])}' if i.get("summary") else ""
    return (f'<div class="row"><a href="{esc(i["link"])}" target="_blank" rel="noopener nofollow">{esc(i["title"])}</a>{summ}'
            f'<br><small>{esc(i["date"])} · المصدر: {esc(i["source"])}</small></div>')


# ---------- البناء ----------
LEVELS = ["الأولى", "الثانية", "الثالثة", "الرابعة", "الخامسة", "السادسة"]


def levels_nav():
    return '<div class="lv">' + "".join(f'<a href="level-{n}.html">السنة {l}</a>' for n, l in enumerate(LEVELS, 1)) + "</div>"


def build(items, posts):
    OUT.mkdir(exist_ok=True)
    (OUT / "style.css").write_text(CSS, "utf-8")
    if (ROOT / "assets").exists():
        shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)
    for p in posts:
        ld = json.dumps({"@context": "https://schema.org", "@type": "Article", "headline": p["title"], "datePublished": p["date"],
                         "inLanguage": "ar", "author": {"@type": "Organization", "name": C["site_name"]}}, ensure_ascii=False).replace("</", "<\\/")
        rel = [q for q in posts if q is not p and ((p["level"] and q["level"] == p["level"]) or (p["subject"] and q["subject"] == p["subject"]))][:3]
        relh = f'<h2>مقالات ذات صلة</h2><div class="grid">{"".join(post_card(q) for q in rel)}</div>' if rel else ""
        page(f'{p["slug"]}.html', p["title"], p["summary"] or p["title"],
             f'<article><h1>{esc(p["title"])}</h1><small>{esc(p["date"])} · {esc(p["level"])} · {esc(p["subject"])}</small> '
             f'<button class="noprint" onclick="window.print()">طباعة</button>'
             f'{ad()}{p["html"]}{ad()}</article>{relh}<p><a href="articles.html">← كل المقالات</a></p>',
             f'<script type="application/ld+json">{ld}</script>')
    page("index.html", C["site_name"], C["tagline"],
         f'<h1>{esc(C["tagline"])}</h1>{levels_nav()}{ad()}<h2>أحدث المقالات</h2><div class="grid">{"".join(post_card(p) for p in posts[:6])}</div>'
         f'<h2>آخر الأخبار الرسمية</h2>{"".join(news_row(i) for i in items[:15])}<p><a href="news.html">كل الأخبار ←</a></p>{ad()}')
    page("articles.html", "المقالات والموارد", "دروس وجذاذات وتمارين",
         f'<h1>المقالات والموارد</h1><div class="grid">{"".join(post_card(p) for p in posts)}</div>{ad()}')
    page("news.html", "الأخبار الرسمية", "آخر مستجدات التعليم الابتدائي بالمغرب",
         f'<h1>الأخبار الرسمية</h1>{ad()}{"".join(news_row(i) for i in items)}')
    mail = esc(C["contact_email"])
    page("about.html", "من نحن", "تعريف بالموقع",
         f'<h1>من نحن</h1><p>{esc(C["site_name"])} موقع مستقل يجمع مستجدات التعليم الابتدائي بالمغرب من مصادر رسمية وإعلامية، '
         'ويحيل دائمًا إلى المصدر الأصلي، وينشر موارد تربوية أعدّها محرّروه. الموقع غير تابع لأي جهة حكومية.</p>')
    page("contact.html", "اتصل بنا", "للتواصل",
         f'<h1>اتصل بنا</h1><p>للاقتراحات أو التصحيحات أو طلبات حذف محتوى: <a href="mailto:{mail}">{mail}</a></p>')
    page("terms.html", "شروط الاستخدام", "شروط الاستخدام",
         '<h1>شروط الاستخدام</h1><p>المحتوى للأغراض التعليمية والإعلامية. نبذل جهدنا لضمان الدقة ولا نتحمل مسؤولية القرارات المبنية عليه؛ '
         'يُرجى الرجوع إلى المصدر الرسمي للتأكد. الأخبار المعروضة تعود حقوقها لأصحابها الأصليين.</p>')
    page("privacy.html", "سياسة الخصوصية", "سياسة الخصوصية",
         '<h1>سياسة الخصوصية</h1><p>لا نجمع بيانات شخصية مباشرة من الزوار. يستخدم الموقع خدمة Google AdSense لعرض الإعلانات، '
         'وقد تستخدم Google وشركاؤها ملفات تعريف الارتباط (كوكيز) لعرض إعلانات مخصصة بناءً على زياراتك السابقة لهذا الموقع ومواقع أخرى. '
         'يمكنك إدارة الإعلانات المخصصة من <a href="https://adssettings.google.com" rel="noopener">إعدادات إعلانات Google</a>. '
         'باستمرارك في تصفح الموقع فإنك توافق على هذه السياسة.</p>')
    for n, name in enumerate(LEVELS, 1):
        sel = [p for p in posts if name in p["level"]]
        page(f"level-{n}.html", f"السنة {name} ابتدائي", f"دروس وموارد السنة {name} من التعليم الابتدائي",
             f'<h1>السنة {name} ابتدائي</h1>{levels_nav()}{ad()}<div class="grid">'
             f'{"".join(post_card(p) for p in sel) or "<p>لا توجد موارد لهذا المستوى بعد.</p>"}</div>')
    idx = [{"t": p["title"], "u": quote(p["slug"]) + ".html", "d": p["summary"], "s": p["subject"]} for p in posts] + \
          [{"t": i["title"], "u": i["link"], "d": i.get("summary", ""), "s": "خبر"} for i in items]
    (OUT / "search.json").write_text(json.dumps(idx, ensure_ascii=False), "utf-8")
    page("search.html", "بحث", "ابحث في المقالات والأخبار",
         '<h1>بحث</h1><input id="q" type="search" placeholder="اكتب كلمة…" autofocus><div id="r" style="margin-top:14px"></div>'
         '<script>let D=[];fetch("search.json").then(r=>r.json()).then(d=>{D=d;go()});const q=document.getElementById("q"),r=document.getElementById("r");'
         'function go(){const k=q.value.trim().toLowerCase();const m=D.filter(x=>!k||(x.t+" "+x.d+" "+x.s).toLowerCase().includes(k)).slice(0,40);'
         'r.innerHTML="";m.forEach(x=>{const d=document.createElement("div");d.className="row";const a=document.createElement("a");a.href=x.u;a.textContent=x.t;'
         'd.append(a);if(x.d){const s=document.createElement("div");s.textContent=x.d;d.append(s)}r.append(d)});if(!m.length)r.textContent="لا نتائج."}'
         'q.addEventListener("input",go)</script>')
    page("404.html", "الصفحة غير موجودة", "الصفحة غير موجودة", '<h1>الصفحة غير موجودة</h1><p><a href="index.html">العودة إلى الرئيسية</a></p>')
    def rfc(d):
        try:
            return dt.datetime.fromisoformat(d).strftime("%a, %d %b %Y 00:00:00 +0000")
        except ValueError:
            return ""
    b = C["base_url"].rstrip("/")
    ents = "".join(f'<item><title>{esc(p["title"])}</title><link>{b}/{quote(p["slug"])}.html</link><guid>{b}/{quote(p["slug"])}.html</guid>'
                   f'<pubDate>{rfc(p["date"])}</pubDate><description>{esc(p["summary"])}</description></item>' for p in posts[:20])
    (OUT / "feed.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{esc(C["site_name"])}</title>'
                                  f'<link>{b}/</link><description>{esc(C["tagline"])}</description><language>ar</language>{ents}</channel></rss>', "utf-8")
    base = C["base_url"].rstrip("/")
    urls = [f"{base}/{quote(n)}" for n in ["index.html", "articles.html", "news.html", "search.html"]] + \
           [f"{base}/level-{n}.html" for n in range(1, 7)] + \
           [f'{base}/{quote(p["slug"])}.html' for p in posts]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                                     + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>", "utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n", "utf-8")
    if C["adsense_client"]:
        pub = C["adsense_client"].replace("ca-", "")
        (OUT / "ads.txt").write_text(f"google.com, {pub}, DIRECT, f08c47fec0942fa0\n", "utf-8")


if __name__ == "__main__":
    items = collect()
    extras.enrich(items)
    DATA.write_text(json.dumps(items, ensure_ascii=False, indent=1), "utf-8")
    extras.weekly_digest(items, ROOT / "posts")
    build(items, load_posts())
    print("تم البناء في", OUT)
