import subprocess
from pathlib import Path

class Cybernetics:
    def execute(self, cmd):
        """Wykonuje komendę systemową i zwraca wynik."""
        try:
            # Timeout 10s dla bezpieczeństwa
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True, timeout=10)
            return f"[SYSTEM OUTPUT]:\n{result}"
        except subprocess.CalledProcessError as e:
            return f"[ERROR code {e.returncode}]:\n{e.output}"
        except subprocess.TimeoutExpired:
            return "[ERROR]: Command timed out."

    def read_file(self, path):
        p = Path(path)
        if p.exists() and p.is_file():
            try:
                content = p.read_text(encoding='utf-8')
                return f"[FILE: {path}]\n{content[:3000]}"
            except Exception as e:
                return f"[READ ERROR]: {str(e)}"
        return "[ERROR]: File not found."