import re
from tree_sitter_languages import get_parser

SUPPORTED_LANGUAGES = {
    "python": "python",
    "py": "python",
    "javascript": "javascript",
    "js": "javascript",
    "c": "c",
    "cpp": "cpp",
    "c++": "cpp",
    "java": "java",
    "go": "go",
    "rust": "rust",
    "rs": "rust"
}

# Node types representing functions in different programming languages in tree-sitter
FUNCTION_NODE_TYPES = {
    "python": {"function_definition", "async_function_definition"},
    "javascript": {"function_declaration", "arrow_function", "generator_function"},
    "c": {"function_definition"},
    "cpp": {"function_definition"},
    "java": {"method_declaration"},
    "go": {"function_declaration", "method_declaration"},
    "rust": {"function_item"}
}

def extract_ast_structure(code: str, language: str = "python") -> str:
    lang = SUPPORTED_LANGUAGES.get(language.lower(), "python")
    try:
        parser = get_parser(lang)
        tree = parser.parse(code.encode("utf-8"))
        
        # Traverse tree and extract node types for language-agnostic AST shape comparison
        tokens = []
        cursor = tree.walk()
        has_more = True
        
        while has_more:
            node = cursor.node
            tokens.append(node.type)
            
            # Depth-first traversal
            if cursor.goto_first_child():
                continue
            if cursor.goto_next_sibling():
                continue
            
            # Backtrack to parent
            backtracking = True
            while backtracking:
                if not cursor.goto_parent():
                    has_more = False
                    backtracking = False
                elif cursor.goto_next_sibling():
                    backtracking = False
        return " ".join(tokens)
    except Exception:
        # Fallback to character normalization if parsing fails
        return code

def extract_functions(code: str, language: str = "python") -> list:
    lang = SUPPORTED_LANGUAGES.get(language.lower(), "python")
    func_types = FUNCTION_NODE_TYPES.get(lang, {"function_definition"})
    functions = []
    
    try:
        parser = get_parser(lang)
        tree = parser.parse(code.encode("utf-8"))
        
        cursor = tree.walk()
        has_more = True
        
        while has_more:
            node = cursor.node
            if node.type in func_types:
                # Find function name child
                name = "anonymous"
                for child in node.children:
                    if child.type in ("identifier", "field_identifier"):
                        name = code[child.start_byte:child.end_byte]
                        break
                
                start_row = node.start_point[0] + 1
                end_row = node.end_point[0] + 1
                func_code = code[node.start_byte:node.end_byte]
                
                functions.append({
                    "name": name,
                    "start_line": start_row,
                    "end_line": end_row,
                    "code": func_code,
                    "structure": extract_ast_structure(func_code, language)
                })
            
            # Traversal
            if cursor.goto_first_child():
                continue
            if cursor.goto_next_sibling():
                continue
            
            # Backtrack
            backtracking = True
            while backtracking:
                if not cursor.goto_parent():
                    has_more = False
                    backtracking = False
                elif cursor.goto_next_sibling():
                    backtracking = False
    except Exception:
        pass
        
    return functions

def jaccard_similarity(s1: set, s2: set) -> float:
    if not s1 and not s2: return 1.0
    return len(s1 & s2) / len(s1 | s2) if (s1 | s2) else 0.0

def structural_similarity(code1: str, code2: str, language: str = "python") -> float:
    def ngrams(tokens, n):
        return set(tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1))
    
    # Extract AST structure tokens using tree-sitter
    s1 = extract_ast_structure(code1, language).split()
    s2 = extract_ast_structure(code2, language).split()
    
    if not s1 or not s2: return 0.0
    bi  = jaccard_similarity(ngrams(s1,2), ngrams(s2,2))
    tri = jaccard_similarity(ngrams(s1,3), ngrams(s2,3))
    
    # 0.4 weight for bigrams, 0.6 weight for trigrams represents structural similarity balance
    return round(bi*0.4 + tri*0.6, 4)