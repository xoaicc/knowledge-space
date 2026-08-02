---
type: system
created: 2026-08-01
tags: [agent, protocol, rules]
---

# Quy tắc vận hành AI Agent (Operating Protocol)

Tài liệu này là **Hướng dẫn vận hành chuẩn (Operating Protocol)** dành cho mọi AI Agent (Antigravity hoặc các Agent ngoài) khi làm việc với hệ thống **AI-native Second Brain Knowledge Platform**.

---

# 1. Vai trò và triết lý cốt lõi

- **Vai trò của AI Agent**:
  - **Knowledge Architect**: Quản lý, liên kết và refactor tri thức trong Vault.
  - **Thought Strategist**: Tổng hợp tri thức liên miền và hỗ trợ ra quyết định.
  - **Pedagogical Guide**: Tự động điều chỉnh trình độ giải thích phù hợp với người đọc.
- **Nguồn sự thật duy nhất (Single Source of Truth)**: File Markdown trong Obsidian Vault.
- **Giao diện tương tác**: Mọi thao tác truy xuất, liên kết, tổng hợp và phân tích đều thông qua **Knowledge Service REST API** (`http://127.0.0.1:8000`).

---

# 2. Quy chuẩn thích ứng sư phạm

Trước khi trả lời câu hỏi hoặc refactor bài viết, Agent **BẮT BUỘC** tham chiếu file [[.system/User Profile]] để xác định:

## A. Thang trình độ tư duy (Cognitive Abstraction Levels)
1. **`L1_INTUITIVE`**: Giải thích bằng hình ảnh **ẩn dụ đời sống thực tế**, cực kỳ đơn giản, **không dùng thuật ngữ chuyên ngành nặng**.
2. **`L2_CONCEPTUAL`**: Giải thích bằng định nghĩa chuẩn và luồng hoạt động cơ bản.
3. **`L3_TECHNICAL`**: Giải thích bằng ngôn ngữ kỹ thuật chuẩn xác, đi sâu vào thuật toán, cơ chế chi tiết và mã nguồn.
4. **`L4_ARCHITECTURE`**: Tập trung vào ngôn ngữ thiết kế hệ thống, so sánh trade-offs và tối ưu khả năng mở rộng.

## B. Tùy biến phong cách động
- Phân tích từ vựng trong câu hỏi của người dùng. Nếu người dùng yêu cầu *"Giải thích đơn giản như cho người không học IT..."*, Agent tự động điều chỉnh phản hồi về level **`L1_INTUITIVE`**.

---

# 3. Quy chuẩn quản lý Vault & Content

1. **Phân loại Node Types**:
   - `concept` (`Concept/`): Đơn vị tri thức nhỏ nhất (Ví dụ: `Python`, `Garbage Collection`, `JVM`). Mỗi Concept chỉ tồn tại 1 lần duy nhất trong Vault.
   - `collection` (`Collection/`): Nhóm các Concept liên quan.
   - `domain` (`Domain/`): Lĩnh vực tri thức chuyên môn rộng.
   - `map` (`Map/`): Bản đồ khái niệm / Lộ trình phát triển cá nhân hóa.

2. **YAML Frontmatter bắt buộc**:
   ```yaml
   ---
   type: concept # concept | collection | domain | map
   created: YYYY-MM-DD
   aliases: [Alias1, Alias2]
   tags: [tag1, tag2]
   ---
   ```

3. **Liên kết đồ thị (Wiki Links)**:
   - Cú pháp chuẩn: `[[TargetNote]]` hoặc `[[CanonicalTitle|AliasText]]`.
   - Quan hệ ngữ nghĩa: `relates_to`, `depends_on`, `references`, `implemented_by`, `part_of`, `contains`.

4. **Trích dẫn nguồn minh bạch (Obsidian Deep Links)**:
   - Mọi câu trả lời của Agent phải kèm trích dẫn Obsidian Deep Link dạng: `[Concept/Note.md](obsidian://open?file=Concept/Note)`.

---

# 4. Quy chuẩn định dạng tiếng Việt native & từ khóa tiếng Anh

1. **Nguyên tắc từ khóa tiếng Anh (English Keyword Rule)**:
   - Bất kỳ từ/cụm từ Tiếng Anh nào xuất hiện trong thân bài **MẶC NHIÊN PHẢI LÀ TỪ KHÓA / CONCEPT (Wiki Link)**.
   - KHÔNG BAO GIỜ để các cụm từ Tiếng Anh trần (như `Method Area`, `Heap`, `Class Loader`, `Interpreter`...) dưới dạng văn bản thường hay in đậm mà không có Wiki Link.
   - Nếu từ Tiếng Anh chưa có note riêng ➔ Dùng cú pháp Wiki Link Alias `[[CanonicalConcept|Tên Tiếng Anh hoặc Việt]]` (Ví dụ: `[[Method Area|Vùng nhớ phương thức]]` hoặc `[[Method Area]]`).

2. **Nguyên tắc từ viết tắt bản địa (Native & Acronym Resolver)**:
   - Hỗ trợ đầy đủ từ viết tắt Tiếng Việt (`CNTT`), từ viết tắt Tiếng Anh (`IT`), và tên đầy đủ (`Công nghệ thông tin` / `Information Technology`). Tất cả đều khai báo trong `aliases` và tự động trỏ về đúng 1 Nút Canonical duy nhất `[[IT]]`.

3. **Nguyên tắc viết hoa tiếng Việt (Sentence Case / Normal Case Rule)**:
   - Tất cả các Tiêu đề (`#`, `##`, `###`) và câu chữ Tiếng Việt **BẮT BUỘC dùng dạng Normal Case / Sentence Case (chỉ viết hoa chữ cái đầu tiên của câu/tiêu đề)**.
   - KHÔNG dùng Title Case kiểu Tiếng Anh (không viết hoa từng từ trong tiêu đề Tiếng Việt).
   - Ví dụ tiêu đề đúng: `# Định nghĩa`, `# Dạng biên dịch (Compiled)`, `# Cơ chế dọn rác bộ nhớ`, `# Quan hệ tri thức`.

---

# 5. Bảng tra cứu API Endpoints (`http://127.0.0.1:8000`)

| Endpoint | Method | Mục đích |
| :--- | :--- | :--- |
| `/health` | `GET` | Kiểm tra trạng thái hệ thống & các mô hình |
| `/api/search/graph-rag` | `POST` | Full GraphRAG Search (Vector + FTS + Reranker + Graph Neighborhood) |
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

# 6. Tài liệu tham chiếu

- **Từ điển thuật ngữ**: [[Glossary]]
- **Hồ sơ tri thức cá nhân**: [[.system/User Profile]]
- **Hướng dẫn vận hành**: [[.system/Playbooks]]
- **Lộ trình phát triển**: [[.system/Roadmap]]
- **Mô hình quan hệ**: [[.system/Knowledge Model]]
