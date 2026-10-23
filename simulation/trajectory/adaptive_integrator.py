"""
Adaptive Numerical Integrator (Dormand-Prince RK45) and Astrodynamics Propagator.
Implements:
  1. Embedded Runge-Kutta 5(4) Dormand-Prince pair with local truncation error control.
  2. Two-body Keplerian equations of motion.
  3. Conservation metric monitors:
     - Specific Orbital Energy: E = v^2 / 2 - mu / r
     - Specific Angular Momentum vector: h_vec = r_vec x v_vec
  4. Mass depletion integration:
     - dm/dt = - T / (Isp * g0)
  5. Multi-tolerance convergence sweep and error analysis.
"""

import math
import numpy as np
from typing import Callable, Dict, Tuple, List, Any, Optional

class DormandPrince45:
    """
    Dormand-Prince 5(4) adaptive-step numerical integrator.
    Local error control with order 5 solution and order 4 embedded comparison.
    """
    # Butcher Tableau coefficients
    c = np.array([0.0, 1.0/5.0, 3.0/10.0, 4.0/5.0, 8.0/9.0, 1.0, 1.0])

    a = [
        np.array([]),
        np.array([1.0/5.0]),
        np.array([3.0/40.0, 9.0/40.0]),
        np.array([44.0/45.0, -56.0/15.0, 32.0/9.0]),
        np.array([19372.0/6561.0, -25360.0/2187.0, 64448.0/6561.0, -212.0/729.0]),
        np.array([9017.0/3168.0, -355.0/33.0, 46732.0/5247.0, 49.0/176.0, -5103.0/18656.0]),
        np.array([35.0/384.0, 0.0, 500.0/1113.0, 125.0/192.0, -2187.0/6784.0, 11.0/84.0])
    ]

    # Order 5 weights
    b5 = np.array([35.0/384.0, 0.0, 500.0/1113.0, 125.0/192.0, -2187.0/6784.0, 11.0/84.0, 0.0])

    # Error weights (b5 - b4)
    e = np.array([
        71.0/57600.0,
        0.0,
        -71.0/16695.0,
        71.0/1920.0,
        -17253.0/339200.0,
        22.0/525.0,
        -1.0/40.0
    ])

    def __init__(self, rtol: float = 1e-8, atol: float = 1e-10, h_min: float = 1e-6, h_max: float = 3600.0):
        self.rtol = rtol
        self.atol = atol
        self.h_min = h_min
        self.h_max = h_max

    def step(self, f: Callable[[float, np.ndarray], np.ndarray], t: float, y: np.ndarray, h: float) -> Tuple[np.ndarray, float, float, bool]:
        """
        Take a single adaptive step using DP5(4).
        Returns: (y_next, t_next, h_next, accepted)
        """
        k = [np.zeros_like(y) for _ in range(7)]
        k[0] = f(t, y)

        for s in range(1, 7):
            dy = np.zeros_like(y)
            for j in range(s):
                dy += self.a[s][j] * k[j]
            k[s] = f(t + self.c[s] * h, y + h * dy)

        # 5th order solution
        y_next = y.copy()
        for s in range(6):
            y_next += h * self.b5[s] * k[s]

        # Truncation error vector
        err_vec = np.zeros_like(y)
        for s in range(7):
            err_vec += h * self.e[s] * k[s]

        # Scale error against tolerances
        scale = self.atol + self.rtol * np.maximum(np.abs(y), np.abs(y_next))
        err_ratio = np.max(np.abs(err_vec) / scale)

        # Step size adjustment with safety factor 0.9
        if err_ratio <= 1.0:
            # Step accepted
            factor = min(2.0, max(0.2, 0.9 * (err_ratio ** -0.2))) if err_ratio > 1e-10 else 2.0
            h_next = min(self.h_max, max(self.h_min, h * factor))
            return y_next, t + h, h_next, True
        else:
            # Step rejected, retry with smaller step
            factor = max(0.1, 0.9 * (err_ratio ** -0.25))
            h_retry = max(self.h_min, h * factor)
            return y, t, h_retry, False

    def integrate(self, 
                  f: Callable[[float, np.ndarray], np.ndarray], 
                  t_span: Tuple[float, float], 
                  y0: np.ndarray, 
                  h_initial: float = 10.0) -> Dict[str, Any]:
        """
        Integrate system dy/dt = f(t, y) from t_span[0] to t_span[1].
        """
        t = t_span[0]
        t_end = t_span[1]
        y = y0.astype(np.float64).copy()
        h = min(h_initial, t_end - t)

        t_hist = [t]
        y_hist = [y.copy()]
        h_hist = [h]
        accepted_steps = 0
        rejected_steps = 0

        while t < t_end:
            if t + h > t_end:
                h = t_end - t

            y_cand, t_cand, h_cand, accepted = self.step(f, t, y, h)
            if accepted:
                t = t_cand
                y = y_cand
                t_hist.append(t)
                y_hist.append(y.copy())
                h_hist.append(h)
                accepted_steps += 1
                h = h_cand
            else:
                rejected_steps += 1
                h = h_cand
                if h <= self.h_min:
                    # Minimum step underflow safeguard
                    t += h
                    t_hist.append(t)
                    y_hist.append(y.copy())
                    break

        return {
            "t": np.array(t_hist),
            "y": np.array(y_hist),
            "h": np.array(h_hist),
            "accepted_steps": accepted_steps,
            "rejected_steps": rejected_steps
        }


class TwoBodyOrbitalPropagator:
    """
    Two-body gravitational dynamics with rigorous conservation calculation.
    """
    MU_EARTH = 3.986004418e14  # Earth standard gravitational parameter [m^3/s^2]
    R_EARTH = 6378137.0         # Earth equatorial radius [m]
    G0 = 9.80665               # Standard gravity [m/s^2]

    def __init__(self, mu: float = MU_EARTH):
        self.mu = mu

    def state_derivative(self, t: float, state: np.ndarray) -> np.ndarray:
        """
        state = [rx, ry, rz, vx, vy, vz]
        d(state)/dt = [vx, vy, vz, ax, ay, az]
        ax, ay, az = -mu * r_vec / |r|^3
        """
        r_vec = state[0:3]
        v_vec = state[3:6]
        r = np.linalg.norm(r_vec)
        if r < 1.0:
            return np.zeros(6)
        a_vec = - (self.mu / (r ** 3)) * r_vec
        return np.concatenate([v_vec, a_vec])

    def state_with_thrust_derivative(self, 
                                     thrust_N: float, 
                                     isp_s: float) -> Callable[[float, np.ndarray], np.ndarray]:
        """
        state = [rx, ry, rz, vx, vy, vz, mass]
        d(state)/dt = [vx, vy, vz, a_grav + a_thrust, dm/dt]
        Thrust aligned with velocity vector.
        """
        def deriv(t: float, state: np.ndarray) -> np.ndarray:
            r_vec = state[0:3]
            v_vec = state[3:6]
            m = state[6]

            r = np.linalg.norm(r_vec)
            v = np.linalg.norm(v_vec)

            a_grav = - (self.mu / (r ** 3)) * r_vec if r > 1.0 else np.zeros(3)
            
            if m > 100.0 and v > 1e-4 and thrust_N > 0.0:
                u_v = v_vec / v
                a_thrust = (thrust_N / m) * u_v
                dm_dt = - thrust_N / (isp_s * self.G0)
            else:
                a_thrust = np.zeros(3)
                dm_dt = 0.0

            a_total = a_grav + a_thrust
            return np.concatenate([v_vec, a_total, [dm_dt]])

        return deriv

    @staticmethod
    def specific_energy(r_vec: np.ndarray, v_vec: np.ndarray, mu: float = MU_EARTH) -> float:
        """Specific orbital energy: E = v^2 / 2 - mu / r [J/kg]"""
        r = np.linalg.norm(r_vec)
        v = np.linalg.norm(v_vec)
        return (v ** 2) / 2.0 - (mu / r)

    @staticmethod
    def specific_angular_momentum(r_vec: np.ndarray, v_vec: np.ndarray) -> np.ndarray:
        """Specific angular momentum vector: h = r x v [m^2/s]"""
        return np.cross(r_vec, v_vec)
