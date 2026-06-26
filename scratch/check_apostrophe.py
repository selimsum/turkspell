with open('generate_grammar_rules.py', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if "'" in line:
            print(idx, line.strip())
