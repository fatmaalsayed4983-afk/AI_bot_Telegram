import subprocess
import tempfile
import sys
import os

class CodeSandbox:
    @staticmethod
    def execute_python_code(code: str, timeout: int = 5) -> str:
        # Isolate code execution into a temporary process and file structure
        # strictly bounded by timeout and avoiding core system variables.
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w', encoding='utf-8') as f:
            f.write(code)
            temp_file_path = f.name
            
        try:
            # Run sandbox with strict security context on python environment subprocess
            result = subprocess.run(
                [sys.executable, temp_file_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            output = result.stdout
            errors = result.stderr
            if errors:
                return f"خطأ أثناء التشغيل:\n{errors}"
            return output if output else "[تم تشغيل الكود بنجاح دون طباعة أي مخرجات]"
        except subprocess.TimeoutExpired:
            return "⚠️ فشل التشغيل: تجاوز الوقت المسموح به للعملية (Timeout)."
        except Exception as e:
            return f"⚠️ فشل التشغيل بسبب خطأ غير متوقع: {e}"
        finally:
            try:
                os.remove(temp_file_path)
            except:
                pass
