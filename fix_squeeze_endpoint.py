content = open('app.py', 'r', encoding='utf-8').read()

endpoint = '''
@app.route("/api/squeeze/candidates", methods=["GET"])
def squeeze_candidates():
    from pathlib import Path
    import json
    f = Path(__file__).parent / "squeeze_candidates.json"
    if f.exists():
        with open(f, "r", encoding="utf-8") as fp:
            return jsonify(json.load(fp))
    return jsonify({"candidates": [], "timestamp": None, "total": 0})
'''

# Inserir antes do ultimo if __name__
content = content.replace('if __name__ == "__main__":', endpoint + '\nif __name__ == "__main__":')
open('app.py', 'w', encoding='utf-8').write(content)
print('OK' if '/api/squeeze/candidates' in content else 'FALHOU')
