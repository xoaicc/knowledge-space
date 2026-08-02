import re
import hashlib
import frontmatter
from pathlib import Path
from typing import Dict, List, Any

# Regex to match Obsidian Wiki Links: [[Link]] or [[Link|Alias]]
WIKI_LINK_REGEX = re.compile(r'\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]')

def calculate_md5(file_path: Path) -> str:
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def parse_markdown_file(file_path: Path, vault_root: Path) -> Dict[str, Any]:
    post = frontmatter.load(file_path)
    relative_path = str(file_path.relative_to(vault_root.parent)).replace("\\", "/")
    
    title = file_path.stem
    node_type = post.get("type")
    
    # Infer type from directory if not present in frontmatter
    if not node_type:
        parent_name = file_path.parent.name.lower()
        if parent_name in ["concept", "collection", "domain", "map"]:
            node_type = parent_name
        else:
            node_type = "unknown"
    else:
        node_type = str(node_type).lower()

    aliases = post.get("aliases", [])
    if isinstance(aliases, str):
        aliases = [aliases]
    elif not isinstance(aliases, list):
        aliases = []

    tags = post.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    elif not isinstance(tags, list):
        tags = []

    content = post.content
    checksum = calculate_md5(file_path)

    # Extract all wiki links in document
    all_links = WIKI_LINK_REGEX.findall(content)
    
    # Extract relationships and sections
    relationships = parse_relationships(content)
    chunks = chunk_markdown(title, content, node_type)

    return {
        "file_path": relative_path,
        "title": title,
        "type": node_type,
        "aliases": aliases,
        "tags": tags,
        "content": content,
        "checksum": checksum,
        "wiki_links": list(set(all_links)),
        "relationships": relationships,
        "chunks": chunks
    }

def parse_relationships(content: str) -> List[Dict[str, str]]:
    relationships = []
    lines = content.splitlines()
    current_section = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            section_heading = stripped.lstrip("#").strip().lower()
            if "relationship" in section_heading or "quan hệ" in section_heading:
                current_section = "relationships"
            elif "reference" in section_heading or "tham chiếu" in section_heading:
                current_section = "references"
            else:
                current_section = None
            continue

        if current_section:
            links = WIKI_LINK_REGEX.findall(stripped)
            for link in links:
                # Infer relationship type from line text or default to relates_to / references
                rel_type = "relates_to" if current_section == "relationships" else "references"
                lower_line = stripped.lower()
                if "depends_on" in lower_line or "phụ thuộc" in lower_line:
                    rel_type = "depends_on"
                elif "implemented_by" in lower_line or "triển khai bởi" in lower_line:
                    rel_type = "implemented_by"
                elif "example_of" in lower_line or "ví dụ của" in lower_line:
                    rel_type = "example_of"
                elif "part_of" in lower_line or "một phần của" in lower_line:
                    rel_type = "part_of"
                elif "contains" in lower_line or "chứa" in lower_line:
                    rel_type = "contains"

                relationships.append({
                    "target_title": link.strip(),
                    "relation_type": rel_type
                })

    return relationships

def chunk_markdown(doc_title: str, content: str, node_type: str = "") -> List[Dict[str, Any]]:
    chunks = []
    lines = content.splitlines()
    chunk_index = 0

    # Special Term-Level Micro-Chunking for Glossary / Lexical Dictionary files
    if node_type == "glossary" or doc_title.lower() == "glossary":
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("- **") and "**:" in stripped:
                term_part = stripped.split("**:", 1)[0].replace("- **", "").strip()
                def_part = stripped.split("**:", 1)[1].strip()
                chunks.append({
                    "chunk_index": chunk_index,
                    "section_heading": f"Term: {term_part}",
                    "content": f"Glossary Term [{term_part}]: {def_part}"
                })
                chunk_index += 1
        if chunks:
            return chunks

    current_heading = doc_title
    current_chunk_lines = []

    for line in lines:
        if line.startswith("#"):
            if current_chunk_lines:
                chunk_text = "\n".join(current_chunk_lines).strip()
                if chunk_text:
                    chunks.append({
                        "chunk_index": chunk_index,
                        "section_heading": current_heading,
                        "content": f"{doc_title} > {current_heading}\n{chunk_text}" if current_heading != doc_title else f"{doc_title}\n{chunk_text}"
                    })
                    chunk_index += 1
                current_chunk_lines = []
            current_heading = line.lstrip("#").strip()
        else:
            current_chunk_lines.append(line)

    if current_chunk_lines:
        chunk_text = "\n".join(current_chunk_lines).strip()
        if chunk_text:
            chunks.append({
                "chunk_index": chunk_index,
                "section_heading": current_heading,
                "content": f"{doc_title} > {current_heading}\n{chunk_text}" if current_heading != doc_title else f"{doc_title}\n{chunk_text}"
            })

    return chunks
