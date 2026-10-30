class ModelRouter:
    @staticmethod
    def decide_best_model(user_query: str, has_image: bool = False, has_file: bool = False) -> str:
        query_lower = user_query.lower()
        
        if has_image:
            return "vision-supported"
            
        # Coding task detection
        code_keywords = ["code", "برمجة", "اكتب كود", "سورس", "python", "javascript", "c++", "html", "css", "وظيفة", "خطأ", "bug"]
        if any(keyword in query_lower for keyword in code_keywords):
            return "coding-reasoning"
            
        # Search-heavy keywords
        search_keywords = ["سعر", "أخبار", "طقس", "اليوم", "مباراة", "ترتيب", "سعر الصرف", "من هو"]
        if any(keyword in query_lower for keyword in search_keywords):
            return "search-heavy"
            
        return "fast-standard"
