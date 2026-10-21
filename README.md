# دليل التشغيل (10 دقائق، مجاني)

1. أنشئ حسابًا على github.com ثم مستودعًا جديدًا **عامًا (Public)** باسم مثل `edu-primaire`.
2. ارفع كل محتويات هذا المجلد إلى المستودع (Add file ← Upload files)، مع مجلد `.github`.
3. افتح `config.json` وعدّل: `base_url` إلى `https://اسم-حسابك.github.io/edu-primaire` والبريد الإلكتروني واسم الموقع.
4. في المستودع: Settings ← Pages ← Source = **GitHub Actions**.
5. تبويب Actions ← build-and-deploy ← Run workflow. بعد دقيقتين يعمل الموقع على الرابط أعلاه.
   بعدها يتحدّث تلقائيًا كل 6 ساعات دون تدخل منك.

## نشر مقال بنفسك
من المتصفح أو الهاتف: مجلد `posts` ← Add file ← Create new file، اسم الملف بحروف لاتينية `lesson-1.md`، والمحتوى:

    ---
    title: عنوان المقال
    date: 2026-10-10
    level: الثالثة
    subject: الرياضيات
    summary: ملخص قصير
    ---
    نص المقال بصيغة Markdown

بمجرد الحفظ (Commit) يُنشر الموقع تلقائيًا.

## المصادر
عدّل `sources.json`: أضف أي رابط RSS (`"type":"rss"`) أو صفحة أخبار (`"type":"html"`). RSS أضمن من HTML.
الموقع الرسمي للوزارة قد يغيّر هيكله؛ تحقق من الرابط في تبويب Actions (سجل البناء يذكر المصدر المتعطل).

## AdSense
1. اجمع 15 إلى 30 مقالًا أصليًا على الأقل، واربط نطاقًا خاصًا (Settings ← Pages ← Custom domain) لأن AdSense لا يقبل عادة `github.io`.
2. قدّم الموقع في adsense.google.com، وبعد القبول ضع في `config.json`: `adsense_client` (مثل `ca-pub-123...`) و`adsense_slot` (رقم وحدة الإعلان).
3. سيُضاف الكود وملف `ads.txt` والإعلانات تلقائيًا.

## الميزات الإضافية (مجانية)
- **ملخصات أصلية للأخبار وحصاد أسبوعي تلقائي:** احصل على مفتاح مجاني من aistudio.google.com/apikey (Gemini) و/أو console.groq.com/keys (Groq)، ثم في المستودع: Settings ← Secrets and variables ← Actions ← New repository secret، وأضف `GEMINI_API_KEY` و/أو `GROQ_API_KEY`. بدون المفاتيح يعمل الموقع عاديًا دون هذه الميزة. إن تغيّر اسم النموذج في المستقبل فعدّل المتغيرين `GEMINI_MODEL` و`GROQ_MODEL` في ملف build.yml.
- **صفحات لكل مستوى** (الأولى إلى السادسة): اكتب في المقال `level: الثالثة` فيظهر تلقائيًا في صفحته.
- **بحث داخلي، تغذية RSS، خريطة الموقع، صفحة 404، بيانات منظّمة للمقالات، زر طباعة** للمقالات.

## بعد النشر (مجانًا)
1. أضف موقعك إلى **Google Search Console** وأرسل `sitemap.xml` لتظهر المقالات في نتائج البحث.
2. في حساب AdSense ← Privacy & messaging: فعّل رسالة الموافقة على الكوكيز (GDPR) مجانًا.
3. احتفظ بنشاط المستودع: إن توقفت الجدولة بعد شهرين دون أي نشاط، اضغط Enable في تبويب Actions.

## الصور وملفات PDF
ضعها في مجلد `assets` (Add file ← Upload files). وفي المقال: `![وصف الصورة](assets/image1.png)` وللتحميل: `[تحميل الملف](assets/lesson1.pdf)`. استخدم أسماء لاتينية بلا فراغات.
