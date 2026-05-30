content = open('app.py', 'r', encoding='utf-8').read()
# Aumentar delays
content = content.replace('time.sleep(0.15)', 'time.sleep(0.5)')
content = content.replace('time.sleep(0.1)', 'time.sleep(0.4)')
content = content.replace('time.sleep(0.05)', 'time.sleep(0.3)')
# Aumentar wait em caso de 429
content = content.replace('time.sleep(2.0)  # Rate limit', 'time.sleep(10.0)  # Rate limit')
open('app.py', 'w', encoding='utf-8').write(content)
print('FEITO')
