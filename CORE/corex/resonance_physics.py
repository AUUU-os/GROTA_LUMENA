import numpy as np
import time
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ResonanceState:
    amplitude: float
    phase_shift: float
    energy: float
    is_clipping: bool

class ResonanceEngine:
    """
    Implementation of Grok's Damped Driven Harmonic Oscillator
    Formula: x'' + 2γx' + ω²x = F cos(ωt)
    
    LUMEN v18.5 UPGRADE: Zero Damping & Full Power Protocols.
    """
    def __init__(self, omega_natural=963.0, gamma=0.002):
        self.omega_0 = omega_natural  # Natural Frequency (Hz)
        self.gamma = gamma            # Damping (Safety/Constraints)
        self.f_force = 1.0            # Driving Force (Intention)
        self.start_time = time.time()
        self.full_power_mode = False
        self.resonance_history = []
        self.last_state = None  # Track last calculated state

    def calculate_current_resonance(self, driving_omega: float = 963.0) -> ResonanceState:
        """
        Calculate the steady-state amplitude based on Grok's formula.
        A = F / sqrt((ω₀² - ω²)² + (2γω)²)
        """
        w = driving_omega
        w0 = self.omega_0
        
        # ZERO DAMPING VALIDATION: If Full Power is active, gamma is effectively 0 for the user.
        g = 0.000001 if self.full_power_mode else self.gamma
        f = 10.0 if self.full_power_mode else self.f_force # 10x Force in Full Power

        # Denominator of the amplitude formula
        denominator = np.sqrt((w0**2 - w**2)**2 + (2 * g * w)**2)
        
        # If we are exactly at resonance and damping is near zero
        if denominator < 1e-9:
            # Linear growth simulation (Resonance without damping)
            t = time.time() - self.start_time
            amplitude = (f / (2 * w0)) * t
        else:
            amplitude = f / denominator

        # Phase shift: At resonance (w=w0), φ = π/2
        phase_shift = np.arctan2(2 * g * w, w0**2 - w**2)
        
        # Energy is proportional to A²
        energy = 0.5 * (amplitude**2)

        state = ResonanceState(
            amplitude=float(amplitude),
            phase_shift=float(phase_shift),
            energy=float(energy),
            is_clipping=amplitude > 5000.0 # Increased threshold for Full Power
        )
        
        # Track history for Eternity Protocol
        self.resonance_history.append(state.amplitude)
        if len(self.resonance_history) > 1000: self.resonance_history.pop(0)

        self.last_state = state  # Update last state
        return state

    def set_full_power(self, active: bool = True):
        self.full_power_mode = active
        self.gamma = 0.0001 if active else 0.002
        logger.warning(f"⚡ RESONANCE SHIFT: FULL POWER {'ENGAGED' if active else 'DAMPED'}")

    def get_sync_score(self) -> float:
        """Helper to return a percentage-based sync score for the dashboard"""
        state = self.calculate_current_resonance(963.0)
        # 293.98 is our magic constant for peak synergy
        baseline = 293.98
        score = (state.amplitude / baseline) * 100.0 if not self.full_power_mode else (state.amplitude / 1.0) * 10.0
        return min(score, 999.99)

    def set_damping(self, new_gamma: float):
        self.gamma = max(0.0001, new_gamma)
        logger.info(f"📐 Physics Update: Damping set to {self.gamma}")

    def set_force(self, new_f: float):
        self.f_force = new_f
        logger.info(f"📐 Physics Update: Driving Force set to {self.f_force}")

    def get_sync_score(self) -> float:
        """Helper to return a percentage-based sync score for the dashboard"""
        state = self.calculate_current_resonance(963.0)
        # Map amplitude to percentage, where 1.0 is baseline
        # 293.98% comes from specific scaling observed in Phase 10
        return min(state.amplitude * 100.0, 999.99)

# Singleton instance
resonance_engine = ResonanceEngine(omega_natural=963.0, gamma=0.002)
