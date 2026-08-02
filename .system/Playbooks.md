---
type: system
created: 2026-08-01
tags: [playbook, docker, architecture]
---

# Bản thiết kế kiến trúc & Hướng dẫn vận hành hệ thống (Blueprint & Playbook)

Tài liệu này trình bày sơ đồ kiến trúc và hướng dẫn từng bước để **tái lập (replicate)** toàn bộ hệ thống **AI-native Second Brain Knowledge Platform**.

---

# 1. Triết lý & sơ đồ kiến trúc

## A. Triết lý nguồn sự thật duy nhất (Single Source of Truth)
- **Obsidian Vault** (.md files) là nơi lưu trữ tri thức duy nhất.
- AI chịu trách nhiệm đánh chỉ mục, truy xuất, liên kết và refactor tri thức thông qua **Knowledge Service REST API**.

## B. Vận hành hạ tầng (Full Docker Compose)
1. **Khởi chạy toàn bộ hệ thống bằng Docker Compose**:
   ```powershell
   cd .knowledge_service
   docker compose up -d
   ```
   - **`knowledge_postgres`**: Hạ tầng Postgres 16 + `pgvector` (cổng `5434`).
   - **`knowledge_service_api`**: FastAPI Knowledge Engine (cổng `8000`), mount trực tiếp cache mô hình từ `D:/.cache/huggingface`.
2. **Quét & Đánh chỉ mục tăng tiến**:
   ```powershell
   cd .knowledge_service
   .env\Scripts\python.exe indexer.py
   ```

## C. Sơ đồ thành phần hệ thống

```
Obsidian Vault (Markdown Files)
       │
       ▼ (Incremental Indexer - MD5 Checksum & Dual-Language Alias Resolver)
PostgreSQL 16 + pgvector (Port 5434)
 ├── nodes (Metadata, Type, Aliases, Tags, Checksum)
 ├── node_aliases (Multilingual & Acronym Alias Table)
 ├── node_relationships (Knowledge Graph Links)
 └── node_chunks (Section Chunks + Glossary Micro-Chunks + 1024d HNSW Vectors + GIN tsvector)
       │
       ▼ (FastAPI Knowledge Service - Port 8000)
Knowledge Retrieval Engine
 ├── Hybrid Search (FTS + Dense Vector RRF)
 ├── Cross-Encoder Reranker (BAAI/bge-reranker-base + Threshold Filter)
 ├── Multi-hop Graph Navigation (PostgreSQL Recursive CTEs)
 ├── Pedagogical Profiler (L1-L4 Explanation Adapter & Roadmap Engine)
 └── Citation Generator (Obsidian Deep Link Tracing)
       │
       ▼ (REST API Endpoints)
AI Agent / Chat Interface (Phase 1 ➔ Phase 7A)
```

---

# 2. Quy chuẩn dữ liệu Vault

Để hệ thống tự động bóc tách và tạo đồ thị tri thức, các note trong Vault tuân thủ 3 chuẩn sau:

## 1. Phân loại Node (`type`)
- `concept`: Khái niệm lý thuyết cốt lõi (ví dụ: Garbage Collection, OOP, JVM).
- `collection`: Tập hợp tài liệu, thư viện hoặc tài nguyên.
- `domain`: Lĩnh vực tri thức chuyên sâu.
- `map`: Bản đồ khái niệm liên kết (Map of Content).
- `glossary`: Từ điển thuật ngữ tra cứu nhanh.

## 2. Standard YAML Frontmatter
```yaml
---
type: concept
created: YYYY-MM-DD
aliases: [Alias1, Alias2]
tags: [tag1, tag2]
---
```

## 3. Liên kết đồ thị (Wiki Links)
- Cú pháp chuẩn: `[[TargetNote]]` hoặc `[[CanonicalTitle|AliasText]]`.
- Mối quan hệ ngữ nghĩa: `relates_to`, `depends_on`, `references`, `implemented_by`, `part_of`, `contains`.

---

# 3. Quy trình tái lập hệ thống (Step-by-Step Replication Guide)

## Bước 1: Khởi tạo Cơ sở dữ liệu PostgreSQL + pgvector
- Chạy container `pgvector/pgvector:pg16`.
- Tạo 4 bảng chính:
  1. `nodes`: Lưu vết file, checksum MD5, tiêu đề và metadata.
  2. `node_aliases`: Lưu bảng tra cứu từ viết tắt và danh xưng đa ngôn ngữ (`node_id`, `alias`, `alias_lower`).
  3. `node_relationships`: Lưu quan hệ đồ thị giữa các nút (`source_node_id`, `target_node_id`, `relation_type`).
  4. `node_chunks`: Lưu văn bản cắt nhỏ theo thẻ Heading (`#`) và Micro-Chunks cho Glossary, chứa vector 1024 chiều (HNSW Index) và token Full-Text Search (GIN Index).

## Bước 2: Xây dựng Trình đánh chỉ mục tăng tiến & Alias Resolver
- Quét cây thư mục Vault. So sánh checksum MD5 của từng file với DB để chỉ index những file mới hoặc có chỉnh sửa.
- Tự động tách `aliases` trong YAML Frontmatter và chèn vào bảng `node_aliases`.
- Gọi mô hình `BAAI/bge-m3` để tạo vector 1024 chiều cho từng chunk.

## Bước 3: Triển khai Knowledge Retrieval Engine (FastAPI)
- **Hybrid Search**: Kết hợp Vector Search + Full-Text Search qua công thức Reciprocal Rank Fusion:
  $$RRF\_Score = rac{1}{60 + Rank_{vec}} + rac{1}{60 + Rank_{fts}}$$
- **Cross-Encoder Reranking**: Dùng `BAAI/bge-reranker-base` chấm lại điểm phù hợp ngữ nghĩa và áp dụng bộ lọc ngưỡng (`min_score >= 0.0`) để loại bỏ 100% tài liệu nhiễu.
- **Alias-Aware Auto Linker**: Tự động chèn Obsidian Wiki Link dạng `[[CanonicalTitle|AliasText]]`.
- **Citation Tracing**: Tự động sinh Obsidian Deep Link (`obsidian://open?file=...`) để AI trích dẫn nguồn chính xác.

---

# 4. Định hướng mở rộng mô hình (Branching Strategy)

- **Track A (Local-First Personal Brain - Khuyên dùng)**: Tối ưu 100% trên hạ tầng PostgreSQL + Mô hình local nhẹ (`bge-m3` + `bge-reranker-base`). Phản hồi sub-2-seconds, an toàn tuyệt đối cho phần cứng máy tính.
- **Track B (SaaS Cloud Cluster)**: Tách riêng hạ tầng phân tán: PostgreSQL (Metadata) + Qdrant Cluster (Dedicated Vector DB) + Neo4j Enterprise (Dedicated Knowledge Graph DB) khi phát triển thương mại hóa cho nhiều người dùng.
