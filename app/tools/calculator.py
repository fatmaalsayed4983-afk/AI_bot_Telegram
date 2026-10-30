class SimpleCalculator:
    @staticmethod
    def calculate(expression: str) -> str:
        # Only allow simple safe mathematical characters
        import string
        allowed = set(string.digits + " +-*/().")
        if not set(expression).issubset(allowed):
            return "تعبير غير آمن."
        try:
            return str(eval(expression, {"__builtins__": None}, {}))
        except Exception as e:
            return f"خطأ في الحساب: {e}"
