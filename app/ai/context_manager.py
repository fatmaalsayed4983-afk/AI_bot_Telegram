class ContextManager:
    @staticmethod
    def get_managed_context(history_messages: list, max_chars: int = 12000) -> list:
        # Simplistic and efficient sliding window character-budget limit
        # Preserves early history if needed, or simply reduces context size by taking the latest messages.
        managed_history = []
        char_count = 0
        
        # Iterate backwards to preserve latest context
        for msg in reversed(history_messages):
            msg_content = msg["content"]
            char_count += len(msg_content)
            if char_count > max_chars:
                break
            managed_history.insert(0, {"role": msg["role"], "content": msg_content})
            
        return managed_history
