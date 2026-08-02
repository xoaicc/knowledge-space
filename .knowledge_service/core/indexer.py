import sys
from pathlib import Path
from typing import Dict, List, Any
import psycopg
from psycopg.rows import dict_row
from FlagEmbedding import BGEM3FlagModel

from core.config import DATABASE_URL, VAULT_ROOT, EMBEDDING_MODEL_NAME, CACHE_DIR
from core.parser import parse_markdown_file

class KnowledgeIndexer:
    def __init__(self):
        print(f"Loading BGEM3FlagModel '{EMBEDDING_MODEL_NAME}' into {CACHE_DIR}...")
        self.embedding_model = BGEM3FlagModel(EMBEDDING_MODEL_NAME, cache_dir=CACHE_DIR, use_fp16=False)
        print("Model loaded successfully.")

    def get_db_connection(self):
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)

    def run_indexing(self, force: bool = False) -> Dict[str, Any]:
        stats = {"indexed": 0, "skipped": 0, "errors": 0, "details": []}
        
        if not VAULT_ROOT.exists():
            print(f"Vault root directory not found: {VAULT_ROOT}")
            return stats

        md_files = [f for f in VAULT_ROOT.rglob("*.md") if not f.name.startswith("_")]

        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                # Fetch existing checksums
                cur.execute("SELECT file_path, checksum FROM nodes")
                existing_checksums = {row["file_path"]: row["checksum"] for row in cur.fetchall()}

                for file_path in md_files:
                    try:
                        parsed = parse_markdown_file(file_path, VAULT_ROOT)
                        rel_path = parsed["file_path"]

                        if not force and rel_path in existing_checksums and existing_checksums[rel_path] == parsed["checksum"]:
                            stats["skipped"] += 1
                            continue

                        print(f"Indexing: {rel_path}")
                        self._index_node(cur, parsed)
                        stats["indexed"] += 1
                        stats["details"].append({"path": rel_path, "status": "indexed"})
                    except Exception as e:
                        print(f"Error indexing {file_path}: {e}")
                        stats["errors"] += 1
                        stats["details"].append({"path": str(file_path), "error": str(e)})

                # Resolve relationship target_node_id pointers
                self._resolve_relationship_links(cur)
                conn.commit()

        print(f"Indexing completed. Indexed: {stats['indexed']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}")
        return stats

    def _index_node(self, cur, parsed: Dict[str, Any]):
        # Delete existing node record if updating
        cur.execute("DELETE FROM nodes WHERE file_path = %s", (parsed["file_path"],))

        # Insert into nodes
        cur.execute(
            """
            INSERT INTO nodes (file_path, title, type, aliases, tags, content, checksum)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (
                parsed["file_path"],
                parsed["title"],
                parsed["type"],
                parsed["aliases"],
                parsed["tags"],
                parsed["content"],
                parsed["checksum"],
            ),
        )
        node_id = cur.fetchone()["id"]

        # Insert relationships
        for rel in parsed["relationships"]:
            cur.execute(
                """
                INSERT INTO node_relationships (source_node_id, target_title, relation_type)
                VALUES (%s, %s, %s);
                """,
                (node_id, rel["target_title"], rel["relation_type"]),
            )

        # Insert aliases into node_aliases
        for alias in parsed["aliases"]:
            if alias and isinstance(alias, str):
                cur.execute(
                    """
                    INSERT INTO node_aliases (node_id, alias, alias_lower)
                    VALUES (%s, %s, %s);
                    """,
                    (node_id, alias.strip(), alias.strip().lower()),
                )

        # Generate embeddings & insert chunks
        if parsed["chunks"]:
            chunk_texts = [c["content"] for c in parsed["chunks"]]
            output = self.embedding_model.encode(chunk_texts, batch_size=12, max_length=8192)
            embeddings = output["dense_vecs"].tolist()

            for chunk, emb in zip(parsed["chunks"], embeddings):
                cur.execute(
                    """
                    INSERT INTO node_chunks (node_id, chunk_index, section_heading, content, embedding)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (node_id, chunk["chunk_index"], chunk["section_heading"], chunk["content"], str(emb)),
                )

    def _resolve_relationship_links(self, cur):
        cur.execute(
            """
            UPDATE node_relationships r
            SET target_node_id = n.id
            FROM nodes n
            WHERE LOWER(r.target_title) = LOWER(n.title) OR LOWER(r.target_title) = ANY(SELECT LOWER(a) FROM unnest(n.aliases) a);
            """
        )

if __name__ == "__main__":
    indexer = KnowledgeIndexer()
    indexer.run_indexing(force=True)
