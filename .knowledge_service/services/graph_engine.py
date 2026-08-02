from typing import List, Dict, Any, Optional
import psycopg
from psycopg.rows import dict_row

class KnowledgeGraphEngine:
    def __init__(self, db_url: str):
        self.db_url = db_url

    def get_db_connection(self):
        return psycopg.connect(self.db_url, row_factory=dict_row)

    def traverse_graph(self, root_title: str, max_depth: int = 2) -> Dict[str, Any]:
        """
        Traverses Knowledge Graph starting from root_title up to max_depth hops.
        Uses PostgreSQL Recursive CTE.
        """
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                # Find root node
                cur.execute(
                    "SELECT id, title, type, file_path FROM nodes WHERE LOWER(title) = LOWER(%s) OR LOWER(%s) = ANY(SELECT LOWER(a) FROM unnest(aliases) a);",
                    (root_title, root_title)
                )
                root = cur.fetchone()
                if not root:
                    return {"root": None, "nodes": [], "edges": []}

                cur.execute(
                    """
                    WITH RECURSIVE graph_tree AS (
                        -- Base case: Root node relationships
                        SELECT 
                            r.id AS rel_id,
                            r.source_node_id,
                            r.target_node_id,
                            r.target_title,
                            r.relation_type,
                            1 AS depth,
                            ARRAY[r.source_node_id] AS path_visited
                        FROM node_relationships r
                        WHERE r.source_node_id = %s

                        UNION ALL

                        -- Recursive step: Next hop relationships
                        SELECT 
                            r.id AS rel_id,
                            r.source_node_id,
                            r.target_node_id,
                            r.target_title,
                            r.relation_type,
                            gt.depth + 1 AS depth,
                            gt.path_visited || r.source_node_id
                        FROM node_relationships r
                        JOIN graph_tree gt ON r.source_node_id = gt.target_node_id
                        WHERE gt.depth < %s
                          AND r.target_node_id IS NOT NULL
                          AND NOT (r.source_node_id = ANY(gt.path_visited))
                    )
                    SELECT DISTINCT 
                        gt.rel_id,
                        gt.source_node_id,
                        sn.title AS source_title,
                        gt.target_node_id,
                        COALESCE(tn.title, gt.target_title) AS target_title,
                        gt.relation_type,
                        gt.depth
                    FROM graph_tree gt
                    JOIN nodes sn ON gt.source_node_id = sn.id
                    LEFT JOIN nodes tn ON gt.target_node_id = tn.id
                    ORDER BY gt.depth, gt.relation_type;
                    """,
                    (root["id"], max_depth)
                )
                edges = cur.fetchall()

                # Collect all involved node IDs
                node_ids = {root["id"]}
                for edge in edges:
                    node_ids.add(edge["source_node_id"])
                    if edge["target_node_id"]:
                        node_ids.add(edge["target_node_id"])

                cur.execute(
                    "SELECT id, title, type, file_path FROM nodes WHERE id = ANY(%s);",
                    (list(node_ids),)
                )
                nodes = cur.fetchall()

                return {
                    "root": root,
                    "max_depth": max_depth,
                    "nodes": nodes,
                    "edges": edges
                }

    def find_shortest_path(self, source_title: str, target_title: str, max_depth: int = 5) -> Dict[str, Any]:
        """
        Finds the shortest path between two concept titles using Recursive CTE BFS.
        """
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, title FROM nodes WHERE LOWER(title) = LOWER(%s) OR LOWER(%s) = ANY(SELECT LOWER(a) FROM unnest(aliases) a);",
                    (source_title, source_title)
                )
                source_node = cur.fetchone()

                cur.execute(
                    "SELECT id, title FROM nodes WHERE LOWER(title) = LOWER(%s) OR LOWER(%s) = ANY(SELECT LOWER(a) FROM unnest(aliases) a);",
                    (target_title, target_title)
                )
                target_node = cur.fetchone()

                if not source_node or not target_node:
                    return {"source": source_title, "target": target_title, "path_found": False, "path": []}

                cur.execute(
                    """
                    WITH RECURSIVE search_path AS (
                        SELECT 
                            r.source_node_id,
                            r.target_node_id,
                            r.relation_type,
                            1 AS depth,
                            ARRAY[r.source_node_id, r.target_node_id] AS visited_nodes,
                            ARRAY[r.relation_type] AS relation_chain
                        FROM node_relationships r
                        WHERE r.source_node_id = %s AND r.target_node_id IS NOT NULL

                        UNION ALL

                        SELECT 
                            r.source_node_id,
                            r.target_node_id,
                            r.relation_type,
                            sp.depth + 1,
                            sp.visited_nodes || r.target_node_id,
                            sp.relation_chain || r.relation_type
                        FROM node_relationships r
                        JOIN search_path sp ON r.source_node_id = sp.target_node_id
                        WHERE sp.depth < %s
                          AND r.target_node_id IS NOT NULL
                          AND NOT (r.target_node_id = ANY(sp.visited_nodes))
                    )
                    SELECT visited_nodes, relation_chain, depth
                    FROM search_path
                    WHERE target_node_id = %s
                    ORDER BY depth ASC
                    LIMIT 1;
                    """,
                    (source_node["id"], max_depth, target_node["id"])
                )
                result = cur.fetchone()

                if not result:
                    return {"source": source_node["title"], "target": target_node["title"], "path_found": False, "path": []}

                visited_ids = result["visited_nodes"]
                relations = result["relation_chain"]

                cur.execute(
                    "SELECT id, title, type, file_path FROM nodes WHERE id = ANY(%s);",
                    (visited_ids,)
                )
                nodes_map = {n["id"]: n for n in cur.fetchall()}

                path_details = []
                for i in range(len(visited_ids) - 1):
                    src_id = visited_ids[i]
                    tgt_id = visited_ids[i + 1]
                    rel = relations[i]
                    path_details.append({
                        "hop": i + 1,
                        "source": nodes_map.get(src_id, {"title": "Unknown"}),
                        "relation": rel,
                        "target": nodes_map.get(tgt_id, {"title": "Unknown"})
                    })

                return {
                    "source": source_node["title"],
                    "target": target_node["title"],
                    "path_found": True,
                    "total_hops": result["depth"],
                    "path": path_details
                }

    def expand_graph_context(self, seed_node_ids: List[str], depth: int = 1) -> List[Dict[str, Any]]:
        """
        Expands context by retrieving 1-hop neighbor nodes and their key chunks.
        """
        if not seed_node_ids:
            return []

        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT n.id, n.title, n.type, n.file_path, r.relation_type, sn.title AS connected_from
                    FROM node_relationships r
                    JOIN nodes n ON r.target_node_id = n.id
                    JOIN nodes sn ON r.source_node_id = sn.id
                    WHERE r.source_node_id = ANY(%s) AND r.target_node_id IS NOT NULL AND NOT (r.target_node_id = ANY(%s))
                    LIMIT 10;
                    """,
                    (seed_node_ids, seed_node_ids)
                )
                neighbors = cur.fetchall()
                return neighbors
