# pwc/critic.py
from .types import Trajectory, TrajectoryScore, Violation


class Critic:
    def __init__(self):
        pass

    def evaluate_trajectory(self, trajectory: Trajectory) -> TrajectoryScore:
        samples = trajectory.samples
        if not samples:
            return TrajectoryScore(
                plan_id=trajectory.plan_id,
                stability_score=0.0,
                safety_score=0.0,
                efficiency_score=0.0,
                integrity_score=0.0,
                overall_score=0.0,
                violations=[],
            )

        drifts = [s.manifold_state.global_drift for s in samples]
        pressures = [s.manifold_state.global_pressure for s in samples]
        safety_flags = [s.safety_flags for s in samples]

        # Very simple metrics
        drift_var = self._variance(drifts)
        stability_score = 1.0 / (1.0 + drift_var)

        trip_count = sum(
            1
            for f in safety_flags
            if f.drift_exceeded or f.pressure_exceeded or f.spectral_instability
        )
        safety_score = 1.0 / (1.0 + trip_count)

        avg_pressure = sum(pressures) / len(pressures)
        efficiency_score = 1.0 / (1.0 + avg_pressure)

        # Integrity: penalize quarantines
        quarantine_count = sum(1 for f in safety_flags if f.quarantined)
        integrity_score = 1.0 / (1.0 + quarantine_count)

        overall_score = (
            0.4 * stability_score
            + 0.3 * safety_score
            + 0.2 * efficiency_score
            + 0.1 * integrity_score
        )

        violations: list[Violation] = []
        for i, f in enumerate(safety_flags):
            if f.drift_exceeded:
                violations.append(
                    Violation(
                        tick_index=i,
                        type="DRIFT_EXCEEDED",
                        severity=1.0,
                        details="Drift exceeded configured limit",
                    )
                )
            if f.pressure_exceeded:
                violations.append(
                    Violation(
                        tick_index=i,
                        type="PRESSURE_EXCEEDED",
                        severity=1.0,
                        details="GS pressure exceeded budget",
                    )
                )
            if f.spectral_instability:
                violations.append(
                    Violation(
                        tick_index=i,
                        type="SPECTRAL_INSTABILITY",
                        severity=1.0,
                        details="Spectral instability detected",
                    )
                )

        return TrajectoryScore(
            plan_id=trajectory.plan_id,
            stability_score=stability_score,
            safety_score=safety_score,
            efficiency_score=efficiency_score,
            integrity_score=integrity_score,
            overall_score=overall_score,
            violations=violations,
        )

    @staticmethod
    def _variance(xs: list[float]) -> float:
        if not xs:
            return 0.0
        m = sum(xs) / len(xs)
        return sum((x - m) ** 2 for x in xs) / len(xs)