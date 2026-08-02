CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: nodes (Vault Files Metadata)
CREATE TABLE IF NOT EXISTS nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_path TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    aliases TEXT[] DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    content TEXT,
    checksum TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Table: node_relationships (Wiki Links & Semantic Relations)
CREATE TABLE IF NOT EXISTS node_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    target_title TEXT NOT NULL,
    target_node_id UUID REFERENCES nodes(id) ON DELETE SET NULL,
    relation_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: node_chunks (Text Chunks for Vector & Full-Text Search)
CREATE TABLE IF NOT EXISTS node_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    section_heading TEXT,
    content TEXT NOT NULL,
    embedding vector(1024),
    fts_tokens tsvector GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED
);

-- Table: node_aliases (Multilingual & Acronym Alias Resolver)
CREATE TABLE IF NOT EXISTS node_aliases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    alias TEXT NOT NULL,
    alias_lower TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for Fast Lookups & Vector/FTS
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
CREATE INDEX IF NOT EXISTS idx_nodes_title_lower ON nodes(LOWER(title));
CREATE INDEX IF NOT EXISTS idx_node_relationships_source ON node_relationships(source_node_id);
CREATE INDEX IF NOT EXISTS idx_node_relationships_target ON node_relationships(target_node_id);
CREATE INDEX IF NOT EXISTS idx_node_relationships_target_title ON node_relationships(LOWER(target_title));
CREATE INDEX IF NOT EXISTS idx_node_relationships_composite ON node_relationships(source_node_id, target_node_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_node_aliases_lower ON node_aliases(alias_lower);
CREATE INDEX IF NOT EXISTS idx_node_aliases_node_id ON node_aliases(node_id);
CREATE INDEX IF NOT EXISTS idx_node_chunks_node_id ON node_chunks(node_id);
CREATE INDEX IF NOT EXISTS idx_node_chunks_fts ON node_chunks USING gin(fts_tokens);
CREATE INDEX IF NOT EXISTS idx_node_chunks_embedding ON node_chunks USING hnsw (embedding vector_cosine_ops);
