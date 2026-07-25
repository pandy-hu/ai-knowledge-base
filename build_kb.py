#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 categories/ 下的知识卡编译成手机友好的单文件 kb.html（搜索 + 标签筛选）。
用法：python build_kb.py  （生成后把 kb.html 发到手机微信即可看）"""
import os, re, json, glob, datetime
import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
CATS_DIR = os.path.join(ROOT, "categories")

def parse_file(path):
    txt = open(path, encoding="utf-8").read()
    lines = txt.split("\n")
    title = lines[0].lstrip("#").strip() if (lines and lines[0].startswith("#")) else os.path.splitext(os.path.basename(path))[0]
    meta, body, in_meta = {}, [], True
    for line in lines[1:]:
        if in_meta:
            m = re.match(r"\s*-\s*\*\*(.+?)\*\*[:：]\s*(.*)", line)
            if m:
                meta[m.group(1).strip()] = m.group(2).strip(); continue
            if line.strip().startswith("---"):
                in_meta = False; continue
            if line.strip() == "":
                continue
            in_meta = False
        body.append(line)
    body_html = markdown.markdown("\n".join(body).strip(), extensions=["tables", "fenced_code"])
    tags = re.findall(r"#([^\s#]+)", meta.get("二级标签", ""))
    return {
        "title": title, "source": meta.get("来源", ""), "date": meta.get("收录日期", ""),
        "category": meta.get("一级分类", ""), "tags": tags,
        "relevance": meta.get("项目关联度", ""), "monetize": meta.get("变现潜力", ""),
        "core": meta.get("一句话核心", ""), "body_html": body_html,
    }

entries = [parse_file(f) for f in glob.glob(os.path.join(CATS_DIR, "**", "*.md"), recursive=True)]
entries.sort(key=lambda e: e["date"], reverse=True)
all_tags = sorted({t for e in entries for t in e["tags"]})
all_cats = sorted({e["category"] for e in entries if e["category"]})

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>我的知识库</title>
<style>
:root{--bg:#f7f7f8;--card:#fff;--line:#e5e7eb;--txt:#1f2328;--mut:#6b7280;--acc:#2563eb;--red:#dc2626;--amb:#b45309;}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--txt);font-size:16px;line-height:1.6;}
header{padding:18px 16px 10px;position:sticky;top:0;background:var(--bg);z-index:5;border-bottom:1px solid var(--line);}
h1{font-size:20px;margin:0 0 2px;}
.sub{color:var(--mut);font-size:13px;}
#search{width:100%;margin-top:10px;padding:12px 14px;border:1px solid var(--line);border-radius:12px;font-size:16px;background:#fff;outline:none;}
#search:focus{border-color:var(--acc);}
.filters{padding:10px 16px;display:flex;flex-wrap:wrap;gap:8px;}
.chip{padding:7px 12px;border:1px solid var(--line);border-radius:999px;background:#fff;font-size:13px;color:var(--mut);cursor:pointer;user-select:none;}
.chip.on{background:var(--acc);color:#fff;border-color:var(--acc);}
main{padding:8px 16px 48px;}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px 16px;margin-bottom:14px;}
.ct{font-size:17px;font-weight:600;margin:0 0 6px;}
.meta{font-size:12px;color:var(--mut);display:flex;flex-wrap:wrap;gap:6px 12px;margin-bottom:8px;align-items:center;}
.badge{padding:2px 8px;border-radius:6px;font-weight:600;}
.b-high{background:#fee2e2;color:var(--red);}
.b-mid{background:#fef3c7;color:var(--amb);}
.b-low{background:#e5e7eb;color:var(--mut);}
.core{font-size:14px;color:#374151;background:#f3f4f6;border-left:3px solid var(--acc);padding:8px 10px;border-radius:0 8px 8px 0;margin-bottom:8px;}
.body{font-size:14px;display:none;}
.body.show{display:block;}
.body h2,.body h3{margin:14px 0 6px;}
.body ul{padding-left:20px;}
.toggle{margin-top:6px;color:var(--acc);font-size:14px;cursor:pointer;user-select:none;}
.tag{display:inline-block;font-size:11px;color:var(--mut);background:#f3f4f6;border-radius:6px;padding:1px 6px;margin:2px 4px 0 0;}
.empty{text-align:center;color:var(--mut);padding:40px 0;}
</style>
</head>
<body>
<header>
<h1>我的知识库</h1>
<div class="sub">共 __COUNT__ 条 · 更新 __DATE__</div>
<input id="search" placeholder="搜索标题 / 标签 / 内容…" />
<div class="filters" id="catFilters"></div>
<div class="filters" id="tagFilters"></div>
</header>
<main id="list"></main>
<script>
var ENTRIES=__ENTRIES__;
var CATS=__CATS__;
var TAGS=__TAGS__;
var curCat="全部",curTags=[],q="";
function badge(t,label){if(!t)return"";var c=t==="高"?"b-high":(t==="中"?"b-mid":"b-low");return'<span class="badge '+c+'">'+label+t+'</span>';}
function renderFilters(){
 var cf=document.getElementById("catFilters");cf.innerHTML="";
 ["全部"].concat(CATS).forEach(function(c){var d=document.createElement("div");d.className="chip"+(c===curCat?" on":"");d.textContent=c;d.onclick=function(){curCat=c;renderFilters();render();};cf.appendChild(d);});
 var tf=document.getElementById("tagFilters");tf.innerHTML="";
 TAGS.forEach(function(t){var on=curTags.indexOf(t)>=0;var d=document.createElement("div");d.className="chip"+(on?" on":"");d.textContent="#"+t;d.onclick=function(){if(on){curTags=curTags.filter(function(x){return x!==t;});}else{curTags.push(t);}renderFilters();render();};tf.appendChild(d);});
}
function render(){
 var box=document.getElementById("list");box.innerHTML="";
 var list=ENTRIES.filter(function(e){
  if(curCat!=="全部"&&e.category!==curCat)return false;
  if(curTags.length&&!curTags.every(function(t){return e.tags.indexOf(t)>=0;}))return false;
  if(q){var s=(e.title+e.core+e.body_html+e.tags.join("")).toLowerCase();if(s.indexOf(q.toLowerCase())<0)return false;}
  return true;
 });
 if(!list.length){box.innerHTML='<div class="empty">没有匹配的内容</div>';return;}
 list.forEach(function(e){
  var card=document.createElement("div");card.className="card";
  var tags=e.tags.map(function(t){return '<span class="tag">#'+t+'</span>';}).join("");
  card.innerHTML='<div class="ct">'+e.title+'</div>'+
   '<div class="meta"><span>'+e.date+'</span><span>'+e.category+'</span>'+badge(e.relevance,"关联")+badge(e.monetize,"变现")+'</div>'+
   (e.core?'<div class="core">'+e.core+'</div>':'')+
   '<div class="body">'+e.body_html+'<div style="margin-top:8px">'+tags+'</div></div>'+
   '<div class="toggle" onclick="tog(this)">展开 ▾</div>';
  box.appendChild(card);
 });
}
function tog(el){var b=el.previousElementSibling;if(b.classList.contains("show")){b.classList.remove("show");el.textContent="展开 ▾";}else{b.classList.add("show");el.textContent="收起 ▴";}}
document.getElementById("search").addEventListener("input",function(ev){q=ev.target.value;render();});
renderFilters();render();
</script>
</body></html>"""

html = (TEMPLATE
        .replace("__COUNT__", str(len(entries)))
        .replace("__DATE__", datetime.date.today().isoformat())
        .replace("__ENTRIES__", json.dumps(entries, ensure_ascii=False))
        .replace("__CATS__", json.dumps(all_cats, ensure_ascii=False))
        .replace("__TAGS__", json.dumps(all_tags, ensure_ascii=False)))
out = os.path.join(ROOT, "kb.html")
open(out, "w", encoding="utf-8").write(html)
print("Built kb.html with", len(entries), "entries ->", out)
