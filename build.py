#!/usr/bin/env python3
"""feed.json -> статический сайт «Что изменилось» в docs/.

    python3 build.py [путь/к/feed.json] [папка-вывода]

Без сборщиков и зависимостей: GitHub Pages отдаёт docs/ прямо из main,
CI не нужен. Пустой фид — не ошибка: рисуется честное «пока пусто».
"""
import glob
import html
import json
import os
import shutil
import sys
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")

CAT = {
    "norm":     ("#4F46E5", {"ru": "Нормативное изменение", "kk": "Нормативтік өзгеріс"}),
    "method":   ("#0D9488", {"ru": "Методические рекомендации", "kk": "Әдістемелік ұсынымдар"}),
    "calendar": ("#B45309", {"ru": "Календарь и сроки", "kk": "Күнтізбе және мерзімдер"}),
    "product":  ("#6360FF", {"ru": "Продукт", "kk": "Өнім"}),
    "service":  ("#C2261F", {"ru": "Работа сервиса", "kk": "Сервис жұмысы"}),
}
MON = {
    "ru": "января февраля марта апреля мая июня июля августа сентября октября ноября декабря".split(),
    "kk": "қаңтар ақпан наурыз сәуір мамыр маусым шілде тамыз қыркүйек қазан қараша желтоқсан".split(),
}
T = {
    "ru": {"title": "Что изменилось", "sub": "нормативные изменения для учителей Казахстана",
           "eff": "Действует с", "pub": "Опубликовано", "src": "Нормативная основа",
           "issuer": "Издатель", "num": "Документ", "date": "Дата", "loc": "Где смотреть",
           "open": "Открыть первоисточник", "back": "Все записи", "empty": "Пока ни одной записи.",
           "emptyw": "Записи появляются здесь после того, как методист принял черновик.",
           "year": "Учебный год", "all": "Все", "rev": "Очередь на ревью",
           "disc": "Это пересказ документа, а не официальное разъяснение. "
                   "Решения принимайте по первоисточнику — ссылка выше."},
    "kk": {"title": "Не өзгерді", "sub": "Қазақстан мұғалімдеріне арналған нормативтік өзгерістер",
           "eff": "Күшіне енеді", "pub": "Жарияланды", "src": "Нормативтік негіз",
           "issuer": "Шығарушы", "num": "Құжат", "date": "Күні", "loc": "Қайдан қарау",
           "open": "Бастапқы дереккөзді ашу", "back": "Барлық жазба", "empty": "Әзірге жазба жоқ.",
           "emptyw": "Жазбалар әдіскер жобаны қабылдағаннан кейін осында шығады.",
           "year": "Оқу жылы", "all": "Барлығы", "rev": "Тексеру кезегі",
           "disc": "Бұл — құжаттың мазмұндамасы, ресми түсіндірме емес. "
                   "Шешімді бастапқы дереккөз бойынша қабылдаңыз — сілтеме жоғарыда."},
}

e = lambda s: html.escape(str(s or ""))


def fdate(s, lang):
    """Даты только абсолютные: «8 месяцев назад» скрывает, актуальна ли норма."""
    if not s or s == "—":
        return "—"
    try:
        y, m, d = str(s)[:10].split("-")
        return f"{int(d)} {MON[lang][int(m) - 1]} {y}"
    except (ValueError, IndexError):
        return str(s)


def loc(v, lang):
    return (v or {}).get(lang) or (v or {}).get("ru") or "—" if isinstance(v, dict) else (v or "—")


CSS = """
:root{--ink:#12141C;--ground:#F6F6FA;--card:#fff;--line:#E4E4EC;--mut:#5C6478;--dim:#8A92A6;
--acc:#6360FF;--acc-soft:#EEEDFF;
--d:'Onest',system-ui,sans-serif;--b:'Inter',system-ui,sans-serif;--m:ui-monospace,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
--ink:#E9EAF0;--ground:#0C0E14;--card:#151822;--line:#262B38;--mut:#9AA2B5;--dim:#7A8296;
--acc:#8E8CFF;--acc-soft:#1E1F3A}}
:root[data-theme="dark"]{--ink:#E9EAF0;--ground:#0C0E14;--card:#151822;--line:#262B38;
--mut:#9AA2B5;--dim:#7A8296;--acc:#8E8CFF;--acc-soft:#1E1F3A}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--ground);color:var(--ink);font:16px/1.6 var(--b);-webkit-font-smoothing:antialiased}
.wrap{max-width:760px;margin:0 auto;padding:0 20px}
header{border-bottom:1px solid var(--line);background:var(--card)}
.hd{display:flex;align-items:baseline;justify-content:space-between;gap:16px;padding:22px 0}
h1{font:800 21px/1.2 var(--d);letter-spacing:-.02em}
h1 a{color:inherit;text-decoration:none}
h1 span{display:block;font:400 12.5px/1.5 var(--b);color:var(--mut);margin-top:4px;letter-spacing:0}
.lang{display:flex;gap:2px;background:var(--ground);border-radius:8px;padding:3px}
.lang a{padding:5px 11px;border-radius:6px;font:600 12.5px var(--b);text-decoration:none;color:var(--mut)}
.lang a[aria-current="true"]{background:var(--card);color:var(--ink);box-shadow:0 1px 2px rgba(0,0,0,.07)}
main{padding:26px 0 70px}
.cats{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:22px}
.cats button{background:var(--card);border:1px solid var(--line);border-radius:20px;
padding:6px 14px;cursor:pointer;font:600 12.5px var(--b);color:var(--mut)}
.cats button[aria-pressed="true"]{background:var(--ink);border-color:var(--ink);color:var(--ground)}
.list{display:grid;gap:13px}
.it{display:block;background:var(--card);border:1px solid var(--line);border-radius:13px;
padding:18px 20px;text-decoration:none;color:inherit}
.it:hover{border-color:var(--acc)}
.cat{font:700 10.5px/1 var(--m);letter-spacing:.07em;text-transform:uppercase;color:var(--c)}
.it h2{font:700 17px/1.4 var(--d);margin:9px 0 7px;letter-spacing:-.01em;text-wrap:balance}
.it p{color:var(--mut);font-size:14.5px;line-height:1.6}
.meta{display:flex;flex-wrap:wrap;gap:14px;margin-top:12px;font:12.5px var(--b);color:var(--dim)}
.meta b{color:var(--ink);font-weight:600}
.empty{background:var(--card);border:1px dashed var(--line);border-radius:13px;
padding:44px 26px;text-align:center}
.empty b{display:block;font:700 16px var(--d);margin-bottom:7px}
.empty span{color:var(--mut);font-size:14px}
.back{display:inline-block;margin-bottom:18px;font:600 13px var(--b);color:var(--acc);text-decoration:none}
article h2{font:800 25px/1.3 var(--d);letter-spacing:-.02em;margin:10px 0 14px;text-wrap:balance}
.lead{font-size:17px;line-height:1.65;color:var(--mut);margin-bottom:22px}
.dates{display:flex;flex-wrap:wrap;gap:22px;padding:15px 18px;background:var(--card);
border:1px solid var(--line);border-radius:12px;margin-bottom:22px}
.dates div span{display:block;font:700 10.5px/1 var(--m);letter-spacing:.07em;
text-transform:uppercase;color:var(--dim);margin-bottom:5px}
.dates .eff b{font:700 18px var(--d)}
.dates .pub b{font:500 14px var(--b);color:var(--mut)}
.src{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:22px 0}
.src h3{font:700 13px var(--d);margin-bottom:11px}
.src dl{display:grid;grid-template-columns:auto 1fr;gap:6px 16px;font-size:13.5px}
.src dt{color:var(--dim)}
.src dd{color:var(--ink)}
.src a{display:inline-block;margin-top:12px;font:600 13px var(--b);color:var(--acc)}
.body{font-size:16px;line-height:1.75}
.body p{margin:0 0 14px}
.body ul,.body ol{margin:0 0 14px 22px}
.body li{margin-bottom:6px}
.disc{margin-top:26px;padding:13px 16px;border-left:3px solid var(--line);
color:var(--dim);font-size:13px;line-height:1.6}
footer{border-top:1px solid var(--line);padding:20px 0;color:var(--dim);font-size:12.5px}
footer a{color:var(--dim)}
footer a:hover{color:var(--acc)}
@media(max-width:600px){.hd{flex-direction:column;gap:12px}article h2{font-size:21px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
"""

HEAD = """<!doctype html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Onest:wght@700;800&display=swap" rel="stylesheet">
<style>{css}</style></head><body>
<header><div class="wrap"><div class="hd">
<h1><a href="{home}">{h1}</a><span>{sub}</span></h1>
<div class="lang">{langs}</div>
</div></div></header><main><div class="wrap">"""

FOOT = """</div></main><footer><div class="wrap">WONK · обновлено {upd} · публикует методист
· <a href="{up}review.html">{rev}</a></div></footer>
</body></html>"""


def shell(lang, title, desc, inner, depth=0):
    up = "../" * depth
    other = "kk" if lang == "ru" else "ru"
    langs = "".join(
        f'<a href="{up}{"index" if l == "ru" else "index.kk"}.html" aria-current="{str(l == lang).lower()}">'
        f'{l.upper()}</a>' for l in ("ru", "kk"))
    t = T[lang]
    return (HEAD.format(lang=lang, title=e(title), desc=e(desc), css=CSS,
                        home=f'{up}{"index" if lang == "ru" else "index.kk"}.html',
                        h1=e(t["title"]), sub=e(t["sub"]), langs=langs)
            + inner + FOOT.format(upd=date.today().isoformat(), up=up, rev=e(t["rev"])))


def item(x, lang):
    tr = (x.get("translations") or {}).get(lang) or (x.get("translations") or {}).get("ru") or {}
    color, names = CAT.get(x.get("category"), ("#8A92A6", {"ru": "—", "kk": "—"}))
    t = T[lang]
    return (f'<a class="it" href="e/{e(x["slug"])}.{lang}.html">'
            f'<div class="cat" style="--c:{color}">{e(names[lang])}</div>'
            f'<h2>{e(tr.get("title"))}</h2>'
            f'<p>{e(tr.get("summary_plain") or tr.get("summary"))}</p>'
            f'<div class="meta"><span>{e(t["eff"])} <b>{e(fdate(x.get("effective_from"), lang))}</b></span>'
            f'<span>{e(t["pub"])} {e(fdate(x.get("published_at"), lang))}</span></div></a>')


def page_index(feed, lang):
    t = T[lang]
    if not feed:
        inner = f'<div class="empty"><b>{e(t["empty"])}</b><span>{e(t["emptyw"])}</span></div>'
    else:
        cats = sorted({x.get("category") for x in feed if x.get("category")})
        btns = f'<button data-c="" aria-pressed="true">{e(t["all"])}</button>' + "".join(
            f'<button data-c="{e(c)}" aria-pressed="false">{e(CAT.get(c, ("", {lang: c}))[1][lang])}</button>'
            for c in cats)
        rows = "".join(f'<div data-c="{e(x.get("category"))}">{item(x, lang)}</div>' for x in feed)
        inner = (f'<div class="cats">{btns}</div><div class="list">{rows}</div>'
                 '<script>document.querySelector(".cats").addEventListener("click",ev=>{'
                 'const b=ev.target.closest("button");if(!b)return;'
                 'document.querySelectorAll(".cats button").forEach(x=>x.setAttribute("aria-pressed",x===b));'
                 'const c=b.dataset.c;document.querySelectorAll(".list>div").forEach(d=>{'
                 'd.hidden=!!c&&d.dataset.c!==c})});</script>')
    return shell(lang, t["title"], t["sub"], inner)


def page_entry(x, lang):
    t = T[lang]
    tr = (x.get("translations") or {}).get(lang) or (x.get("translations") or {}).get("ru") or {}
    src = x.get("source") or {}
    color, names = CAT.get(x.get("category"), ("#8A92A6", {"ru": "—", "kk": "—"}))
    dl = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in [
        (t["issuer"], src.get("issuer")), (t["num"], src.get("number")),
        (t["date"], fdate(src.get("date"), lang)), (t["loc"], loc(src.get("locator"), lang))] if v)
    url = src.get("url_kk") if lang == "kk" and src.get("url_kk") else src.get("url")
    link = f'<a href="{e(url)}" target="_blank" rel="noopener">{e(t["open"])} →</a>' if url else ""
    body = tr.get("body") or ""
    if "<p>" not in body:
        body = "".join(f"<p>{e(p)}</p>" for p in body.split("\n\n") if p.strip())
    disc = (f'<div class="disc">{e(t["disc"])}</div>'
            if x.get("category") in ("norm", "method", "calendar") else "")
    inner = (f'<a class="back" href="../{"index" if lang == "ru" else "index.kk"}.html">← {e(t["back"])}</a>'
             f'<article><div class="cat" style="--c:{color}">{e(names[lang])}</div>'
             f'<h2>{e(tr.get("title"))}</h2>'
             f'<p class="lead">{e(tr.get("summary_plain") or tr.get("summary"))}</p>'
             f'<div class="dates"><div class="eff"><span>{e(t["eff"])}</span>'
             f'<b>{e(fdate(x.get("effective_from"), lang))}</b></div>'
             f'<div class="pub"><span>{e(t["pub"])}</span><b>{e(fdate(x.get("published_at"), lang))}</b></div>'
             + (f'<div class="pub"><span>{e(t["year"])}</span><b>{e(x.get("applies_to_academic_year"))}</b></div>'
                if x.get("applies_to_academic_year") else "")
             + f'</div><div class="src"><h3>{e(t["src"])}</h3><dl>{dl}</dl>{link}</div>'
             f'<div class="body">{body}</div>{disc}</article>')
    return shell(lang, tr.get("title") or x["slug"], tr.get("summary_plain") or "", inner, depth=1)


def main():
    fn = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "feed.json")
    # Второй аргумент — чтобы собрать предпросмотр, не трогая docs/,
    # который уходит в репозиторий.
    out = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else OUT
    feed = json.load(open(fn, encoding="utf-8")) if os.path.exists(fn) else []
    feed = [x for x in feed if x.get("status") != "retracted"]
    feed.sort(key=lambda x: x.get("published_at") or "", reverse=True)

    # Сносим только то, чем управляет этот скрипт: review.html и robots.txt
    # кладёт sync_review.sh, и rmtree всей папки стирал бы их каждой пересборкой.
    if os.path.isdir(os.path.join(out, "e")):
        shutil.rmtree(os.path.join(out, "e"))
    for f in glob.glob(os.path.join(out, "index*.html")) + [os.path.join(out, "feed.json")]:
        if os.path.exists(f):
            os.remove(f)
    os.makedirs(os.path.join(out, "e"), exist_ok=True)

    for lang in ("ru", "kk"):
        name = "index.html" if lang == "ru" else "index.kk.html"
        open(os.path.join(out, name), "w", encoding="utf-8").write(page_index(feed, lang))
        for x in feed:
            open(os.path.join(out, "e", f'{x["slug"]}.{lang}.html'), "w",
                 encoding="utf-8").write(page_entry(x, lang))

    # Фид отдаём как есть: по нему можно построить другую витрину.
    json.dump(feed, open(os.path.join(out, "feed.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    # Pages иначе прогонит страницы через Jekyll и сломает пути с подчёркиваниями.
    open(os.path.join(out, ".nojekyll"), "w").close()

    print(f"собрано: {len(feed)} записей → {out}")
    for x in feed:
        print(f'  {x["slug"]}')


if __name__ == "__main__":
    main()
