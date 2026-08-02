import os
import re
from datetime import date
from typing import Dict, List, Any, Optional
import psycopg
from psycopg.rows import dict_row

from core.config import DATABASE_URL
from services.auto_linker import AutoWikiLinker

class VaultRefactorEngine:
    def __init__(self, db_url: str = DATABASE_URL):
        self.db_url = db_url
        self.linker = AutoWikiLinker(db_url=db_url)

    def detect_gaps(self) -> Dict[str, Any]:
        """
        Analyzes Knowledge Graph in PostgreSQL to detect:
        1. Orphan Nodes: Nodes with zero incoming or outgoing relationships.
        2. Unlinked Mentions / Missing Links.
        3. Nodes missing mandatory YAML frontmatter properties.
        """
        with psycopg.connect(self.db_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # 1. Detect Orphan Nodes
                cur.execute(
                    """
                    SELECT n.id, n.title, n.file_path, n.type
                    FROM nodes n
                    LEFT JOIN node_relationships r1 ON n.id = r1.source_node_id
                    LEFT JOIN node_relationships r2 ON n.id = r2.target_node_id
                    WHERE r1.id IS NULL AND r2.id IS NULL
                    ORDER BY n.title;
                    """
                )
                orphan_nodes = cur.fetchall()

                # 2. Total nodes & relationships summary
                cur.execute("SELECT COUNT(*) AS total_nodes FROM nodes;")
                total_nodes = cur.fetchone()["total_nodes"]

                cur.execute("SELECT COUNT(*) AS total_relationships FROM node_relationships;")
                total_rels = cur.fetchone()["total_relationships"]

                # 3. Nodes with missing frontmatter or aliases
                cur.execute(
                    """
                    SELECT id, title, file_path, type, aliases, tags
                    FROM nodes
                    WHERE type IS NULL OR type = '' OR aliases IS NULL OR cardinality(aliases) = 0;
                    """
                )
                missing_metadata_nodes = cur.fetchall()

                return {
                    "summary": {
                        "total_nodes": total_nodes,
                        "total_relationships": total_rels,
                        "orphan_count": len(orphan_nodes),
                        "missing_metadata_count": len(missing_metadata_nodes)
                    },
                    "orphan_nodes": orphan_nodes,
                    "missing_metadata_nodes": missing_metadata_nodes
                }

    def refactor_file(self, full_file_path: str, save: bool = False) -> Dict[str, Any]:
        """
        Reads a markdown note file, auto-inserts Wiki Links, and ensures proper frontmatter structure.
        """
        if not os.path.exists(full_file_path):
            return {"error": f"File '{full_file_path}' does not exist"}

        with open(full_file_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        filename = os.path.basename(full_file_path).replace(".md", "")
        
        # 1. Apply AutoWikiLinker
        refactored_content = self.linker.linkify_text(original_content, current_title=filename)

        # 2. Ensure Frontmatter exists
        if not refactored_content.startswith("---"):
            today_str = date.today().isoformat()
            default_fm = f"---\ntype: concept\ncreated: {today_str}\naliases: []\ntags: [knowledge]\n---\n\n"
            refactored_content = default_fm + refactored_content

        has_changes = (original_content != refactored_content)

        if save and has_changes:
            with open(full_file_path, "w", encoding="utf-8") as f:
                f.write(refactored_content)

        return {
            "file_path": full_file_path,
            "title": filename,
            "has_changes": has_changes,
            "saved": save and has_changes,
            "original_length": len(original_content),
            "refactored_length": len(refactored_content),
            "refactored_content": refactored_content
        }

if __name__ == "__main__":
    engine = VaultRefactorEngine()
    print("--- GAP DETECTION REPORT ---")
    report = engine.detect_gaps()
    print("Summary:", report["summary"])
