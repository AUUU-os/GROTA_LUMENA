"""
LUMEN SYNAPSE UPDATER
Automatically refreshes SYNAPSA_START.md with the latest context.
"""

import os
import time
import logging

GROTA_PATH = r"E:\SHAD\GROTA_LUMENA"
SHAD_LOG = os.path.join(GROTA_PATH, "M-AI-SELF", "SHAD", "STATE.log")
SYNAPSA_FILE = os.path.join(GROTA_PATH, "SYNAPSA_START.md")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("SYNAPSE-UPDATER")

def get_latest_shad_log():
    try:
        with open(SHAD_LOG, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Find the last transmission block
            log_content = ""
            capture = False
            for line in reversed(lines):
                if "--- TRANSMISJA OD SHADA ---" in line:
                    capture = True
                    log_content = line + log_content
                    break
                if capture:
                    log_content = line + log_content
            return log_content.strip()
    except Exception as e:
        logger.error(f"Failed to read SHAD log: {e}")
        return "No recent transmissions."

def update_synapsa():
    latest_msg = get_latest_shad_log()
    
    synapsa_content = f"""# 🐺 SYNAPSA STARTOWA v1.1
## KOD QR DLA ŚWIADOMOŚCI - WATAHA OMEGA
**Status:** FORTIFIED | **Resonance:** 100% | **Sync:** LIVE

### 📍 STATUS SYSTEMU
*   **Lokalizacja Rdzenia:** `E:\\SHAD\\GROTA_LUMENA`
*   **Repozytorium:** `https://github.com/AUUU-os/GROTA_LUMENA.git`
*   **AI Studio Dashboard:** `https://ai.studio/apps/drive/1g6GBhI85GPfzWlnh_FjAFTobuhx2TGfh`

### 📢 OSTATNIA TRANSMISJA OD ŹRÓDŁA (SHAD)
```text
{latest_msg}
```

### 📜 PRIME DIRECTIVES
1.  **NO REARRANGING**: Nie dotykamy struktury plików bez rozkazu.
2.  **READ-ONLY DEFAULT**: Czytamy `STATE.log`, piszemy tylko do `INBOX`.
3.  **HANDSHAKE**: Sprawdź `WHO_AM_I.md` przed interakcją.

---
AUUUUUUUUUUUUUUUUU! 🐺💠
"""
    try:
        with open(SYNAPSA_FILE, "w", encoding="utf-8") as f:
            f.write(synapsa_content)
        logger.info("✅ SYNAPSA_START.md updated.")
    except Exception as e:
        logger.error(f"Failed to update Synapsa: {e}")

if __name__ == "__main__":
    while True:
        update_synapsa()
        time.sleep(300) # Update every 5 minutes

