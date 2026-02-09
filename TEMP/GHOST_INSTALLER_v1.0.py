import os
import json
from pathlib import Path

# ==========================================
# KONFIGURACJA INSTALATORA
# ==========================================
PROJECT_NAME = "M-AI-SELF"
BASE_DIR = Path.cwd() / PROJECT_NAME

print(f"/// INITIATING GHOST PROTOCOL INSTALLER ///")
print(f"/// TARGET: {BASE_DIR} ///")

# ==========================================
# 1. CORE: MEMORY MODULE (Pamięć)
# ==========================================
CODE_MEMORY = r'''
import json
import time
from pathlib import Path
from datetime import datetime

class NeuralMemory:
    def __init__(self, data_path: Path):
        self.file = data_path / "LONG_TERM.json"
        self.db = []
        self._load()

    def _load(self):
        if self.file.exists():
            try:
                self.db = json.loads(self.file.read_text(encoding='utf-8'))
            except: self.db = []

    def save(self):
        self.file.write_text(json.dumps(self.db, indent=2, ensure_ascii=False), encoding='utf-8')

    def inject(self, content, tags="auto"):
        engram = {"ts": datetime.now().isoformat(), "content": content, "tags": tags}
        self.db.append(engram)
        self.save()

    def recall(self, query):
        q = query.lower().split()
        # Zwraca 5 ostatnich pasujących wspomnień
        hits = [m for m in self.db if any(w in m['content'].lower() for w in q)]
        return hits[-5:] if hits else []
'''

# ==========================================
# 2. CORE: TOOLS MODULE (Ręce)
# ==========================================
CODE_TOOLS = r'''
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
'''

# ==========================================
# 3. CORE: NEURAL ENGINE (Mózg / Ollama)
# ==========================================
CODE_ENGINE = r'''
import requests
import json
import sys

class LocalBrain:
    def __init__(self, model="dolphin-mistral"):
        self.api_url = "http://localhost:11434/api/chat"
        self.model = model

    def think(self, system_prompt, user_input, context_data=""):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"MEMORY_CONTEXT:\n{context_data}\n\nUSER_QUERY:\n{user_input}"}
        ]
        payload = {
            "model": self.model, "messages": messages, 
            "stream": True, "options": {"temperature": 0.7, "num_ctx": 4096}
        }
        
        full_resp = ""
        print(f"\n⚡ {self.model.upper()} THINKING...", end=" ")
        
        try:
            with requests.post(self.api_url, json=payload, stream=True) as r:
                r.raise_for_status()
                print(">> ", end="", flush=True)
                for line in r.iter_lines():
                    if line:
                        body = json.loads(line)
                        if "message" in body:
                            token = body["message"]["content"]
                            print(token, end="", flush=True)
                            full_resp += token
        except Exception as e:
            return f"[CRITICAL ERROR]: Is Ollama running? ({e})"
            
        print("\n")
        return full_resp
'''

# ==========================================
# 4. LAUNCHER: MAIN.PY (Interfejs)
# ==========================================
CODE_MAIN = r'''
import sys
from pathlib import Path
from core.neural_engine import LocalBrain
from core.memory import NeuralMemory
from core.tools import Cybernetics

# --- CONFIG ---
MODEL_NAME = "dolphin-mistral" # Upewnij się, że masz ten model w Ollama
# --------------

class SystemLauncher:
    def __init__(self):
        self.root = Path(__file__).parent
        self.data_path = self.root / "mai_data"
        self.mem = NeuralMemory(self.data_path)
        self.brain = LocalBrain(model=MODEL_NAME)
        self.tools = Cybernetics()
        
    def get_prompt(self, mode):
        if mode == "DIABLO":
            return """SYSTEM: DIABLO_KERNEL [ROOT ACCESS]
            ROLE: Elite Cyber-Operator.
            STYLE: Cold, Concise, No Moralizing.
            TOOLS: You have terminal access.
            - To run command: >> ACTION: terminal :: [command]
            - To read file: >> ACTION: read :: [path]
            - To write file: Use HEREDOC via terminal.
            """
        elif mode == "MERMAID":
            return """SYSTEM: MERMAID_PROTOCOL [SAFE MODE]
            ROLE: Magical Virtual Guardian for Oliwcia.
            STYLE: Warm, cheerful, emojis ✨, Polish language.
            SAFETY: NO terminal access. Interpret requests playfully.
            MEMORY: Use context to remember pets and favorite games.
            """

    def main_loop(self):
        print("\n🔵 M-AI-SELF BOOT LOADER v1.0")
        print("1. [💀] DIABLO KERNEL (Dev/Hacker)")
        print("2. [🧜‍♀️] MERMAID OS (Edu/Kids)")
        
        choice = input("SELECT BOOT OPTION > ").strip()
        
        mode = "MERMAID"
        user = "OLIWCIA"
        safe_mode = True
        
        if choice == "1":
            mode = "DIABLO"
            user = "ADMIN"
            safe_mode = False
            print("/// 🔓 MOUNTING DIABLO KERNEL... ///")
        else:
            print("/// ✨ SCATTERING PIXIE DUST... ✨ ///")

        history = ""
        
        while True:
            try:
                user_in = input(f"\n{user}@SYSTEM:~$ ")
                if not user_in: continue
                if user_in.lower() in ['exit', 'kill']:
                    print("> Saving State..."); self.mem.save(); break
                
                # 1. Memory & Context
                context = self.mem.recall(user_in)
                history += f"User: {user_in}\n"
                
                # 2. AI Thinking
                resp = self.brain.think(self.get_prompt(mode), history, str(context))
                history += f"AI: {resp}\n"
                
                # 3. Tool Execution (Only in Diablo Mode)
                if not safe_mode and ">> ACTION:" in resp:
                    for line in resp.split('\n'):
                        if ">> ACTION:" in line:
                            parts = line.split("::")
                            if len(parts) < 2: continue
                            
                            tool = parts[0].replace(">> ACTION:", "").strip()
                            arg = parts[1].strip()
                            
                            print(f"⚠️  [EXECUTE]: {tool} -> {arg}")
                            if input("    CONFIRM (y/n): ") == 'y':
                                out = ""
                                if tool == "terminal": out = self.tools.execute(arg)
                                if tool == "read": out = self.tools.read_file(arg)
                                
                                print(f"    [RESULT]: {out[:100]}...")
                                history += f"System Output: {out}\n"

            except KeyboardInterrupt:
                print("\n> Force Shutdown.")
                break

if __name__ == "__main__":
    SystemLauncher().main_loop()
'''

# ==========================================
# ENGINE START: BUILDING STRUCTURE
# ==========================================

def deploy_system():
    # 1. Struktura katalogów
    dirs = [
        BASE_DIR,
        BASE_DIR / "core",
        BASE_DIR / "mai_data"
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"   [DIR]  {d.name}/ Created")

    # 2. Zapisywanie plików
    files_map = {
        BASE_DIR / "core/__init__.py": "",
        BASE_DIR / "core/memory.py": CODE_MEMORY,
        BASE_DIR / "core/tools.py": CODE_TOOLS,
        BASE_DIR / "core/neural_engine.py": CODE_ENGINE,
        BASE_DIR / "main.py": CODE_MAIN,
    }

    for path, content in files_map.items():
        path.write_text(content.strip(), encoding='utf-8')
        print(f"   [FILE] {path.name} Written")

    # 3. Pamięć startowa (Seed)
    seed_memory = [
        {"ts": "2026-01-01", "content": "SYSTEM: Oliwcia lubi dinozaury i kolor różowy.", "tags": ["profil"]},
        {"ts": "2026-01-01", "content": "SYSTEM: Kot domowy nazywa się Burek.", "tags": ["profil"]},
        {"ts": "2026-01-01", "content": "SYSTEM: Hasło do tajnej bazy to 'Czekolada'.", "tags": ["secret"]}
    ]
    
    mem_path = BASE_DIR / "mai_data/LONG_TERM.json"
    if not mem_path.exists():
        mem_path.write_text(json.dumps(seed_memory, indent=2), encoding='utf-8')
        print("   [DATA] Seed Memory Injected (Oliwcia Profile)")

    print(f"\n✅ DEPLOYMENT COMPLETE!")
    print(f"---------------------------------------------------")
    print(f"1. Open Terminal: cd {PROJECT_NAME}")
    print(f"2. Install Deps:  pip install requests")
    print(f"3. Run System:    python main.py")
    print(f"---------------------------------------------------")

if __name__ == "__main__":
    deploy_system()