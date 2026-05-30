lines = open('app.py', 'r', encoding='utf-8').read().splitlines()
lines[253] = '        sinais = [enrich_signal_with_squeeze(s) for s in sinais]'
lines[1967] = '        sinais = [enrich_signal_with_squeeze(s) for s in sinais]'
open('app.py', 'w', encoding='utf-8').write('\n'.join(lines))
print('FEITO')
