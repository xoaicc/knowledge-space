import os
import re
from typing import Dict, Any, Optional

from core.config import VAULT_ROOT

PROFILE_FILE_PATH = str(VAULT_ROOT / ".system/User Profile.md")

class UserProfileManager:
    def __init__(self, profile_path: str = PROFILE_FILE_PATH):
        self.profile_path = profile_path

    def load_profile(self) -> Dict[str, Any]:
        """Loads and parses Knowledge/.system/User Profile.md."""
        if not os.path.exists(self.profile_path):
            return {
                "cognitive_level": "L3_TECHNICAL",
                "target_role": "AI System Architect",
                "focus_areas": ["Vector DB", "Knowledge Graphs"],
                "explanation_style": "balanced_technical"
            }

        with open(self.profile_path, "r", encoding="utf-8") as f:
            content = f.read()

        cog_level = "L3_TECHNICAL"
        role = "AI System Architect"
        focus_areas = []

        m_cog = re.search(r"cognitive_level:\s*([A-Z0-9_]+)", content)
        if m_cog:
            cog_level = m_cog.group(1).strip()

        m_role = re.search(r"target_role:\s*(.+)", content)
        if m_role:
            role = m_role.group(1).strip()

        m_focus = re.findall(r"-\s*(.+)", content)
        if m_focus:
            focus_areas = [f.strip() for f in m_focus[:5]]

        return {
            "cognitive_level": cog_level,
            "target_role": role,
            "focus_areas": focus_areas,
            "raw_content": content
        }

    def estimate_cognitive_level(self, query_text: str, current_level: str = "L3_TECHNICAL") -> str:
        """
        Dynamically estimates cognitive level based on query intent & vocabulary:
        - L1_INTUITIVE: Requests simple metaphors, non-technical phrasing ("đơn giản", "người không học IT", "bình dị").
        - L2_CONCEPTUAL: High-level overview ("là gì", "tổng quan", "khái niệm").
        - L3_TECHNICAL: Deep technical ("thuật toán", "cơ chế", "mã nguồn", "memory allocation").
        - L4_ARCHITECTURE: System design ("kiến trúc", "tradeoff", "scalable", "hạ tầng").
        """
        text_lower = query_text.lower()

        if any(w in text_lower for w in ["đơn giản", "người không học it", "dễ hiểu", "bình dị", "ví dụ đời sống", "ẩn dụ"]):
            return "L1_INTUITIVE"
        
        if any(w in text_lower for w in ["kiến trúc", "tradeoff", "trade-off", "scalable", "hạ tầng", "phân tán", "system design"]):
            return "L4_ARCHITECTURE"

        if any(w in text_lower for w in ["thuật toán", "cơ chế", "mã nguồn", "memory allocation", "mark-and-sweep", "cpython", "jvm"]):
            return "L3_TECHNICAL"

        if any(w in text_lower for w in ["là gì", "tổng quan", "định nghĩa", "khái niệm"]):
            return "L2_CONCEPTUAL"

        return current_level

    def adapt_explanation(self, explanation: str, level: str) -> str:
        """
        Formats and adapts the explanation based on the target Cognitive Level.
        """
        header = f"### [Thích ứng Tư duy: {level}]\n\n"

        if level == "L1_INTUITIVE":
            header += "> 💡 **Góc nhìn Ẩn dụ Bình dị (Intuitive View)**: Giải thích bằng hình ảnh đời sống thực tế, không dùng thuật ngữ chuyên ngành nặng.\n\n"
            # Simplify wording
            adapted = explanation.replace("Garbage Collection", "Xe Dọn Rác Tự Động")
            adapted = adapted.replace("JVM", "Môi trường Chạy ứng dụng")
            return header + adapted

        elif level == "L2_CONCEPTUAL":
            header += "> 📚 **Góc nhìn Khái niệm (Conceptual View)**: Tập trung vào định nghĩa chuẩn và luồng hoạt động cơ bản.\n\n"
            return header + explanation

        elif level == "L3_TECHNICAL":
            header += "> 🛠️ **Góc nhìn Kỹ thuật (Technical View)**: Đi sâu vào thuật toán, cơ chế chi tiết và mã nguồn.\n\n"
            return header + explanation

        elif level == "L4_ARCHITECTURE":
            header += "> 🏛️ **Góc nhìn Kiến trúc Hệ thống (System Architecture View)**: Tập trung vào thiết kế hệ thống, so sánh trade-offs và khả năng mở rộng.\n\n"
            return header + explanation

        return header + explanation

if __name__ == "__main__":
    mgr = UserProfileManager()
    profile = mgr.load_profile()
    print("Profile Loaded:", profile["cognitive_level"], "| Role:", profile["target_role"])
    
    sample_q = "Giải thích đơn giản Garbage Collection như cho người không học IT"
    est_level = mgr.estimate_cognitive_level(sample_q)
    print("Estimated Level for query:", est_level)
    print(mgr.adapt_explanation("Garbage Collection chạy trên JVM giúp thu hồi RAM.", est_level))
