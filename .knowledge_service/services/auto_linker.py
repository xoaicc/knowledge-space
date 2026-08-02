import re
import psycopg
from psycopg.rows import dict_row
from typing import List, Dict, Set
from core.config import DATABASE_URL

class AutoWikiLinker:
    def __init__(self, db_url: str = DATABASE_URL):
        self.db_url = db_url
        self._concept_map: Dict[str, str] = {} # term -> target_title
        self.refresh_concepts()

    def refresh_concepts(self):
        """Load all concept titles and aliases from PostgreSQL nodes table."""
        new_map: Dict[str, str] = {}
        with psycopg.connect(self.db_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT title, aliases FROM nodes;")
                rows = cur.fetchall()
                for r in rows:
                    title = r["title"]
                    if not title:
                        continue
                    new_map[title.lower()] = title
                    aliases = r.get("aliases") or []
                    if isinstance(aliases, list):
                        for alias in aliases:
                            if alias and isinstance(alias, str):
                                new_map[alias.lower()] = title
        # Sort terms by length descending to match longest terms first
        self._concept_map = dict(sorted(new_map.items(), key=lambda x: len(x[0]), reverse=True))

    def linkify_text(self, content: str, current_title: str = "") -> str:
        """
        Scans input content and replaces unlinked concept mentions with [[ConceptTitle]].
        Ignores existing [[Wiki Links]], code blocks, inline code, and YAML frontmatter.
        """
        if not content or not self._concept_map:
            return content

        # Separate YAML frontmatter if present
        frontmatter = ""
        body = content
        fm_match = re.match(r"^(---\s*\n.*?\n---\s*\n)(.*)", content, flags=re.DOTALL)
        if fm_match:
            frontmatter = fm_match.group(1)
            body = fm_match.group(2)

        # Protect code blocks and existing wiki links with placeholders
        placeholders: List[str] = []
        
        def add_placeholder(match_text: str) -> str:
            idx = len(placeholders)
            placeholders.append(match_text)
            return f"__PLACEHOLDER_{idx}__"

        # Protect ``` code blocks ```
        body = re.sub(r"```[\s\S]*?```", lambda m: add_placeholder(m.group(0)), body)
        # Protect ` inline code `
        body = re.sub(r"`[^`\n]+`", lambda m: add_placeholder(m.group(0)), body)
        # Protect existing [[Wiki Links]]
        body = re.sub(r"\[\[[^\]]+\]\]", lambda m: add_placeholder(m.group(0)), body)
        # Protect Markdown URLs [text](url)
        body = re.sub(r"\[[^\]]+\]\([^)]+\)", lambda m: add_placeholder(m.group(0)), body)

        current_lower = current_title.lower() if current_title else ""

        # Perform replacement for terms
        for term_lower, target_title in self._concept_map.items():
            if current_lower and term_lower == current_lower:
                continue # Do not self-link current title
            
            # Match term with word boundaries (handling Vietnamese unicode words)
            pattern = re.compile(r'(?<![a-zA-Z0-9_\-\[\]])' + re.escape(term_lower) + r'(?![a-zA-Z0-9_\-\[\]])', re.IGNORECASE)
            
            # Check if term exists before substituting
            def replace_with_alias(match):
                matched_text = match.group(0)
                if matched_text.lower() == target_title.lower():
                    return f"[[{target_title}]]"
                else:
                    return f"[[{target_title}|{matched_text}]]"

            if pattern.search(body):
                body = pattern.sub(replace_with_alias, body)

        # Restore protected placeholders
        for idx in range(len(placeholders) - 1, -1, -1):
            body = body.replace(f"__PLACEHOLDER_{idx}__", placeholders[idx])

        return frontmatter + body

if __name__ == "__main__":
    linker = AutoWikiLinker()
    sample = "Garbage Collection trong Python giúps tự động quản lý bộ nhớ thông qua JVM."
    print("Original:", sample)
    print("Linkified:", linker.linkify_text(sample))
