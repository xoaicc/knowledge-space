import urllib.parse
from typing import Dict, List, Any, Optional
import psycopg
from psycopg.rows import dict_row

from core.config import DATABASE_URL
from services.graph_engine import KnowledgeGraphEngine

class DecisionSupportEngine:
    def __init__(self, db_url: str = DATABASE_URL):
        self.db_url = db_url
        self.graph_engine = KnowledgeGraphEngine(db_url=db_url)

    def evaluate_decision(self, problem_statement: str, search_fn=None) -> Dict[str, Any]:
        """
        Evaluates a decision or architectural problem statement by querying 
        grounded concepts from the Vault and analyzing graph context.
        """
        grounded_items = []
        graph_neighbors = []

        if search_fn:
            rag_res = search_fn(problem_statement, top_k=3)
            grounded_items = rag_res.get("primary_results", [])
            graph_neighbors = rag_res.get("graph_context", [])

        citations = []
        concepts_used = []

        for item in grounded_items:
            title = item.get("title", "")
            file_path = item.get("file_path", "")
            concepts_used.append(title)
            if file_path:
                encoded = urllib.parse.quote(file_path.replace(".md", ""))
                uri = f"obsidian://open?file={encoded}"
                citations.append({
                    "title": title,
                    "file_path": file_path,
                    "obsidian_uri": uri,
                    "markdown_citation": f"[{file_path}]({uri})"
                })

        report_md = f"# Báo cáo Hỗ trợ Quyết định (Decision Support Report)\n\n"
        report_md += f"**Bài toán / Đặt vấn đề:** {problem_statement}\n\n"
        report_md += f"---\n\n"
        report_md += f"## 1. Tri thức Căn bản từ Vault (Grounded Knowledge)\n"
        
        if grounded_items:
            for item in grounded_items:
                report_md += f"- **[[{item['title']}]]** (Score: `{item.get('rerank_score', 0):.2f}`)\n"
                report_md += f"  > {item.get('content', '')}\n\n"
        else:
            report_md += "Chưa có tri thức trực tiếp liên quan đến bài toán này trong Vault.\n\n"

        report_md += f"## 2. Bối cảnh Đồ thị & Mối quan hệ Lân cận\n"
        if graph_neighbors:
            for g in graph_neighbors:
                report_md += f"- Khái niệm **{g['connected_from']}** --[{g['relation_type']}]--> **[[{g['neighbor_title']}]]**\n"
        else:
            report_md += "Không tìm thấy mở rộng đồ thị lân cận.\n"

        report_md += f"\n## 3. Khuyến nghị & Phân tích Đánh giá (Grounded Decision)\n"
        report_md += f"- Dựa trên dữ liệu Vault, bài toán `{problem_statement}` liên quan trực tiếp đến các khái niệm: "
        report_md += ", ".join([f"**[[{c}]]**" for c in concepts_used]) if concepts_used else "Chưa xác định"
        report_md += f".\n- **Khuyến nghị**: Nên tuân thủ quy chuẩn thiết kế đã được định nghĩa trong các note liên quan để đảm bảo tính nhất quán của hệ thống.\n\n"

        report_md += f"## 4. Trích dẫn Nguồn Obsidian\n"
        for c in citations:
            report_md += f"- {c['markdown_citation']}\n"

        return {
            "problem_statement": problem_statement,
            "concepts_used": concepts_used,
            "grounded_items_count": len(grounded_items),
            "citations": citations,
            "decision_report": report_md
        }

if __name__ == "__main__":
    engine = DecisionSupportEngine()
    print("--- TESTING DECISION SUPPORT ENGINE ---")
    res = engine.evaluate_decision("Lựa chọn cơ chế quản lý bộ nhớ tự động")
    print(res["decision_report"])
