import sys
from pathlib import Path
from core.neural_engine import LocalBrain
from core.memory import NeuralMemory
from core.tools import Cybernetics

# --- CONFIG ---
MODEL_NAME = "dolphin-llama3" # Upewnij się, że masz ten model w Ollama
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