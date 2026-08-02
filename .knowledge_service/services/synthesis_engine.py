import urllib.parse
from typing import Dict, List, Any, Optional
import psycopg
from psycopg.rows import dict_row

from core.config import DATABASE_URL
from services.graph_engine import KnowledgeGraphEngine

class KnowledgeSynthesisEngine:
    def __init__(self, db_url: str = DATABASE_URL):
        self.db_url = db_url
        self.graph_engine = KnowledgeGraphEngine(db_url=db_url)

    def synthesize_cross_domain(self, topic_a: str, topic_b: str) -> Dict[str, Any]:
        """
        Synthesizes insights between two cross-domain concepts by analyzing their 
        shortest path in the Knowledge Graph and shared neighboring concepts.
        """
        # 1. Find Graph Path between Concept A and Concept B
        path_res = self.graph_engine.find_shortest_path(source_title=topic_a, target_title=topic_b, max_depth=5)
        
        # 2. Get neighbor context for Topic A and Topic B
        with psycopg.connect(self.db_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT n.id, n.title, n.type, n.file_path
                    FROM nodes n
                    WHERE LOWER(n.title) IN (LOWER(%s), LOWER(%s));
                    """,
                    (topic_a, topic_b)
                )
                seed_nodes = cur.fetchall()
                seed_ids = [n["id"] for n in seed_nodes]
                
                shared_neighbors = []
                if seed_ids:
                    shared_neighbors = self.graph_engine.expand_graph_context(seed_ids, depth=1)

        hops = path_res.get("path", [])
        is_connected = path_res.get("path_found", False)

        # Collect unique nodes along the path
        path_nodes = []
        seen_titles = set()
        for h in hops:
            src = h.get("source", {})
            tgt = h.get("target", {})
            if src.get("title") and src["title"] not in seen_titles:
                seen_titles.add(src["title"])
                path_nodes.append(src)
            if tgt.get("title") and tgt["title"] not in seen_titles:
                seen_titles.add(tgt["title"])
                path_nodes.append(tgt)

        # 3. Format Obsidian Citations
        citations = []
        for p in path_nodes:
            file_path = p.get("file_path") or f"Knowledge/Concept/{p['title']}.md"
            encoded = urllib.parse.quote(file_path.replace(".md", ""))
            uri = f"obsidian://open?file={encoded}"
            citations.append({
                "title": p.get("title", ""),
                "file_path": file_path,
                "obsidian_uri": uri,
                "markdown_citation": f"[{file_path}]({uri})"
            })

        synthesis_summary = f"### Tổng hợp Tri thức Liên miền: {topic_a} ↔ {topic_b}\n\n"
        if is_connected and hops:
            synthesis_summary += f"**Mối liên kết Đồ thị ({path_res.get('total_hops', 1)} nấc):**\n"
            chain_elements = []
            for i, h in enumerate(hops):
                src_t = h['source'].get('title', 'Unknown')
                rel_t = h.get('relation', 'relates_to')
                tgt_t = h['target'].get('title', 'Unknown')
                if i == 0:
                    chain_elements.append(f"**[[{src_t}]]**")
                chain_elements.append(f"--[{rel_t}]--> **[[{tgt_t}]]**")
            synthesis_summary += " ".join(chain_elements) + "\n\n"
        else:
            synthesis_summary += f"Chưa tìm thấy đường đi trực tiếp kết nối giữa `{topic_a}` và `{topic_b}` trong Vault.\n\n"

        if shared_neighbors:
            synthesis_summary += "**Các Khái niệm Lân cận Giao nhau:**\n"
            for n in shared_neighbors[:5]:
                synthesis_summary += f"- {n['connected_from']} --[{n['relation_type']}]--> **[[{n['title']}]]**\n"

        return {
            "topic_a": topic_a,
            "topic_b": topic_b,
            "is_connected": is_connected,
            "total_hops": path_res.get("total_hops", 0),
            "hops": hops,
            "shared_neighbors": shared_neighbors,
            "citations": citations,
            "synthesis_summary": synthesis_summary
        }

    def generate_map_of_content(self, domain_or_tag: str) -> Dict[str, Any]:
        """
        Generates a structured Map of Content (MOC) markdown file content for a domain or tag.
        """
        with psycopg.connect(self.db_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Query nodes matching tag or domain
                cur.execute(
                    """
                    SELECT id, title, type, file_path, aliases, tags
                    FROM nodes
                    WHERE %s = ANY(tags) OR LOWER(type) = LOWER(%s) OR LOWER(title) LIKE %s
                    ORDER BY type, title;
                    """,
                    (domain_or_tag.lower(), domain_or_tag.lower(), f"%{domain_or_tag.lower()}%")
                )
                nodes = cur.fetchall()

        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for n in nodes:
            t = n.get("type") or "concept"
            grouped.setdefault(t, []).append(n)

        moc_content = f"---\ntype: map\ncreated: auto-generated\ntags: [moc, {domain_or_tag.lower()}]\n---\n\n"
        moc_content += f"# Map of Content: {domain_or_tag.capitalize()}\n\n"
        moc_content += f"Bản đồ khái niệm tự động tổng hợp cho chủ đề **{domain_or_tag}**.\n\n"

        for node_type, items in grouped.items():
            moc_content += f"## {node_type.capitalize()} Nodes\n"
            for item in items:
                encoded = urllib.parse.quote(item['file_path'].replace(".md", ""))
                uri = f"obsidian://open?file={encoded}"
                moc_content += f"- [[{item['title']}]] — [{item['file_path']}]({uri})\n"
            moc_content += "\n"

        return {
            "domain_or_tag": domain_or_tag,
            "total_nodes": len(nodes),
            "moc_content": moc_content
        }

if __name__ == "__main__":
    synth = KnowledgeSynthesisEngine()
    print("--- TESTING SYNTHESIS ---")
    res = synth.synthesize_cross_domain("Garbage Collection", "Python")
    print(res["synthesis_summary"])
