import re

class MemorySystem:
    # Evaluates whether an input message has memory-worthy personal facts
    @staticmethod
    def parse_and_extract_memory(text: str) -> str:
        triggers = [
            r"اسمي\s+(\w+)",
            r"أنا\s+(طالب|مطور|مبرمج|مهندس|طبيب|كاتب|مصمم)",
            r"أحب\s+(\w+)",
            r"لغتي المفضلة هي\s+(\w+)",
            r"تذكر أنني\s+(.+)",
            r"احفظ أن\s+(.+)"
        ]
        
        for trigger in triggers:
            match = re.search(trigger, text, re.IGNORECASE)
            if match:
                # If user wants to save memory directly or matched patterns
                return text
        return ""
