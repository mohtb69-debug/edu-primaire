"""ميزات مجانية تقوّي المحتوى: ملخصات أصلية للأخبار + حصاد أسبوعي تلقائي.
تعمل فقط إذا أضفت مفتاح GEMINI_API_KEY أو GROQ_API_KEY (كلاهما مجاني). بدونهما يُتخطى كل شيء بهدوء."""
import os, datetime as dt
import requests
from bs4 import BeautifulSoup

H = {"User-Agent": "Mozilla/5.0 (compatible; EduNewsBot/1.0)"}


def ask(prompt):
    key = os.getenv("GEMINI_API_KEY")
    if key:
        try:
            model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"x-goog-api-key": key}, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as ex:
            print("Gemini:", ex)
    key = os.getenv("GROQ_API_KEY")
    if key:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {key}"},
                json={"model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                      "messages": [{"role": "user", "content": prompt}]}, timeout=60)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as ex:
            print("Groq:", ex)
    return None


def page_text(url):
    try:
        soup = BeautifulSoup(requests.get(url, headers=H, timeout=25).content, "html.parser")
        for t in soup(["script", "style", "nav", "header", "footer", "aside"]):
            t.decompose()
        text = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
        return text[:4000] if len(text) > 400 else ""
    except Exception:
        return ""


def enrich(items, limit=8):
    """يضيف ملخصًا بصياغة جديدة لكل خبر جديد تم جلب نصه فعليًا (لا يخمّن من العنوان وحده)."""
    done = 0
    for it in items:
        if done >= limit:
            break
        if "summary" in it or it.get("tried"):
            continue
        it["tried"] = True
        text = page_text(it["link"])
        if not text:
            continue
        s = ask("لخّص الخبر التالي في جملتين أو ثلاث بالعربية الفصحى وبصياغتك الخاصة دون نسخ العبارات، "
                "واعتمد على النص فقط دون إضافة أي معلومة غير واردة فيه.\n\nالنص:\n" + text)
        if s:
            it["summary"] = s
            done += 1


def weekly_digest(items, posts_dir):
    """مقال «حصاد الأسبوع» مرة كل أسبوع (من الجمعة إلى الأحد) اعتمادًا على عناوين الأخبار المجمعة فقط."""
    today = dt.date.today()
    year, week, _ = today.isocalendar()
    f = posts_dir / f"digest-{year}-w{week:02d}.md"
    if f.exists() or today.weekday() < 4:
        return
    since = (today - dt.timedelta(days=7)).isoformat()
    recent = [i for i in items if i["date"] >= since][:15]
    if len(recent) < 3:
        return
    titles = "\n".join(f"- {i['title']}" for i in recent)
    body = ask("اكتب بالعربية الفصحى مقالًا قصيرًا (حوالي 200 كلمة) بعنوان فرعي واحد أو اثنين بصيغة Markdown (##) يلخص "
               "أبرز ما ورد هذا الأسبوع في التعليم الابتدائي بالمغرب، اعتمادًا على العناوين التالية فقط. "
               "لا تضف أي تفاصيل أو أرقام أو تواريخ غير موجودة في العناوين، ولا تضع عنوانًا رئيسيًا.\n\n" + titles)
    if not body:
        return
    sources = "\n".join(f"- [{i['title']}]({i['link']}) — {i['source']}" for i in recent)
    f.write_text(
        f"---\ntitle: حصاد الأسبوع في التعليم الابتدائي – الأسبوع {week}\ndate: {today.isoformat()}\nlevel: عام\n"
        f"subject: أخبار\nsummary: أبرز مستجدات التعليم الابتدائي بالمغرب خلال الأسبوع.\n---\n{body}\n\n"
        f"## المصادر\n{sources}\n\n*ملاحظة: هذا الملخص أُعدّ بمساعدة الذكاء الاصطناعي؛ راجع المصادر الرسمية للتأكد.*\n", "utf-8")
