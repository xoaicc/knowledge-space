---
type: system
created: 2026-08-01
tags: [model, relationships, ontology]
---

# Mô hình quan hệ dữ liệu (Knowledge Model)

Mô tả các mối quan hệ ngữ nghĩa giữa các node types trong hệ thống.

# Concept

```
Concept
    ├── relates_to        → Liên quan đến concept khác
    ├── depends_on        → Phụ thuộc vào concept khác
    ├── implemented_by    → Được triển khai bởi concept khác
    ├── example_of        → Là ví dụ của concept khác
    └── part_of           → Là một phần của concept khác
```

**Ví dụ:**
- [[Python]] `relates_to` [[OOP]]
- [[Execution Model]] `depends_on` [[JVM]]
- [[Garbage Collection]] `part_of` [[Memory Management]]

# Collection

```
Collection
    └── contains          → Chứa các Concept
```

# Domain

```
Domain
    └── references        → Tham chiếu đến Collections/Concepts
```

# Map

```
Map
    └── organizes         → Tổ chức Concepts theo lộ trình
```

# Tài liệu tham chiếu

- [[Glossary]] - Từ điển thuật ngữ tra cứu nhanh
- [[.system/Agents]] - Quy tắc vận hành AI Agent
