"""
Module Router
Routes intents to appropriate LAB modules
"""

import asyncio
from typing import Dict, Any, Optional
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModuleStatus(Enum):
    """LAB module status"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


class ModuleRouter:
    """
    Routes intents to appropriate LAB modules

    Responsibilities:
    - Module lifecycle (start, stop, restart)
    - Load balancing (if multiple instances)
    - Health checking
    - Dependency management

    Example:
        router = ModuleRouter()
        await router.attach_module("lab_dev", LABDevModule())
        result = await router.route("lab_dev", "git_status", {})
    """

    def __init__(self):
        self.modules: Dict[str, Any] = {}  # module_name -> module_instance
        self.status: Dict[str, ModuleStatus] = {}  # module_name -> status
        self.health: Dict[str, bool] = {}  # module_name -> is_healthy

    async def attach_module(self, name: str, module: Any) -> None:
        """
        Attach a LAB module to the router

        Args:
            name: Module name (e.g., "lab_dev")
            module: Module instance
        """
        logger.info(f"Attaching module: {name}")
        self.modules[name] = module
        self.status[name] = ModuleStatus.STOPPED

        # Initialize module
        try:
            await self._start_module(name)
        except Exception as e:
            logger.error(f"Failed to start module {name}: {e}")
            self.status[name] = ModuleStatus.ERROR

    async def detach_module(self, name: str) -> None:
        """
        Detach a LAB module from the router

        Args:
            name: Module name
        """
        if name not in self.modules:
            raise ValueError(f"Module {name} not found")

        logger.info(f"Detaching module: {name}")

        # Stop module first
        await self._stop_module(name)

        # Remove from router
        del self.modules[name]
        del self.status[name]
        if name in self.health:
            del self.health[name]

    async def route(
        self,
        module_name: str,
        operation: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route an operation to a module

        Args:
            module_name: Target module name
            operation: Operation to perform
            params: Operation parameters

        Returns:
            Result dictionary from module

        Raises:
            ValueError: If module not found or not healthy
            RuntimeError: If operation fails
        """
        # Check module exists
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found. Available: {list(self.modules.keys())}")

        # Check module is running
        if self.status[module_name] != ModuleStatus.RUNNING:
            raise ValueError(f"Module {module_name} not running (status: {self.status[module_name].value})")

        # Check module health
        if not self.health.get(module_name, False):
            logger.warning(f"Module {module_name} may be unhealthy, attempting operation anyway")

        # Route to module
        module = self.modules[module_name]
        logger.info(f"Routing {operation} to {module_name} with params: {params}")

        try:
            result = await module.execute(operation, params)
            return result
        except Exception as e:
            logger.error(f"Operation {operation} failed on {module_name}: {e}")
            raise RuntimeError(f"Module execution failed: {e}")

    async def _start_module(self, name: str) -> None:
        """Start a module"""
        module = self.modules[name]
        self.status[name] = ModuleStatus.STARTING

        try:
            if hasattr(module, 'start'):
                await module.start()

            self.status[name] = ModuleStatus.RUNNING
            self.health[name] = True
            logger.info(f"Module {name} started successfully")

        except Exception as e:
            self.status[name] = ModuleStatus.ERROR
            self.health[name] = False
            raise

    async def _stop_module(self, name: str) -> None:
        """Stop a module"""
        module = self.modules[name]

        try:
            if hasattr(module, 'stop'):
                await module.stop()

            self.status[name] = ModuleStatus.STOPPED
            self.health[name] = False
            logger.info(f"Module {name} stopped")

        except Exception as e:
            logger.error(f"Error stopping module {name}: {e}")

    async def restart_module(self, name: str) -> None:
        """Restart a module"""
        logger.info(f"Restarting module: {name}")
        await self._stop_module(name)
        await self._start_module(name)

    async def health_check(self, name: str) -> bool:
        """
        Check if a module is healthy

        Args:
            name: Module name

        Returns:
            True if healthy, False otherwise
        """
        if name not in self.modules:
            return False

        module = self.modules[name]

        try:
            # If module has health_check method, use it
            if hasattr(module, 'health_check'):
                is_healthy = await module.health_check()
                self.health[name] = is_healthy
                return is_healthy

            # Otherwise, assume healthy if running
            return self.status[name] == ModuleStatus.RUNNING

        except Exception as e:
            logger.error(f"Health check failed for {name}: {e}")
            self.health[name] = False
            return False

    async def health_check_all(self) -> Dict[str, bool]:
        """Health check all modules"""
        results = {}
        for name in self.modules.keys():
            results[name] = await self.health_check(name)
        return results

    def get_status(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get module status

        Args:
            name: Module name (or None for all modules)

        Returns:
            Status dictionary
        """
        if name:
            return {
                "module": name,
                "status": self.status.get(name, ModuleStatus.STOPPED).value,
                "healthy": self.health.get(name, False)
            }

        # Return all modules
        return {
            "modules": [
                {
                    "name": name,
                    "status": status.value,
                    "healthy": self.health.get(name, False)
                }
                for name, status in self.status.items()
            ],
            "total": len(self.modules)
        }

    def list_modules(self) -> list[str]:
        """List all attached modules"""
        return list(self.modules.keys())


# Example usage and tests
if __name__ == "__main__":
    # Mock module for testing
    class MockModule:
        async def start(self):
            print("MockModule starting...")
            await asyncio.sleep(0.1)

        async def stop(self):
            print("MockModule stopping...")

        async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
            print(f"MockModule executing: {operation} with {params}")
            return {"success": True, "operation": operation, "params": params}

        async def health_check(self) -> bool:
            return True

    async def main():
        print("🔀 Module Router Tests\n")

        router = ModuleRouter()

        # Test 1: Attach module
        print("Test 1: Attach module")
        mock_module = MockModule()
        await router.attach_module("mock_lab", mock_module)
        print(f"  Status: {router.get_status('mock_lab')}\n")

        # Test 2: Route operation
        print("Test 2: Route operation")
        result = await router.route("mock_lab", "test_operation", {"param1": "value1"})
        print(f"  Result: {result}\n")

        # Test 3: Health check
        print("Test 3: Health check")
        health = await router.health_check("mock_lab")
        print(f"  Healthy: {health}\n")

        # Test 4: List modules
        print("Test 4: List modules")
        modules = router.list_modules()
        print(f"  Modules: {modules}\n")

        # Test 5: Detach module
        print("Test 5: Detach module")
        await router.detach_module("mock_lab")
        print(f"  Modules after detach: {router.list_modules()}")

    asyncio.run(main())
