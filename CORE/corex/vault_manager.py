"""
LUMEN VAULT MANAGER (Wrapper)
Aligns existing SecretVault with the new technical manifest.
"""

from .vault import SecretVault
import secrets
from datetime import datetime


class VaultManager:
    def __init__(self, vault_dir="data/vault"):
        self.vault = SecretVault(vault_dir=vault_dir)

    async def init(self):
        # Asynchronously initialize the vault (key & cipher)
        await self.vault.initialize()
        return {
            "status": "vault_initialized",
            "key_present": self.vault.key_file.exists(),
            "created_at": datetime.fromtimestamp(
                self.vault.key_file.stat().st_ctime
            ).isoformat()
            if self.vault.key_file.exists()
            else None,
        }

    async def generate_key(self):
        # In our SecretVault, keys are managed via set/get
        # This will generate a new random token for the user to use as a secondary key/token
        new_token = secrets.token_hex(32)
        # Store it in the vault for persistence
        token_id = f"TOKEN_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        await self.vault.set(token_id, new_token)
        return {
            "status": "key_generated",
            "token_id": token_id,
            "token_preview": f"{new_token[:8]}...",
        }

    async def status(self):
        keys = await self.vault.list_keys()
        return {
            "initialized": self.vault.key_file.exists(),
            "keys_count": len(keys),
            "vault_dir": str(self.vault.vault_dir),
        }


# Singleton
vault_manager = VaultManager()
