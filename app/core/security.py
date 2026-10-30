import os
import html
import re

class SecurityChecker:
    @staticmethod
    def is_safe_path(base_dir: str, target_path: str) -> bool:
        # Ensure the file path doesn't try directory traversal
        absolute_base = os.path.abspath(base_dir)
        absolute_target = os.path.abspath(target_path)
        return absolute_target.startswith(absolute_base)

    @staticmethod
    def sanitize_html_text(text: str) -> str:
        # Highly robust parser to convert markdown or standard responses into safe Telegram HTML
        code_blocks = []
        def extract_code(match):
            lang = match.group(1) or ""
            code = match.group(2)
            code_blocks.append((lang, code))
            return f"___CODE_PLACEHOLDER_{len(code_blocks)-1}___"

        # Replace code blocks to preserve spacing and syntax
        clean_text = re.sub(r'```(\w*)\n(.*?)```', extract_code, text, flags=re.DOTALL)
        
        # Escape general HTML
        clean_text = html.escape(clean_text)
        
        # Process inline markdown elements
        clean_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', clean_text)
        clean_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', clean_text)
        clean_text = re.sub(r'`(.*?)`', lambda m: f"<code>{html.escape(m.group(1))}</code>", clean_text)

        # Re-inject processed code blocks safely
        for i, (lang, code) in enumerate(code_blocks):
            safe_code = html.escape(code)
            code_html = f"<pre><code class=\"language-{lang}\">{safe_code}</code></pre>"
            clean_text = clean_text.replace(f"___CODE_PLACEHOLDER_{i}___", code_html)
            
        return clean_text
