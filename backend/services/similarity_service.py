import urllib.request
import urllib.parse
import ssl
import re
import logging
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, util
from backend.services.text_preprocessing import chunk_with_metadata

logger = logging.getLogger("similarity_service")

# Initialize SentenceTransformer model
try:
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
except Exception as e:
    logger.error("Failed to load SentenceTransformer: %s", e)
    model = None

def search_internet(query: str, n_results: int = 5) -> list:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    # Clean query and limit length
    clean_query = re.sub(r'[^\w\s]', ' ', query)[:200].strip()
    if not clean_query:
        return []
        
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(clean_query)}"
    req = urllib.request.Request(url, headers=headers)
    
    # Disable SSL verification for development to avoid issues with standard proxy/certificates on Windows
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=2) as response:
            html = response.read()
            soup = BeautifulSoup(html, "html.parser")
            
            links = soup.find_all("a", class_="result__url")
            snippets = soup.find_all("a", class_="result__snippet")
            
            results = []
            for link, snippet in zip(links, snippets):
                href = link.get("href", "")
                
                # Skip ads or DDG internal JS redirects
                if "duckduckgo.com/y.js" in href or "ad_provider" in href or "/y.js" in href:
                    continue
                
                # Unpack redirect parameters
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
                    results.append({
                        "url": final_url,
                        "title": link.get_text().strip(),
                        "snippet": snippet.get_text().strip()
                    })
                    if len(results) >= n_results:
                        break
            return results
    except Exception as e:
        logger.error("General web search failed for query '%s': %s", clean_query, e)
        return []

def fetch_url_content(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=2) as response:
            # Check content-type to avoid downloading binary formats
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type.lower() and "text/plain" not in content_type.lower():
                return ""
                
            html = response.read()
            soup = BeautifulSoup(html, "html.parser")
            
            # Decompose tags that aren't body content
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
                
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = " ".join(chunk for chunk in chunks if chunk)
            return clean_text
    except Exception as e:
        logger.warning("Failed to fetch web content from %s: %s", url, e)
        return ""

def check_text_similarity(text: str, n_results: int = 3) -> dict:
    chunks = chunk_with_metadata(text, chunk_size=500, overlap=100)
    if not chunks:
        return {"chunks": [], "source_scores": {}, "all_similarities": []}

    if model is None:
        logger.error("Similarity calculation failed: Embedding model not initialized.")
        return {"chunks": [], "source_scores": {}, "all_similarities": []}

    # Use the first 250 characters of student's text to query the internet
    search_query = text[:250].strip()
    web_results = search_internet(search_query, n_results=5)
    
    # Try keywords if the initial snippet search yielded nothing
    if not web_results:
        words = [w for w in re.split(r'\W+', text) if len(w) > 4]
        if words:
            kw_query = " ".join(words[:6])
            web_results = search_internet(kw_query, n_results=5)

    # Fetch contents of top web results
    web_sources = []
    for res in web_results:
        content = fetch_url_content(res["url"])
        if content and len(content.strip()) > 100:
            web_sources.append({
                "title": res["title"],
                "url": res["url"],
                "content": content
            })
            if len(web_sources) >= n_results:
                break

    if not web_sources:
        return {"chunks": [], "source_scores": {}, "all_similarities": []}

    # Chunk fetched web page texts with same settings
    source_chunks = []
    for src in web_sources:
        src_chunks = chunk_with_metadata(src["content"], chunk_size=500, overlap=100)
        for sc in src_chunks:
            source_chunks.append({
                "text": sc["text"],
                "source": src["title"],
                "url": src["url"]
            })

    if not source_chunks:
        return {"chunks": [], "source_scores": {}, "all_similarities": []}

    try:
        student_texts = [c["text"] for c in chunks]
        source_texts = [sc["text"] for sc in source_chunks]
        
        student_embeddings = model.encode(student_texts, convert_to_tensor=True)
        source_embeddings = model.encode(source_texts, convert_to_tensor=True)
        
        # Calculate cosine similarity matrix (student_count x source_count)
        cosine_scores = util.cos_sim(student_embeddings, source_embeddings)
    except Exception as e:
        logger.error("Failed encoding or similarity computation: %s", e)
        return {"chunks": [], "source_scores": {}, "all_similarities": []}

    all_similarities = []
    source_scores = {}
    chunk_results = []

    for i, chunk_info in enumerate(chunks):
        chunk_text = chunk_info["text"]
        scores = cosine_scores[i]
        
        best_score_idx = int(scores.argmax())
        best_similarity = float(scores[best_score_idx])
        best_similarity = max(0.0, min(1.0, best_similarity))
        all_similarities.append(best_similarity)
        
        matched_chunk = source_chunks[best_score_idx]
        best_source = matched_chunk["source"]
        best_url = matched_chunk["url"]
        best_matched_text = matched_chunk["text"]

        if best_source not in source_scores:
            source_scores[best_source] = {
                "source_document": best_source,
                "url": best_url,
                "max_similarity": best_similarity,
                "matched_chunks": 1,
                "sample_text": best_matched_text[:200]
            }
        else:
            if best_similarity > source_scores[best_source]["max_similarity"]:
                source_scores[best_source]["max_similarity"] = best_similarity
                source_scores[best_source]["sample_text"] = best_matched_text[:200]
            source_scores[best_source]["matched_chunks"] += 1

        chunk_results.append({
            "start": chunk_info["start"],
            "end": chunk_info["end"],
            "text": chunk_text[:200],
            "best_similarity": round(best_similarity, 4),
            "best_source": best_source,
            "url": best_url,
            "matched_text": best_matched_text[:300]
        })

    return {
        "chunks": chunk_results,
        "source_scores": source_scores,
        "all_similarities": all_similarities
    }