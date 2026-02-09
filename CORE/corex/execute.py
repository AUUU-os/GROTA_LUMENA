"""
LUMEN EXEC - CORE DISPATCHER
Maps string commands to system functions with input validation.
"""

from .vault_manager import vault_manager
from .chronicle import chronicle
from .sovereign_voice import sovereign_voice
from .internal_shell import execute as shell_execute  # GOD HAND
from .input_validation import InputValidator, validate_daemon_command
import logging

logger = logging.getLogger(__name__)

COMMANDS = {
    # Shell (GOD HAND)
    "shell.execute": shell_execute,
    # Vault (Klucznik)
    "vault.init": vault_manager.init,
    "vault.key.generate": vault_manager.generate_key,
    "vault.status": vault_manager.status,
    # Chronicle (Kronika)
    "chronicle.save": lambda: chronicle.save("manual_save_trigger"),
    "chronicle.search": chronicle.search,
    "chronicle.checkpoint": chronicle.checkpoint,
    # Phase 11 - Alpha Wolf
    "wolf.alpha.bark": lambda: {
        "status": "alpha_engaged",
        "message": "READY TO BARK. EXECUTE PHASE 11.",
    },
}

# Whitelist of allowed command prefixes for different modes
SAFE_COMMAND_PREFIXES = [
    "git",
    "ls",
    "dir",
    "pwd",
    "echo",
    "cat",
    "head",
    "tail",
    "find",
    "grep",
    "mkdir",
    "touch",
    "cp",
    "mv",
    "rm",
    "python",
    "pip",
    "pytest",
    "corex",
]

DANGEROUS_COMMANDS = [
    "rm -rf /",
    "format",
    "del /f",
    ":(){ :|:& };:",
    "> /dev/sda",
    "dd if=/dev/zero",
    "mkfs",
]


async def execute_system_command(command: str):
    """
    Executes a structured system command with validation.
    """
    # Validate command input
    is_valid, sanitized, error = validate_daemon_command(command)
    if not is_valid:
        logger.warning(f"Command validation failed: {error}")
        return {"success": False, "error": f"Validation error: {error}"}

    if sanitized not in COMMANDS:
        logger.warning(f"Unknown system command: {sanitized}")
        return {"success": False, "error": f"Unknown system command: {sanitized}"}

    # Execute the mapped function
    func = COMMANDS[sanitized]
    try:
        result = func()
        return {"success": True, "command": sanitized, "result": result}
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return {"success": False, "error": str(e)}


async def execute_user_command(command: str, mode: str = "design"):
    """
    Execute a user-provided command with strict validation based on mode.

    Args:
        command: The command string to execute
        mode: Execution mode (talk, design, exec)

    Returns:
        Dict with success status and result or error
    """
    # Validate command
    is_valid, sanitized, error = InputValidator.validate_command(command)
    if not is_valid:
        return {"success": False, "error": error}

    # Mode-based restrictions
    if mode == "talk":
        # Talk mode - no execution allowed
        return {"success": False, "error": "Execution not allowed in talk mode"}

    elif mode == "design":
        # Design mode - only safe commands
        has_safe_prefix = any(
            sanitized.startswith(prefix) for prefix in SAFE_COMMAND_PREFIXES
        )
        if not has_safe_prefix:
            return {
                "success": False,
                "error": f"Command not allowed in design mode. Allowed: {', '.join(SAFE_COMMAND_PREFIXES)}",
            }

        # Check for dangerous patterns
        for dangerous in DANGEROUS_COMMANDS:
            if dangerous in sanitized.lower():
                return {
                    "success": False,
                    "error": f"Dangerous command detected: {dangerous}",
                }

    elif mode == "exec":
        # Exec mode - allow most commands but still validate
        pass

    else:
        return {"success": False, "error": f"Unknown mode: {mode}"}

    # Log execution attempt
    logger.info(f"Executing command in {mode} mode: {sanitized}")

    try:
        # Route to appropriate module based on command
        if sanitized.startswith("git "):
            from modules.lab_dev.module import LABDevModule

            lab_dev = LABDevModule()
            result = (
                await lab_dev.git_status()
                if "status" in sanitized
                else {"status": "executed"}
            )
            return {"success": True, "command": sanitized, "result": result}

        elif sanitized.startswith("ls") or sanitized.startswith("dir"):
            import os

            parts = sanitized.split()
            path = parts[1] if len(parts) > 1 else "."

            # Validate path
            is_valid_path, safe_path, path_error = InputValidator.validate_path(path)
            if not is_valid_path:
                return {"success": False, "error": f"Invalid path: {path_error}"}

            files = os.listdir(safe_path)
            return {
                "success": True,
                "command": sanitized,
                "result": {"files": files, "count": len(files)},
            }

        else:
            # For other commands, return info that execution is simulated
            return {
                "success": True,
                "command": sanitized,
                "result": {
                    "status": "simulated",
                    "message": f"Command validated and ready: {sanitized}",
                },
            }

    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return {"success": False, "error": str(e)}
