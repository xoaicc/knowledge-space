# 🚀 Knowledge Space — AI-Native Second Brain Platform & Vault Template

> **Knowledge Space** là nền tảng quản lý tri thức cá nhân thế hệ mới (AI-Native Second Brain Platform). Được xây dựng trên nguyên tắc **Markdown là Nguồn Sự Thật Duy Nhất (Single Source of Truth)** kết hợp với hạ tầng **Knowledge Engine (FastAPI + PostgreSQL 16 + pgvector + BAAI/bge-m3 + GraphRAG)**.

---

## 🌟 Tính năng Cốt lõi (Key Features)

- **AI-Native Engine (GraphRAG & Hybrid Search)**: Kết hợp Vector Search 1024 chiều (`BAAI/bge-m3`), Full-Text Search RRF và Đồ thị tri thức PostgreSQL N-nấc.
- **Thích ứng Sư phạm (Pedagogical Adaptability L1 - L4)**: Tự động điều chỉnh ngôn ngữ giải thích theo Thang trình độ tư duy (`L1_INTUITIVE` Ẩn dụ đời sống ➔ `L4_ARCHITECTURE` Thiết kế hệ thống).
- **Phân giải Danh xưng Đa ngôn ngữ (Canonical & Alias Resolver)**: 
  - Tự động nhận diện cả từ viết tắt Tiếng Việt (`CNTT`), Tiếng Anh (`IT`), từ phổ biến và từ bản địa.
  - Tự động gắn Wiki Link dạng Obsidian Alias: `[[IT|CNTT]]` hoặc `[[Garbage Collection|thu gom rác]]`.
- **Trình bày Tiếng Việt Native Standard**: 100% tiêu đề dùng dạng **Normal case** (`# Định nghĩa`, `# Mô hình thực thi`).
- **Giao diện Obsidian Sạch 100%**: 
  - Thư mục hỗ trợ người dùng `_` (`_Templates`, `_Archive`, `_Attachments`) giúp Obsidian dán ảnh (`Ctrl+V`) mượt 100%, Templater (`Alt+N`) nhận mẫu tức thì.
  - Cấu hình AI Agent ẩn 100% trong `.system`.
  - Mã nguồn Backend Engine nằm ẩn 100% trong `.knowledge_service` với kiến trúc Modular Packages sạch sẽ.
- **Đóng gói Docker Compose Full-Stack**: Chạy toàn bộ hạ tầng PostgreSQL 16 `pgvector` và FastAPI Knowledge Engine chỉ bằng 1 lệnh.

---

## 📂 Cấu trúc Vault & Kiến trúc Backend Modular (Directory Blueprint)

```
KnowledgeSpace/
├── Glossary.md              # 📖 Từ điển Thuật ngữ Tra cứu Nhanh (User & AI accessible)
│
├── Concept/                 # 🟢 Thư mục chứa các Concept mới (.gitkeep rỗng)
├── Collection/              # 🟢 Thư mục chứa các Collection mới (.gitkeep rỗng)
├── Domain/                  # 🟢 Thư mục chứa các Domain mới (.gitkeep rỗng)
├── Map/                     # 🟢 Thư mục chứa các Map mới (.gitkeep rỗng)
│
├── _Templates/              # 📝 4 File Mẫu Tạo Note (Concept, Collection, Domain, Map)
├── _Archive/                # 📦 Kho lưu trữ note cũ (.gitkeep rỗng)
├── _Attachments/            # 📸 Hình ảnh & Phương tiện đính kèm (.gitkeep rỗng, ignore ảnh dán)
├── .obsidian/               # 🎨 Cấu hình Giao diện & Plugins Obsidian
│
├── .system/                 # 🙈 File Cấu hình AI Agent Ẩn (Agents, Playbooks, User Profile)
│   ├── Agents.md            # Operating Protocol cho AI Agent
│   ├── Playbooks.md         # Bản thiết kế Kiến trúc & Guide Vận hành
│   ├── Knowledge Model.md   # Mô hình Dữ liệu Quan hệ
│   └── User Profile.md      # Hồ sơ Tri thức Cá nhân & Thang Tư duy L1-L4
│
└── .knowledge_service/      # 🚀 Modular FastAPI Backend Engine (Ẩn 100% khỏi Sidebar Obsidian)
    ├── db/                  # Hạ tầng CSDL PostgreSQL Schema
    │   └── init.sql         # SQL Schema (tables, pgvector, indexes)
    │
    ├── core/                # Các Module Cốt lõi (Ingestion, Parsing & Indexing)
    │   ├── config.py        # Cấu hình Môi trường & Models
    │   ├── parser.py        # Phân tích Markdown & Term-Level Micro-Chunking
    │   └── indexer.py       # Incremental Indexer Engine
    │
    ├── services/            # Các Dịch vụ Xử lý Tri thức Chuyên sâu
    │   ├── graph_engine.py  # Hybrid Search (FTS + Vector BAAI/bge-m3 + Reranker + Graph)
    │   ├── auto_linker.py   # Dual-Language Wiki Link Generator [[Title|Alias]]
    │   ├── reasoning_engine.py  # Decision Support & Reasoning System
    │   ├── synthesis_engine.py  # Cross-domain Knowledge Synthesis Engine
    │   ├── refactor_engine.py   # Markdown Formatting & Refactor Engine
    │   ├── roadmap_engine.py    # Personal Learning Roadmap Engine
    │   └── user_profiler.py     # Pedagogical Adaptation Engine (L1-L4)
    │
    ├── main.py              # REST API Entrypoint chính (FastAPI REST Server)
    ├── indexer_cli.py       # CLI Script chạy đánh chỉ mục (python indexer_cli.py)
    ├── Dockerfile           # Docker Image Build Specification
    └── docker-compose.yml   # Full Stack Docker Compose Setup
```

---

## ⚙️ Cấu hình Mô hình AI & Tự động Tải (AI Model Configuration)

Hệ thống **tự động tải mô hình (Auto-Download)** từ Hugging Face Hub về máy tính trong lần khởi chạy đầu tiên (`~/.cache/huggingface`). Bạn không cần phải tải thủ công bất kỳ file weights nào.

### Tùy chọn Mô hình theo Phần cứng (Hardware Configuration Presets)

Bạn có thể thay đổi biến môi trường trong file `.knowledge_service/core/config.py` để phù hợp với phần cứng máy tính:

| Cấu hình Phần cứng | Embeddings Model (`EMBEDDING_MODEL_NAME`) | Reranker Model (`RERANKER_MODEL_NAME`) | Ghi chú |
| :--- | :--- | :--- | :--- |
| 🚀 **High-Performance (GPU / Default)** | `BAAI/bge-m3` | `BAAI/bge-reranker-base` | Đa ngôn ngữ, Vector 1024d, Reranking chính xác cao |
| ⚡ **CPU Low-Spec (Máy CPU thấp)** | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | `BAAI/bge-reranker-small` | Siêu nhẹ, phản hồi sub-second trên CPU |
| 🌐 **Cloud API** | OpenAI `text-embedding-3-small` | Cohere Rerank API | Không tốn RAM/GPU local |

---

## ⚡ Hướng dẫn Vận hành Nhanh (Quick Start Guide)

### 1. Mở Vault bằng Obsidian
Tải và mở thư mục **`KnowledgeSpace`** trực tiếp trong phần mềm [Obsidian](https://obsidian.md).

### 2. Khởi chạy Backend Service bằng Docker Compose
Yêu cầu: Đã cài đặt Docker Desktop.

```powershell
# Di chuyển vào thư mục backend ẩn
cd .knowledge_service

# Khởi chạy Docker Compose (PostgreSQL 5434 & FastAPI 8000)
docker compose up -d
```

### 3. Cài đặt Virtualenv & Đánh chỉ mục Vault
```powershell
cd .knowledge_service

# Tạo môi trường ảo Python
python -m venv venv
.env\Scriptsctivate

# Cài đặt thư viện phụ thuộc
pip install -r requirements.txt

# Chạy script đánh chỉ mục CLI
python indexer_cli.py
```

- **Kiểm tra Trạng thái API**: Mở trình duyệt truy cập `http://127.0.0.1:8000/health`.

---

## 🌐 Danh mục REST API Endpoints (`http://127.0.0.1:8000`)

| Endpoint | Method | Mục đích |
| :--- | :--- | :--- |
| `/health` | `GET` | Kiểm tra trạng thái hệ thống & các mô hình |
| `/api/search/graph-rag` | `POST` | Full GraphRAG Search (Vector BAAI/bge-m3 + FTS + Reranker BAAI/bge-reranker-base + Multi-hop Graph) |
| `/api/agent/suggest-links` | `POST` | Tự động phân tích văn bản và chèn Wiki Links `[[Note]]` / `[[Title\|Alias]]` |
| `/api/agent/gap-detection` | `POST` | Quét báo cáo các note mồ côi (Orphan nodes) và thiếu metadata |
| `/api/agent/refactor` | `POST` | Tự động refactor note Markdown theo chuẩn Vault |
| `/api/reasoning/synthesis` | `POST` | Tổng hợp tri thức liên miền giữa 2 chủ đề bất kỳ |
| `/api/reasoning/build-map` | `POST` | Tự động sinh nội dung Map of Content (MOC) |
| `/api/reasoning/decision-support` | `POST` | Báo cáo phân tích hỗ trợ ra quyết định grounded trong Vault |
| `/api/profile` | `GET` | Lấy Hồ sơ Tri thức Cá nhân & Cognitive Level |
| `/api/profile/adapt-explanation` | `POST` | Tùy biến bài giải thích theo Cognitive Level (L1 - L4) |
| `/api/profile/generate-roadmap` | `POST` | Sinh file Lộ trình Học tập Cá nhân hóa |

---

## 📜 Giấy phép & Đóng góp (License)

Dự án phát triển mã nguồn mở theo giấy phép **MIT License**. Mọi đóng góp cải tiến đều được chào đón!
