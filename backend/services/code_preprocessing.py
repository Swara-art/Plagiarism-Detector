import re, ast, hashlib

def normalize_python_code(code: str) -> str:
    code = re.sub(r'#.*', '', code)
    code = re.sub(r'""".*?"""', '""""""', code, flags=re.DOTALL)
    code = re.sub(r"'''.*?'''", "''''''", code, flags=re.DOTALL)
    lines = [line.rstrip() for line in code.splitlines()]
    return '\n'.join(line for line in lines if line.strip())

def extract_ast_structure(code: str) -> str:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    class StructureExtractor(ast.NodeVisitor):
        def __init__(self): self.tokens = []
        def generic_visit(self, node):
            t = type(node).__name__
            if t not in ('Constant','Num','Str','Bytes','NameConstant','Ellipsis'):
                self.tokens.append(t)
            ast.NodeVisitor.generic_visit(self, node)

    ex = StructureExtractor()
    ex.visit(tree)
    return ' '.join(ex.tokens)

def fingerprint_code(code: str) -> str:
    return hashlib.sha256(extract_ast_structure(normalize_python_code(code)).encode()).hexdigest()

def extract_functions(code: str) -> list:
    functions = []
    try:
        tree  = ast.parse(code)
        lines = code.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start     = node.lineno
                end       = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno + 10
                func_code = '\n'.join(lines[start-1:end])
                functions.append({
                    "name": node.name, "start_line": start, "end_line": end,
                    "code": func_code, "structure": extract_ast_structure(func_code)
                })
    except Exception:
        pass
    return functions

def jaccard_similarity(s1: set, s2: set) -> float:
    if not s1 and not s2: return 1.0
    return len(s1 & s2) / len(s1 | s2) if (s1 | s2) else 0.0

def structural_similarity(code1: str, code2: str) -> float:
    def ngrams(tokens, n):
        return set(tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1))
    s1 = extract_ast_structure(normalize_python_code(code1)).split()
    s2 = extract_ast_structure(normalize_python_code(code2)).split()
    if not s1 or not s2: return 0.0
    bi  = jaccard_similarity(ngrams(s1,2), ngrams(s2,2))
    tri = jaccard_similarity(ngrams(s1,3), ngrams(s2,3))
    return round(bi*0.4 + tri*0.6, 4)