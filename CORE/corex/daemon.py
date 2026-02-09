"""
CORE_X_AGENT Daemon
Main orchestration process
"""

import asyncio
import logging
import signal
from typing import Dict, Any, Optional
from datetime import datetime

from .interpreter import CommandInterpreter
from .policy import PolicyEngine, PolicyDecision, WindowMode, PolicyContext
from .router import ModuleRouter
from .audit import AuditLogger
from .vault import SecretVault
from .error_formatter import ErrorFormatter
from .metrics import metrics_engine
from modules.sentinel import SentinelModule
from modules.architect import ArchitectModule
from modules.knowledge import KnowledgeModule
from modules.optimizer import OptimizerModule
import time

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CoreXDaemon:
    """
    CORE_X_AGENT main daemon process

    Orchestrates all components:
    - Command Interpreter (AI language â†’ intents)
    - Policy Engine (security decisions)
    - Module Router (route to LAB_*)
    - Audit Logger (tamper-proof logging)
    - Secret Vault (encrypted secrets)

    Flow:
    1. AI sends command: "commit my changes"
    2. Interpreter parses â†’ Intent(module="lab_dev", operation="git_commit")
    3. Policy Engine checks â†’ ALLOW/DENY
    4. Router executes â†’ LAB_DEV module
    5. Audit Logger records â†’ JSONL log
    6. Return result to AI

    Example:
        daemon = CoreXDaemon(mode=WindowMode.DESIGN)
        await daemon.start()
        result = await daemon.execute_command("commit my code")
    """

    def __init__(
        self,
        mode: WindowMode = WindowMode.DESIGN,
        data_dir: str = "data",
        working_dir: Optional[str] = None,
    ):
        self.mode = mode
        self.data_dir = data_dir
        self.working_dir = working_dir
        self.is_running = False

        # Core components
        self.interpreter = CommandInterpreter()
        self.policy = PolicyEngine(mode=mode)
        self.router = ModuleRouter()
        self.audit = AuditLogger(data_dir=f"{data_dir}/audit")
        self.vault = SecretVault(vault_dir=f"{data_dir}/vault")
        self.error_formatter = ErrorFormatter()

        # Statistics
        self.stats = {
            "commands_total": 0,
            "commands_allowed": 0,
            "commands_denied": 0,
            "commands_failed": 0,
            "started_at": None,
        }

        # Setup signal handlers
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup graceful shutdown on SIGINT/SIGTERM"""

        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def _init_modules(self) -> None:
        """Initialize and attach core modules to the router."""
        modules = {
            "sentinel": SentinelModule(),
            "architect": ArchitectModule(working_dir=self.working_dir or "."),
            "knowledge": KnowledgeModule(),
            "optimizer": OptimizerModule(),
        }
        for name, module in modules.items():
            try:
                await self.router.attach_module(name, module)
                logger.info(f"  Module registered: {name}")
            except Exception as e:
                logger.error(f"  Failed to register module {name}: {e}")

    async def start(self) -> None:
        """Start the daemon"""
        logger.info("đźşđź’  CORE_X_AGENT starting...")

        # Async initialization
        await self.vault.initialize()

        # Register core modules
        await self._init_modules()

        logger.info(f"  Mode: {self.mode.value}")
        logger.info(f"  Data dir: {self.data_dir}")
        logger.info(f"  Working dir: {self.working_dir or 'current'}")

        self.stats["started_at"] = datetime.now().isoformat()
        self.is_running = True

        logger.info("âś… CORE_X_AGENT started successfully")

    async def stop(self) -> None:
        """Stop the daemon"""
        logger.info("Stopping CORE_X_AGENT...")

        # Stop all modules
        for module_name in self.router.list_modules():
            try:
                await self.router.detach_module(module_name)
            except Exception as e:
                logger.error(f"Error stopping module {module_name}: {e}")

        self.is_running = False
        logger.info("âś… CORE_X_AGENT stopped")

    async def execute_command(
        self, command: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a command from AI
        """
        start_time = time.perf_counter()
        self.stats["commands_total"] += 1
        logger.info(f"đź“Ą Command: '{command}'")

        response = {
            "success": False,
            "command": command,
            "timestamp": datetime.now().isoformat(),
        }

        intent = None
        try:
            # Step 1: Interpret command
            intent = self.interpreter.parse(command)
            # ... (rest of the logic)
            response["intent"] = {
                "module": intent.module,
                "operation": intent.operation,
                "params": intent.params,
                "confidence": intent.confidence,
            }
            logger.info(
                f"  Intent: {intent.module}.{intent.operation} (confidence: {intent.confidence})"
            )

            # Step 2: Policy check
            policy_context = PolicyContext(
                mode=self.mode,
                operation=intent.operation,
                module=intent.module,
                params=intent.params,
                archetype=context.get("archetype") if context else None,
                urgency=context.get("urgency", "NORMAL") if context else "NORMAL",
            )

            decision, reason = self.policy.evaluate(
                operation=intent.operation,
                module=intent.module,
                params=intent.params,
                context=policy_context,
            )

            response["policy_decision"] = decision.value
            response["policy_reason"] = reason
            logger.info(f"  Policy: {decision.value} - {reason}")

            # Step 3: Execute if allowed
            if decision == PolicyDecision.ALLOW:
                self.stats["commands_allowed"] += 1

                # Route to module
                try:
                    result = await self.router.route(
                        module_name=intent.module,
                        operation=intent.operation,
                        params=intent.params,
                    )

                    response["success"] = result.get("success", False)
                    response["result"] = result
                    logger.info(f"  Result: {result}")

                except Exception as e:
                    self.stats["commands_failed"] += 1
                    response["success"] = False
                    logger.error(f"  Execution failed: {e}")

                    # Check if it's a git error and format appropriately
                    error_str = str(e)
                    if "git" in intent.operation.lower() or "git" in error_str.lower():
                        enhanced_error = self.error_formatter.format_git_error(
                            error_message=error_str, operation=intent.operation
                        )
                        response["error"] = enhanced_error.to_dict()
                    else:
                        enhanced_error = self.error_formatter.format_system_error(
                            error=e, context=f"Executing {intent.operation}"
                        )
                        response["error"] = enhanced_error.to_dict()

                    # Log to audit
                    await self.audit.log(
                        action=intent.operation,
                        intent=response["intent"],
                        policy_decision=decision.value,
                        error=str(e),
                        metadata=context,
                    )

                    return response

            else:
                # Denied or needs user confirmation
                self.stats["commands_denied"] += 1
                response["success"] = False

                # Generate enhanced error message
                enhanced_error = self.error_formatter.format_policy_denial(
                    operation=intent.operation,
                    mode=self.mode.value,
                    reason=reason,
                    module=intent.module,
                )
                response["error"] = enhanced_error.to_dict()

            # Step 4: Audit log
            await self.audit.log(
                action=intent.operation,
                intent=response["intent"],
                policy_decision=decision.value,
                result=response.get("result"),
                metadata=context,
            )

            # đź§¬ OMEGA FEEDBACK LOOP
            asyncio.create_task(self._adaptive_learning_feedback(command, response))

            return response

        except ValueError as e:
            # Command interpretation failed
            logger.error(f"  Interpretation failed: {e}")

            # Get suggestions from interpreter
            suggestions = self.interpreter.suggest_corrections(command)

            # Generate enhanced error message
            enhanced_error = self.error_formatter.format_command_unknown(
                command=command, similar_commands=suggestions
            )
            response["error"] = enhanced_error.to_dict()

            return response

        except Exception as e:
            # Unexpected error
            logger.error(f"  Unexpected error: {e}", exc_info=True)
            self.stats["commands_failed"] += 1

            # Generate enhanced error message
            enhanced_error = self.error_formatter.format_system_error(
                error=e, context="Command execution"
            )
            response["error"] = enhanced_error.to_dict()
            return response

        finally:
            # Step 5: Log metrics
            latency_ms = (time.perf_counter() - start_time) * 1000
            module = intent.module if intent else "unknown"
            operation = intent.operation if intent else "unknown"
            metrics_engine.log_command(
                module=module,
                operation=operation,
                latency_ms=latency_ms,
                success=response["success"],
            )

    async def get_status(self) -> Dict[str, Any]:
        """Get daemon status"""
        keys = await self.vault.list_keys()
        return {
            "running": self.is_running,
            "mode": self.mode.value,
            "modules": self.router.get_status(),
            "stats": self.stats,
            "vault_keys": len(keys),
        }

    def set_mode(self, mode: WindowMode) -> None:
        """Change window mode"""
        logger.info(f"Mode changed: {self.mode.value} â†’ {mode.value}")
        self.mode = mode
        self.policy.set_mode(mode)

    async def _adaptive_learning_feedback(self, command: str, response: Dict[str, Any]):
        """
        đź§¬ ADAPTIVE LEARNING: Stores execution feedback in the memory engine.
        Allows the system to remember what worked and what failed.
        """
        status = "SUCCESS" if response.get("success") else "FAILURE"
        _content = f"Command: '{command}' | Status: {status} | Intent: {response.get('intent', {}).get('operation')}"  # noqa: F841

        try:
            await metrics_engine.log_command(
                module="core", operation="adaptive_learning", latency_ms=0, success=True
            )
            # Store feedback in memory engine (lazy import to avoid circular deps)
            try:
                from .memory_engine import memory_engine
                await memory_engine.store_memory(
                    content=_content,
                    memory_type="execution_feedback",
                    importance=4,
                    metadata={"source": "daemon", "status": status},
                )
            except Exception as mem_err:
                logger.error(f"Memory Engine Error: {mem_err}")            logger.info(f"đź§¬ Feedback Loop: Insight indexed for '{command[:20]}...'")
        except Exception as e:
            logger.error(f"âťŚ Feedback Loop Error: {e}")


# Example usage
if __name__ == "__main__":
    from modules.lab_dev.module import LABDevModule

    async def main():
        print("đźşđź’  CORE_X_AGENT Daemon Test\n")

        # Create daemon
        daemon = CoreXDaemon(mode=WindowMode.DESIGN, data_dir="data", working_dir=".")

        # Start daemon
        await daemon.start()
        print()

        # Attach LAB_DEV module
        print("Attaching LAB_DEV module...")
        lab_dev = LABDevModule(working_dir=".")
        await daemon.router.attach_module("lab_dev", lab_dev)
        print()

        # Test commands
        test_commands = [
            "show git status",
            "show me the last 3 commits",
            # "commit my changes with message 'test commit'",  # Requires user confirmation in DESIGN mode
        ]

        for cmd in test_commands:
            print(f"Command: '{cmd}'")
            result = await daemon.execute_command(cmd)
            print(f"  Success: {result['success']}")
            if result.get("result"):
                print(f"  Data: {result['result'].get('data')}")
            if result.get("error"):
                print(f"  Error: {result['error']}")
            print()

        # Get status
        print("Daemon Status:")
        status = daemon.get_status()
        print(f"  Running: {status['running']}")
        print(f"  Mode: {status['mode']}")
        print(f"  Commands: {status['stats']['commands_total']}")
        print(f"  Allowed: {status['stats']['commands_allowed']}")
        print(f"  Denied: {status['stats']['commands_denied']}")
        print()

        # View audit log
        print("Recent Audit Log:")
        recent = daemon.audit.get_recent(limit=5)
        for entry in recent:
            print(
                f"  [{entry['timestamp']}] {entry['action']}: {entry['policy_decision']}"
            )
        print()

        # Stop daemon
        await daemon.stop()

    asyncio.run(main())

