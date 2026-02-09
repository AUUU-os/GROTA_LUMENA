"""
Secure Vault
Encrypted storage for API keys and secrets
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional
from cryptography.fernet import Fernet
import logging

import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecretVault:
    """
    Encrypted storage for secrets (Asynchronous wrapper)
    """

    def __init__(self, vault_dir: str = "data/vault"):
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)

        self.key_file = self.vault_dir / ".vault_key"
        self.data_file = self.vault_dir / "secrets.enc"
        self.cipher = None

    async def initialize(self):
        """Explicitly initialize the cipher asynchronously."""
        key = await asyncio.to_thread(self._load_or_create_key_sync)
        self.cipher = Fernet(key)

    def _load_or_create_key_sync(self) -> bytes:
        """Internal synchronous key management."""
        if self.key_file.exists():
            return self.key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            try:
                os.chmod(self.key_file, 0o600)
            except OSError:
                pass
            return key

    async def _load_data(self) -> Dict[str, str]:
        """Load and decrypt vault data asynchronously."""
        if not self.data_file.exists():
            return {}

        encrypted_data = await asyncio.to_thread(self.data_file.read_bytes)
        if not encrypted_data:
            return {}

        decrypted_data = await asyncio.to_thread(self.cipher.decrypt, encrypted_data)
        return json.loads(decrypted_data.decode("utf-8"))

    async def _save_data(self, data: Dict[str, str]) -> None:
        """Encrypt and save vault data asynchronously."""
        json_data = json.dumps(data).encode("utf-8")
        encrypted_data = await asyncio.to_thread(self.cipher.encrypt, json_data)
        await asyncio.to_thread(self.data_file.write_bytes, encrypted_data)

    async def set(self, key: str, value: str) -> None:
        """Store a secret asynchronously."""
        data = await self._load_data()
        data[key] = value
        await self._save_data(data)
        logger.info(f"Stored secret: {key}")

    async def get_auth_header(self, key: str) -> Optional[str]:
        """Retrieve a secret and format it as a Bearer token for headers."""
        val = await self.get(key)
        if val and not val.startswith("Bearer "):
            return f"Bearer {val}"
        return val

    async def delete(self, key: str) -> bool:
        """
        Delete a secret

        Args:
            key: Secret name

        Returns:
            True if deleted, False if not found
        """
        data = await self._load_data()
        if key in data:
            del data[key]
            await self._save_data(data)
            logger.info(f"Deleted secret: {key}")
            return True
        return False

    async def list_keys(self) -> list[str]:
        """List all secret keys (not values!)"""
        data = await self._load_data()
        return list(data.keys())

    async def clear(self) -> None:
        """Clear all secrets (dangerous!)"""
        logger.warning("Clearing all secrets from vault")
        await self._save_data({})

    async def export_for_container(self) -> Dict[str, str]:
        """
        Export secrets as environment variables for container

        Returns:
            Dictionary of ENV_VAR: value
        """
        return await self._load_data()


# Example usage
if __name__ == "__main__":
    print("🔐 Secure Vault Tests\n")

    vault = SecretVault(vault_dir="data/vault")

    # Test 1: Store secrets
    print("Test 1: Store secrets")
    vault.set("GITHUB_TOKEN", "ghp_test_token_12345")
    vault.set("OPENAI_API_KEY", "sk-test-key-67890")
    print("  Stored 2 secrets\n")

    # Test 2: Retrieve secrets
    print("Test 2: Retrieve secrets")
    github_token = vault.get("GITHUB_TOKEN")
    print(f"  GITHUB_TOKEN: {github_token[:15]}... (truncated)\n")

    # Test 3: List keys
    print("Test 3: List keys")
    keys = vault.list_keys()
    print(f"  Keys: {keys}\n")

    # Test 4: Export for container
    print("Test 4: Export for container")
    env_vars = vault.export_for_container()
    print(f"  ENV vars: {list(env_vars.keys())}\n")

    # Test 5: Delete secret
    print("Test 5: Delete secret")
    deleted = vault.delete("OPENAI_API_KEY")
    print(f"  Deleted: {deleted}")
    print(f"  Remaining keys: {vault.list_keys()}")
