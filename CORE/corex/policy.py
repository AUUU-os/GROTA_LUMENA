"""
Policy Engine
Security layer - decides whether to allow/deny actions
"""

import re
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, time as dt_time


class PolicyDecision(Enum):
    """Policy decision outcomes"""
    ALLOW = "allowed"
    DENY = "denied"
    ASK_USER = "ask_user"  # Require user confirmation


class WindowMode(Enum):
    """Window operation modes"""
    TALK = "talk"  # Pure conversation, no execution
    DESIGN = "design"  # Controlled execution (safe operations only)
    EXEC = "exec"  # Full execution (danger zone!)


@dataclass
class PolicyContext:
    """Context for policy decision"""
    mode: WindowMode
    operation: str
    module: str
    params: Dict[str, Any]
    archetype: Optional[str] = None  # For ARKALOS integration
    urgency: str = "NORMAL"  # LOW | NORMAL | HIGH
    timestamp: Optional[datetime] = None


@dataclass
class PolicyRule:
    """Single policy rule"""
    name: str
    condition: callable  # Function that returns True if rule applies
    decision: PolicyDecision
    reason: str
    priority: int = 0  # Higher priority = checked first


class PolicyEngine:
    """
    Security policy engine with default-deny model

    Three-tier security:
    1. Mode-based restrictions (TALK < DESIGN < EXEC)
    2. Whitelist/blacklist patterns
    3. Context-based rules (time, urgency, etc.)

    Example:
        engine = PolicyEngine(mode=WindowMode.DESIGN)
        decision = engine.evaluate(operation="git_commit", module="lab_dev")
        # Returns PolicyDecision.ALLOW or DENY with reason
    """

    def __init__(self, mode: WindowMode = WindowMode.DESIGN):
        self.mode = mode
        self.whitelist: List[str] = []  # Explicitly allowed operations
        self.blacklist: List[str] = []  # Explicitly denied operations
        self.rules: List[PolicyRule] = []
        self._build_default_rules()
        self._add_default_whitelist()

    def _build_default_rules(self):
        """Build default security rules"""

        # Blacklist: Destructive operations (HIGHEST PRIORITY)
        destructive_ops = [
            "file_delete", "file_delete_all",
            "git_reset_hard", "git_force_push",
            "system_shutdown", "rm_rf"
        ]
        self.rules.append(PolicyRule(
            name="blacklist_destructive",
            condition=lambda ctx: any(
                op in ctx.operation for op in destructive_ops
            ),
            decision=PolicyDecision.DENY,
            reason="Destructive operation not allowed",
            priority=100  # Highest - overrides everything
        ))

        # TALK mode: NO execution allowed
        self.rules.append(PolicyRule(
            name="talk_mode_deny_all",
            condition=lambda ctx: ctx.mode == WindowMode.TALK,
            decision=PolicyDecision.DENY,
            reason="No execution allowed in TALK mode",
            priority=95
        ))

        # DESIGN mode: Safe operations only
        safe_operations = [
            # Git safe operations
            "git_status", "git_diff", "git_log",
            # LAB_FILES safe operations (read-only)
            "file_read", "file_list", "file_info",
            # LAB_NET safe operations (read-only)
            "http_get", "http_head"
        ]
        self.rules.append(PolicyRule(
            name="design_mode_safe_only",
            condition=lambda ctx: (
                ctx.mode == WindowMode.DESIGN and
                ctx.operation not in safe_operations
            ),
            decision=PolicyDecision.ASK_USER,
            reason=f"Operation requires user confirmation in DESIGN mode",
            priority=90
        ))

        # EXEC mode: Allow all (unless blacklisted)
        self.rules.append(PolicyRule(
            name="exec_mode_allow_all",
            condition=lambda ctx: ctx.mode == WindowMode.EXEC,
            decision=PolicyDecision.ALLOW,
            reason="EXEC mode allows all operations",
            priority=80  # Lowest - fallback for EXEC mode
        ))

        # Business hours check (optional - commented out by default)
        # self.rules.append(PolicyRule(
        #     name="business_hours_only",
        #     condition=lambda ctx: not self._is_business_hours(),
        #     decision=PolicyDecision.ASK_USER,
        #     reason="Operation outside business hours requires confirmation",
        #     priority=50
        # ))

    def _add_default_whitelist(self):
        """Add default safe operations to whitelist"""
        # Safe read-only git operations
        safe_git_ops = [
            "git_status",
            "git_diff",
            "git_log",
        ]
        for op in safe_git_ops:
            self.add_whitelist(op)
            
        # Safe read-only file operations
        safe_file_ops = [
            "file_read",
            "file_list",
            "file_info",
        ]
        for op in safe_file_ops:
            self.add_whitelist(op)
            
        # Safe read-only network operations
        safe_net_ops = [
            "http_get",
            "http_head",
        ]
        for op in safe_net_ops:
            self.add_whitelist(op)

    def evaluate(
        self,
        operation: str,
        module: str,
        params: Optional[Dict[str, Any]] = None,
        context: Optional[PolicyContext] = None
    ) -> tuple[PolicyDecision, str]:
        """
        Evaluate whether to allow/deny an operation

        Args:
            operation: Operation name (e.g., "git_commit")
            module: Module name (e.g., "lab_dev")
            params: Operation parameters
            context: Additional context

        Returns:
            Tuple of (decision, reason)
        """
        # Build context if not provided
        if context is None:
            context = PolicyContext(
                mode=self.mode,
                operation=operation,
                module=module,
                params=params or {},
                timestamp=datetime.now()
            )

        # Check whitelist first (always allow)
        if self._is_whitelisted(operation):
            return PolicyDecision.ALLOW, "Whitelisted operation"

        # Check blacklist (always deny)
        if self._is_blacklisted(operation):
            return PolicyDecision.DENY, "Blacklisted operation"

        # Evaluate rules (sorted by priority, highest first)
        sorted_rules = sorted(self.rules, key=lambda r: r.priority, reverse=True)
        for rule in sorted_rules:
            if rule.condition(context):
                return rule.decision, f"{rule.reason} (rule: {rule.name})"

        # Default: DENY (security by default)
        return PolicyDecision.DENY, "No matching allow rule (default deny)"

    def add_whitelist(self, pattern: str):
        """Add operation pattern to whitelist"""
        self.whitelist.append(pattern)

    def add_blacklist(self, pattern: str):
        """Add operation pattern to blacklist"""
        self.blacklist.append(pattern)

    def add_rule(self, rule: PolicyRule):
        """Add custom policy rule"""
        self.rules.append(rule)

    def _is_whitelisted(self, operation: str) -> bool:
        """Check if operation matches whitelist"""
        return any(
            re.match(pattern, operation) for pattern in self.whitelist
        )

    def _is_blacklisted(self, operation: str) -> bool:
        """Check if operation matches blacklist"""
        return any(
            re.match(pattern, operation) for pattern in self.blacklist
        )

    def _is_business_hours(self) -> bool:
        """Check if current time is business hours (9am-5pm)"""
        now = datetime.now().time()
        return dt_time(9, 0) <= now <= dt_time(17, 0)

    def set_mode(self, mode: WindowMode):
        """Change window mode"""
        self.mode = mode

    def get_stats(self) -> Dict[str, Any]:
        """Get policy engine statistics"""
        return {
            "mode": self.mode.value,
            "whitelist_count": len(self.whitelist),
            "blacklist_count": len(self.blacklist),
            "rules_count": len(self.rules)
        }


# Example usage and tests
if __name__ == "__main__":
    print("đź”’ Policy Engine Tests\n")

    # Test 1: TALK mode (no execution)
    print("Test 1: TALK mode")
    engine = PolicyEngine(mode=WindowMode.TALK)
    decision, reason = engine.evaluate("git_commit", "lab_dev")
    print(f"  git_commit: {decision.value} - {reason}\n")

    # Test 2: DESIGN mode (safe operations OK, dangerous need confirmation)
    print("Test 2: DESIGN mode")
    engine = PolicyEngine(mode=WindowMode.DESIGN)

    safe_ops = ["git_status", "git_diff", "file_read"]
    for op in safe_ops:
        decision, reason = engine.evaluate(op, "lab_dev")
        print(f"  {op}: {decision.value}")

    dangerous_ops = ["git_commit", "git_push", "file_write"]
    for op in dangerous_ops:
        decision, reason = engine.evaluate(op, "lab_dev")
        print(f"  {op}: {decision.value} - {reason}")

    print()

    # Test 3: EXEC mode with whitelist
    print("Test 3: EXEC mode with whitelist")
    engine = PolicyEngine(mode=WindowMode.EXEC)
    engine.add_whitelist(r"git_.*")  # Allow all git operations
    engine.add_blacklist(r".*force.*")  # Block anything with "force"

    test_ops = ["git_commit", "git_push", "git_force_push", "file_delete"]
    for op in test_ops:
        decision, reason = engine.evaluate(op, "lab_dev")
        print(f"  {op}: {decision.value}")

    print()

    # Test 4: Custom rule (archetype-based)
    print("Test 4: Custom rule (archetype-specific)")
    engine = PolicyEngine(mode=WindowMode.DESIGN)

    # Wolf archetype can commit urgently without confirmation
    engine.add_rule(PolicyRule(
        name="wolf_urgent_commit",
        condition=lambda ctx: (
            ctx.archetype == "Wolf" and
            ctx.operation == "git_commit" and
            ctx.urgency == "HIGH"
        ),
        decision=PolicyDecision.ALLOW,
        reason="Wolf archetype trusted for urgent commits",
        priority=80
    ))

    # Test with Wolf archetype
    ctx = PolicyContext(
        mode=WindowMode.DESIGN,
        operation="git_commit",
        module="lab_dev",
        params={},
        archetype="Wolf",
        urgency="HIGH"
    )
    decision, reason = engine.evaluate("git_commit", "lab_dev", context=ctx)
    print(f"  Wolf urgent commit: {decision.value} - {reason}")

    # Test without Wolf
    ctx.archetype = "Architect"
    decision, reason = engine.evaluate("git_commit", "lab_dev", context=ctx)
    print(f"  Architect commit: {decision.value} - {reason}")

