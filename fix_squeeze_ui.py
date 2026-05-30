content = open('static/index.html', 'r', encoding='utf-8').read()

old = "}</span>\n      </span>\n    </div>\n    <div class=\"detail\" id=\"det-"
new = "}</span>\n      <span class=\"td\" style=\"min-width:70px\">\n        <span style=\"font-size:9px;font-weight:700;padding:2px 5px;border-radius:3px;background:;color:\"></span><br>\n        <span style=\"font-size:8px;color:#666\"></span>\n      </span>\n    </div>\n    <div class=\"detail\" id=\"det-"

if old in content:
    print('ENCONTRADO - a injetar...')
    content = content.replace(old, new, 1)
    open('static/index.html', 'w', encoding='utf-8').write(content)
    print('FEITO')
else:
    print('NAO ENCONTRADO')
