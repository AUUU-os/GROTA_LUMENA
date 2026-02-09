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