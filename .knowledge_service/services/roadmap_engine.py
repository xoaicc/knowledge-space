import os
import urllib.parse
from datetime import date
from typing import Dict, List, Any
import psycopg
from psycopg.rows import dict_row

from core.config import DATABASE_URL, VAULT_ROOT
from services.user_profiler import UserProfileManager

ROADMAP_FILE_PATH = str(VAULT_ROOT / "Map" / "Personal Learning Roadmap.md")

class PersonalRoadmapEngine:
    def __init__(self, db_url: str = DATABASE_URL):
        self.db_url = db_url
        self.profile_mgr = UserProfileManager()

    def generate_personal_roadmap(self, save: bool = True) -> Dict[str, Any]:
        """
        Generates a personalized learning roadmap based on User Profile goals,
        PostgreSQL Knowledge Graph relationships, and orphan concepts.
        """
        profile = self.profile_mgr.load_profile()
        cog_level = profile.get("cognitive_level", "L3_TECHNICAL")
        role = profile.get("target_role", "AI System Architect")
        focus_areas = profile.get("focus_areas", [])

        with psycopg.connect(self.db_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # 1. Fetch foundational concepts (incoming relationships > 0)
                cur.execute(
                    """
                    SELECT n.id, n.title, n.type, n.file_path, COUNT(r.id) AS connection_count
                    FROM nodes n
                    LEFT JOIN node_relationships r ON n.id = r.target_node_id
                    GROUP BY n.id, n.title, n.type, n.file_path
                    ORDER BY connection_count DESC, n.title;
                    """
                )
                ranked_nodes = cur.fetchall()

        today_str = date.today().isoformat()
        content = f"---\ntype: map\ncreated: {today_str}\ntags: [roadmap, personal-learning, {cog_level.lower()}]\n---\n\n"
        content += f"# Personal Learning Roadmap 2026\n\n"
        content += f"> **Vai trò Mục tiêu**: `{role}`  \n"
        content += f"> **Trình độ Tư duy (Cognitive Level)**: `{cog_level}`  \n"
        content += f"> **Lĩnh vực Ưu tiên**: {', '.join(focus_areas)}\n\n"
        content += f"---\n\n"

        content += f"## 1. Cây Tri thức Cốt lõi (Foundational Prerequisites)\n"
        content += f"Các khái niệm nền tảng có nhiều liên kết nhất trong Second Brain Vault:\n\n"

        for item in ranked_nodes[:5]:
            encoded = urllib.parse.quote(item['file_path'].replace(".md", ""))
            uri = f"obsidian://open?file={encoded}"
            content += f"- [[{item['title']}]] ({item['connection_count']} liên kết) — [{item['file_path']}]({uri})\n"

        content += f"\n## 2. Các Khái niệm Cần Đọc Tiếp Theo (Next Recommended Reads)\n"
        for item in ranked_nodes[5:10]:
            encoded = urllib.parse.quote(item['file_path'].replace(".md", ""))
            uri = f"obsidian://open?file={encoded}"
            content += f"- [[{item['title']}]] — [{item['file_path']}]({uri})\n"

        content += f"\n## 3. Lộ trình Nâng cấp theo Cấp độ ({cog_level})\n"
        if cog_level.startswith("L1"):
            content += "- [ ] **Giai đoạn 1**: Nắm vững khái niệm ẩn dụ & hình ảnh thực tế.\n"
            content += "- [ ] **Giai đoạn 2**: Xây dựng liên kết 2 chiều giữa các bài học cơ bản.\n"
        elif cog_level.startswith("L2"):
            content += "- [ ] **Giai đoạn 1**: Nắm vững các định nghĩa tiêu chuẩn trong Vault.\n"
            content += "- [ ] **Giai đoạn 2**: Đọc các bài Map of Content (MOC).\n"
        elif cog_level.startswith("L3"):
            content += "- [ ] **Giai đoạn 1**: Đào sâu thuật toán ma trận & bộ nhớ RAM/GPU.\n"
            content += "- [ ] **Giai đoạn 2**: Refactor các note cũ theo đúng chuẩn YAML Frontmatter.\n"
        else:
            content += "- [ ] **Giai đoạn 1**: Đánh giá trade-offs & kiến trúc hệ thống phân tán.\n"
            content += "- [ ] **Giai đoạn 2**: Tối ưu hóa hạ tầng Knowledge Service API.\n"

        if save:
            os.makedirs(os.path.dirname(ROADMAP_FILE_PATH), exist_ok=True)
            with open(ROADMAP_FILE_PATH, "w", encoding="utf-8") as f:
                f.write(content)

        return {
            "roadmap_file": ROADMAP_FILE_PATH,
            "target_role": role,
            "cognitive_level": cog_level,
            "nodes_included": len(ranked_nodes),
            "content": content
        }

if __name__ == "__main__":
    engine = PersonalRoadmapEngine()
    print("--- TESTING PERSONAL ROADMAP GENERATOR ---")
    res = engine.generate_personal_roadmap(save=True)
    print("Generated Roadmap at:", res["roadmap_file"])
    print(res["content"][:300] + "...")
