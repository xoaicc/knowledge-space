from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import urllib.parse
import psycopg
from psycopg.rows import dict_row
from FlagEmbedding import BGEM3FlagModel
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

from core.config import DATABASE_URL, EMBEDDING_MODEL_NAME, RERANKER_MODEL_NAME, CACHE_DIR
from core.indexer import KnowledgeIndexer
from services.graph_engine import KnowledgeGraphEngine
from services.auto_linker import AutoWikiLinker
from services.refactor_engine import VaultRefactorEngine
from services.synthesis_engine import KnowledgeSynthesisEngine
from services.reasoning_engine import DecisionSupportEngine
from services.user_profiler import UserProfileManager
from services.roadmap_engine import PersonalRoadmapEngine

class SafeLocalReranker:
    def __init__(self, model_name: str, cache_dir: str):
        print(f"Loading Safe Reranker Model '{model_name}'...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name, cache_dir=cache_dir)
        self.model.eval()

    def compute_score(self, pairs: List[List[str]]) -> List[float]:
        if not pairs:
            return []
        inputs = self.tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=256)
        with torch.no_grad():
            scores = self.model(**inputs, return_dict=True).logits.view(-1).float().tolist()
        return scores if isinstance(scores, list) else [scores]

app = FastAPI(
    title="Knowledge Service API",
    description="PostgreSQL + pgvector + Reranker + GraphRAG + Agent Tools + Phase 6A Adaptive Knowledge Strategist Engine",
    version="6.0.0"
)

# Global model & engine instances
print(f"Initializing Query Embedding Model '{EMBEDDING_MODEL_NAME}' into {CACHE_DIR}...")
embedding_model = BGEM3FlagModel(EMBEDDING_MODEL_NAME, cache_dir=CACHE_DIR, use_fp16=False)

print(f"Initializing Safe Reranker Model '{RERANKER_MODEL_NAME}' into {CACHE_DIR}...")
reranker_model = SafeLocalReranker(RERANKER_MODEL_NAME, cache_dir=CACHE_DIR)

graph_engine = KnowledgeGraphEngine(DATABASE_URL)
auto_linker = AutoWikiLinker(DATABASE_URL)
refactor_engine = VaultRefactorEngine(DATABASE_URL)
synthesis_engine = KnowledgeSynthesisEngine(DATABASE_URL)
decision_engine = DecisionSupportEngine(DATABASE_URL)
profile_mgr = UserProfileManager()
roadmap_engine = PersonalRoadmapEngine(DATABASE_URL)
print("Models & Engines ready.")

def get_db_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def build_citation(file_path: str, heading: Optional[str] = None) -> Dict[str, str]:
    encoded_path = urllib.parse.quote(file_path.replace(".md", ""))
    obsidian_uri = f"obsidian://open?file={encoded_path}"
    return {
        "file_path": file_path,
        "section_heading": heading or "",
        "obsidian_uri": obsidian_uri,
        "markdown_citation": f"[{file_path}]({obsidian_uri})"
    }

# Pydantic Schemas
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    min_score: Optional[float] = 0.0

class GraphRAGRequest(BaseModel):
    query: str
    top_k: int = 3
    graph_depth: int = 1
    min_score: Optional[float] = 0.0

class TraverseRequest(BaseModel):
    root_title: str
    max_depth: int = 2

class ShortestPathRequest(BaseModel):
    source_title: str
    target_title: str
    max_depth: int = 5

class IndexRequest(BaseModel):
    force: bool = False

class SuggestLinksRequest(BaseModel):
    text: str
    current_title: Optional[str] = ""

class RefactorNoteRequest(BaseModel):
    file_path: str
    save: bool = False

class AgentChatRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = None

class SynthesisRequest(BaseModel):
    topic_a: str
    topic_b: str

class BuildMapRequest(BaseModel):
    domain_or_tag: str

class DecisionSupportRequest(BaseModel):
    problem_statement: str

class AdaptExplanationRequest(BaseModel):
    content: str
    query: Optional[str] = ""
    override_level: Optional[str] = None

class GenerateRoadmapRequest(BaseModel):
    save: bool = True

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "phase": "6A - Pedagogical & Adaptive Personal Knowledge Strategist",
        "embedding_model": EMBEDDING_MODEL_NAME,
        "reranker_model": RERANKER_MODEL_NAME,
        "threshold_filter_enabled": True
    }

@app.post("/api/index")
def trigger_index(req: IndexRequest):
    indexer = KnowledgeIndexer()
    stats = indexer.run_indexing(force=req.force)
    auto_linker.refresh_concepts()
    return {"message": "Indexing completed", "stats": stats}

@app.post("/api/search/semantic")
def semantic_search(req: SearchRequest):
    raw_emb = embedding_model.encode([req.query], max_length=8192)["dense_vecs"][0]
    query_emb = [float(x) for x in raw_emb]
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    c.id AS chunk_id,
                    n.id AS node_id,
                    n.title,
                    n.file_path,
                    n.type,
                    c.section_heading,
                    c.content,
                    1 - (c.embedding <=> %s::vector) AS cosine_similarity
                FROM node_chunks c
                JOIN nodes n ON c.node_id = n.id
                ORDER BY c.embedding <=> %s::vector ASC
                LIMIT %s;
                """,
                (str(query_emb), str(query_emb), req.top_k)
            )
            rows = cur.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["citation"] = build_citation(item["file_path"], item["section_heading"])
                results.append(item)
            return {"query": req.query, "results": results}

@app.post("/api/search/fts")
def full_text_search(req: SearchRequest):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    c.id AS chunk_id,
                    n.id AS node_id,
                    n.title,
                    n.file_path,
                    n.type,
                    c.section_heading,
                    c.content,
                    ts_rank_cd(c.fts_tokens, plainto_tsquery('simple', %s)) AS rank
                FROM node_chunks c
                JOIN nodes n ON c.node_id = n.id
                WHERE c.fts_tokens @@ plainto_tsquery('simple', %s)
                ORDER BY rank DESC
                LIMIT %s;
                """,
                (req.query, req.query, req.top_k)
            )
            rows = cur.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["citation"] = build_citation(item["file_path"], item["section_heading"])
                results.append(item)
            return {"query": req.query, "results": results}

@app.post("/api/search/hybrid")
def hybrid_search(req: SearchRequest):
    raw_emb = embedding_model.encode([req.query], max_length=8192)["dense_vecs"][0]
    query_emb = [float(x) for x in raw_emb]
    k_rrf = 60

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH vector_search AS (
                    SELECT c.id AS chunk_id, ROW_NUMBER() OVER (ORDER BY c.embedding <=> %s::vector ASC) AS rank
                    FROM node_chunks c
                    LIMIT 15
                ),
                fts_search AS (
                    SELECT c.id AS chunk_id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(c.fts_tokens, plainto_tsquery('simple', %s)) DESC) AS rank
                    FROM node_chunks c
                    WHERE c.fts_tokens @@ plainto_tsquery('simple', %s)
                    LIMIT 15
                )
                SELECT 
                    c.id AS chunk_id,
                    n.id AS node_id,
                    n.title,
                    n.file_path,
                    n.type,
                    c.section_heading,
                    c.content,
                    COALESCE(1.0 / (%s + v.rank), 0.0) + COALESCE(1.0 / (%s + f.rank), 0.0) AS rrf_score
                FROM node_chunks c
                JOIN nodes n ON c.node_id = n.id
                LEFT JOIN vector_search v ON c.id = v.chunk_id
                LEFT JOIN fts_search f ON c.id = f.chunk_id
                WHERE v.chunk_id IS NOT NULL OR f.chunk_id IS NOT NULL
                ORDER BY rrf_score DESC
                LIMIT %s;
                """,
                (str(query_emb), req.query, req.query, k_rrf, k_rrf, req.top_k)
            )
            rows = cur.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["citation"] = build_citation(item["file_path"], item["section_heading"])
                results.append(item)
            return {"query": req.query, "results": results}

@app.post("/api/search/rerank")
def rerank_search(req: SearchRequest):
    raw_emb = embedding_model.encode([req.query], max_length=8192)["dense_vecs"][0]
    query_emb = [float(x) for x in raw_emb]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH vector_search AS (
                    SELECT c.id AS chunk_id, ROW_NUMBER() OVER (ORDER BY c.embedding <=> %s::vector ASC) AS rank
                    FROM node_chunks c
                    LIMIT 8
                ),
                fts_search AS (
                    SELECT c.id AS chunk_id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(c.fts_tokens, plainto_tsquery('simple', %s)) DESC) AS rank
                    FROM node_chunks c
                    WHERE c.fts_tokens @@ plainto_tsquery('simple', %s)
                    LIMIT 8
                )
                SELECT 
                    c.id AS chunk_id,
                    n.id AS node_id,
                    n.title,
                    n.file_path,
                    n.type,
                    c.section_heading,
                    c.content
                FROM node_chunks c
                JOIN nodes n ON c.node_id = n.id
                LEFT JOIN vector_search v ON c.id = v.chunk_id
                LEFT JOIN fts_search f ON c.id = f.chunk_id
                WHERE v.chunk_id IS NOT NULL OR f.chunk_id IS NOT NULL;
                """,
                (str(query_emb), req.query, req.query)
            )
            candidates = cur.fetchall()

    if not candidates:
        return {"query": req.query, "results": []}

    pairs = [[req.query, c["content"]] for c in candidates]
    scores = reranker_model.compute_score(pairs)

    results = []
    for c, score in zip(candidates, scores):
        item = dict(c)
        item["rerank_score"] = float(score)
        item["citation"] = build_citation(item["file_path"], item["section_heading"])
        results.append(item)

    results.sort(key=lambda x: x["rerank_score"], reverse=True)

    if req.min_score is not None:
        filtered_results = [r for r in results if r["rerank_score"] >= req.min_score]
        if not filtered_results and results:
            filtered_results = [results[0]]
        results = filtered_results

    return {"query": req.query, "results": results[:req.top_k]}

@app.post("/api/search/graph-rag")
def graph_rag_search(req: GraphRAGRequest):
    rerank_res = rerank_search(SearchRequest(query=req.query, top_k=req.top_k, min_score=req.min_score))
    top_items = rerank_res.get("results", [])
    
    if not top_items:
        return {"query": req.query, "primary_results": [], "graph_context": []}

    seed_node_ids = [item["node_id"] for item in top_items if "node_id" in item]
    
    graph_context = graph_engine.expand_graph_context(seed_node_ids, depth=req.graph_depth)
    
    formatted_graph_context = []
    for g in graph_context:
        citation = build_citation(g["file_path"])
        formatted_graph_context.append({
            "connected_from": g["connected_from"],
            "relation_type": g["relation_type"],
            "neighbor_title": g["title"],
            "neighbor_type": g["type"],
            "citation": citation
        })

    return {
        "query": req.query,
        "primary_results": top_items,
        "graph_context": formatted_graph_context
    }

@app.post("/api/graph/traverse")
def graph_traverse(req: TraverseRequest):
    result = graph_engine.traverse_graph(root_title=req.root_title, max_depth=req.max_depth)
    if not result.get("root"):
        raise HTTPException(status_code=404, detail=f"Concept node '{req.root_title}' not found in vault")
    return result

@app.post("/api/graph/shortest-path")
def shortest_path(req: ShortestPathRequest):
    result = graph_engine.find_shortest_path(source_title=req.source_title, target_title=req.target_title, max_depth=req.max_depth)
    return result

@app.get("/api/graph")
def get_graph():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, type, file_path FROM nodes;")
            nodes = cur.fetchall()

            cur.execute(
                """
                SELECT r.id, r.source_node_id, r.target_title, r.target_node_id, r.relation_type
                FROM node_relationships r;
                """
            )
            relationships = cur.fetchall()

            return {"nodes": nodes, "relationships": relationships}

# ==================== PHASE 4A: AGENTIC & REFACTORING ENDPOINTS ====================

@app.post("/api/agent/suggest-links")
def suggest_wiki_links(req: SuggestLinksRequest):
    linkified_text = auto_linker.linkify_text(req.text, current_title=req.current_title or "")
    return {
        "original_text": req.text,
        "linkified_text": linkified_text,
        "has_new_links": (req.text != linkified_text)
    }

@app.post("/api/agent/gap-detection")
def gap_detection():
    return refactor_engine.detect_gaps()

@app.post("/api/agent/refactor")
def refactor_note(req: RefactorNoteRequest):
    return refactor_engine.refactor_file(req.file_path, save=req.save)

@app.post("/api/agent/chat")
def agent_chat(req: AgentChatRequest):
    rag_result = graph_rag_search(GraphRAGRequest(query=req.query, top_k=3))
    primary = rag_result.get("primary_results", [])

    context_str = "\n".join([f"- {p['title']}: {p['content']}" for p in primary])
    citations = [p["citation"]["markdown_citation"] for p in primary if "citation" in p]

    answer = f"### Grounded Response for: '{req.query}'\n\n"
    if context_str:
        answer += f"**Trích xuất Tri thức:**\n{context_str}\n\n"
        answer += f"**Nguồn tham chiếu Obsidian:**\n" + "\n".join(citations)
    else:
        answer += "Không tìm thấy tri thức phù hợp trong Vault."

    return {
        "query": req.query,
        "response": answer,
        "rag_data": rag_result
    }

# ==================== PHASE 5A: THOUGHT & REASONING ENGINE ENDPOINTS ====================

@app.post("/api/reasoning/synthesis")
def cross_domain_synthesis(req: SynthesisRequest):
    return synthesis_engine.synthesize_cross_domain(req.topic_a, req.topic_b)

@app.post("/api/reasoning/build-map")
def build_map_of_content(req: BuildMapRequest):
    return synthesis_engine.generate_map_of_content(req.domain_or_tag)

@app.post("/api/reasoning/decision-support")
def decision_support(req: DecisionSupportRequest):
    def internal_rag_search(q: str, top_k: int = 3):
        return graph_rag_search(GraphRAGRequest(query=q, top_k=top_k))

    return decision_engine.evaluate_decision(req.problem_statement, search_fn=internal_rag_search)

# ==================== PHASE 6A: PEDAGOGICAL & ADAPTIVE STRATEGIST ENDPOINTS ====================

@app.get("/api/profile")
def get_user_profile():
    """Fetches current User Knowledge Profile."""
    return profile_mgr.load_profile()

@app.post("/api/profile/adapt-explanation")
def adapt_explanation(req: AdaptExplanationRequest):
    """Adapts an explanation text based on query intent or specified Cognitive Level (L1 - L4)."""
    prof = profile_mgr.load_profile()
    curr_level = prof.get("cognitive_level", "L3_TECHNICAL")

    target_level = req.override_level
    if not target_level:
        target_level = profile_mgr.estimate_cognitive_level(req.query or req.content, current_level=curr_level)

    adapted = profile_mgr.adapt_explanation(req.content, level=target_level)
    return {
        "original_content": req.content,
        "target_level": target_level,
        "adapted_content": adapted
    }

@app.post("/api/profile/generate-roadmap")
def generate_personal_roadmap(req: GenerateRoadmapRequest):
    """Generates personalized learning roadmap MOC based on User Profile and Knowledge Graph."""
    return roadmap_engine.generate_personal_roadmap(save=req.save)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
