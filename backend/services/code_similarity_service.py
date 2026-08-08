import logging
import urllib.request
import urllib.parse
import ssl
import re
from bs4 import BeautifulSoup
from backend.services.code_preprocessing import (
    extract_ast_structure,
    structural_similarity,
    extract_functions,
    SUPPORTED_LANGUAGES
)

logger = logging.getLogger("code_similarity_service")

def search_internet_for_code(query: str, n_results: int = 3) -> list:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    clean_query = re.sub(r'[^\w\s]', ' ', query)[:200].strip()
    if not clean_query:
        return []
        
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(clean_query)}"
    req = urllib.request.Request(url, headers=headers)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=2) as response:
            html = response.read()
            soup = BeautifulSoup(html, "html.parser")
            
            links = soup.find_all("a", class_="result__url")
            results = []
            for link in links:
                href = link.get("href", "")
                if "duckduckgo.com/y.js" in href or "ad_provider" in href or "/y.js" in href:
                    continue
                if "uddg=" in href:
                    try:
                        parsed = urllib.parse.urlparse(href)
                        qs = urllib.parse.parse_qs(parsed.query)
                        final_url = qs.get("uddg", [None])[0]
                    except Exception:
                        final_url = href
                else:
                    final_url = href
                    
                if final_url:
                    results.append(final_url)
                    if len(results) >= n_results:
                        break
            return results
    except Exception as e:
        logger.error("Web search for code failed for query '%s': %s", clean_query, e)
        return []

def extract_code_snippets_from_page(url: str) -> list:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=2) as response:
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type.lower() and "text/plain" not in content_type.lower():
                return []
            html = response.read()
            soup = BeautifulSoup(html, "html.parser")
            
            snippets = []
            # Extract code from pre / code HTML tags
            for tag in soup.find_all(["pre", "code"]):
                code_text = tag.get_text()
                if len(code_text.strip().splitlines()) >= 3:
                    snippets.append(code_text.strip())
                    
            # If no tags, fallback to parsing code indentation in plain text blocks
            if not snippets:
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                text = soup.get_text()
                lines = text.splitlines()
                current_block = []
                in_code = False
                for line in lines:
                    stripped = line.strip()
                    is_code_line = (
                        stripped.startswith("def ") or
                        stripped.startswith("class ") or
                        stripped.startswith("import ") or
                        stripped.startswith("function ") or
                        stripped.startswith("const ") or
                        stripped.startswith("let ") or
                        (in_code and line.startswith("    "))
                    )
                    if is_code_line:
                        in_code = True
                        current_block.append(line)
                    else:
                        if in_code:
                            if len(current_block) >= 3:
                                snippets.append("\n".join(current_block))
                            current_block = []
                            in_code = False
                if current_block and len(current_block) >= 3:
                    snippets.append("\n".join(current_block))
            return snippets
    except Exception as e:
        logger.warning("Failed to extract code snippets from %s: %s", url, e)
        return []

def check_code_similarity(code: str, language: str = "python") -> dict:
    lang = SUPPORTED_LANGUAGES.get(language.lower())
    if not lang:
        logger.warning("Unsupported language requested: %s", language)
        return {
            "flagged_blocks": [],
            "source_scores": {},
            "all_similarities": [],
            "functions_analysed": 0
        }

    # Extract functions and formulate queries for search engines
    functions = extract_functions(code, language)
    
    queries = []
    for func in functions:
        clean_name = func["name"].replace("_", " ")
        queries.append(f"{clean_name} {language} implementation")
        
    # Also find docstrings or comments as queries
    comments = re.findall(r'#\s*(.*)', code)
    for comment in comments[:2]:
        if len(comment.strip()) > 10:
            queries.append(comment.strip() + f" {language}")
            
    if not queries:
        queries.append(f"{language} programming snippets")

    # Search web for code references
    web_urls = []
    for q in queries[:2]:
        urls = search_internet_for_code(q, n_results=3)
        web_urls.extend(urls)
    # Deduplicate
    web_urls = list(set(web_urls))

    web_code_snippets = []
    for url in web_urls:
        snippets = extract_code_snippets_from_page(url)
        for snip in snippets:
            web_code_snippets.append({
                "source": urllib.parse.urlparse(url).netloc or "Web Resource",
                "url": url,
                "code": snip
            })
            if len(web_code_snippets) >= 15:
                break
        if len(web_code_snippets) >= 15:
            break

    all_similarities = []
    source_scores = {}
    flagged_blocks = []

    # Whole-file structural AST comparison against crawled code blocks
    for snip in web_code_snippets:
        try:
            sim = structural_similarity(code, snip["code"], language)
            all_similarities.append(sim)
            source_name = snip["source"]
            url = snip["url"]
            
            if source_name not in source_scores:
                source_scores[source_name] = {
                    "source_document": source_name,
                    "url": url,
                    "max_similarity": sim,
                    "matched_chunks": 1,
                    "sample_text": snip["code"][:200]
                }
            else:
                if sim > source_scores[source_name]["max_similarity"]:
                    source_scores[source_name]["max_similarity"] = sim
                    source_scores[source_name]["sample_text"] = snip["code"][:200]
                source_scores[source_name]["matched_chunks"] += 1
        except Exception as e:
            logger.error("Failed whole-file structural comparison: %s", e)

    # Function-level AST checks
    for func in functions:
        if not func["structure"].strip():
            continue
        for snip in web_code_snippets:
            try:
                sim = structural_similarity(func["code"], snip["code"], language)
                if sim >= 0.45:  # Configured threshold
                    flagged_blocks.append({
                        "lines": f"{func['start_line']}-{func['end_line']}",
                        "function_name": func["name"],
                        "match_score": round(sim, 4),
                        "matched_source": snip["source"],
                        "url": snip["url"],
                        "reason": _code_reason(sim)
                    })
                    break
            except Exception as e:
                logger.error("Failed function-level similarity check: %s", e)
                continue

    return {
        "flagged_blocks": sorted(flagged_blocks, key=lambda x: x["match_score"], reverse=True),
        "source_scores": source_scores,
        "all_similarities": all_similarities,
        "functions_analysed": len(functions)
    }

def _code_reason(sim: float) -> str:
    if sim >= 0.90: return "Identical AST structure — likely direct copy with variable renaming."
    if sim >= 0.75: return "Very similar logical structure — probable code reuse or heavy adaptation."
    if sim >= 0.60: return "Significant structural overlap — similar algorithm or pattern detected."
    return "Moderate structural similarity — shared logic patterns found."