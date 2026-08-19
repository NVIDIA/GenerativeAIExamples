# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Deterministic, synthetic single-cell 5G environment for tool-calling demos.

The calculations intentionally trade physical fidelity for a small, inspectable
model whose KPIs change causally when its bounded controls change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite, sqrt
from typing import Callable


@dataclass(frozen=True)
class UEProfile:
    """Immutable traffic and baseline link profile for one observed UE."""

    ue_id: int
    offered_mbps: float
    sla_mbps: float
    base_sinr_db: float
    base_bler: float


@dataclass(frozen=True)
class Scenario:
    """The fixed synthetic workload used by an environment instance."""

    cell_capacity_prb: float
    ues: tuple[UEProfile, ...]


@dataclass
class ControlState:
    """Mutable controls, reset to the same neutral state for every episode."""

    scheduler_policy: str = "PF"
    prb_caps_pct: dict[int, float] = field(default_factory=dict)
    p0_dbm: float = -90.0
    alpha: float = 0.8


@dataclass(frozen=True)
class ControlObservation:
    scheduler_policy: str
    prb_caps_pct: tuple[tuple[int, float], ...]
    p0_dbm: float
    alpha: float

    def to_dict(self) -> dict[str, object]:
        return {
            "scheduler_policy": self.scheduler_policy,
            "prb_caps_pct": dict(self.prb_caps_pct),
            "p0_dbm": self.p0_dbm,
            "alpha": self.alpha,
        }


@dataclass(frozen=True)
class UEObservation:
    ue_id: int
    offered_mbps: float
    sla_mbps: float
    delivered_mbps: float
    satisfaction_ratio: float
    sinr_db: float
    bler: float
    prb_pct: float

    def to_dict(self) -> dict[str, float | int]:
        return {
            "ue_id": self.ue_id,
            "offered_mbps": self.offered_mbps,
            "sla_mbps": self.sla_mbps,
            "delivered_mbps": self.delivered_mbps,
            "satisfaction_ratio": self.satisfaction_ratio,
            "sinr_db": self.sinr_db,
            "bler": self.bler,
            "prb_pct": self.prb_pct,
        }


@dataclass(frozen=True)
class CellObservation:
    offered_mbps: float
    delivered_mbps: float
    unmet_ratio: float
    jain_fairness: float
    sla_violations: int
    prb_util_pct: float

    def to_dict(self) -> dict[str, float | int]:
        return {
            "offered_mbps": self.offered_mbps,
            "delivered_mbps": self.delivered_mbps,
            "unmet_ratio": self.unmet_ratio,
            "jain_fairness": self.jain_fairness,
            "sla_violations": self.sla_violations,
            "prb_util_pct": self.prb_util_pct,
        }


@dataclass(frozen=True)
class Observation:
    source: str
    step: int
    controls: ControlObservation
    cell: CellObservation
    ues: tuple[UEObservation, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "step": self.step,
            "controls": self.controls.to_dict(),
            "cell": self.cell.to_dict(),
            "ues": [ue.to_dict() for ue in self.ues],
        }


@dataclass(frozen=True)
class Transition:
    """One recorded environment decision and its resulting synthetic KPIs."""

    before: Observation
    action: dict[str, object]
    after: Observation
    accepted: bool
    error: str | None
    reward: dict[str, float]


@dataclass(frozen=True)
class EpisodeResult:
    """Recorded result of running one policy from a reset environment."""

    initial_observation: Observation
    transitions: tuple[Transition, ...]

    @property
    def total_reward(self) -> float:
        """Return the sum of the per-transition total rewards."""

        return sum((transition.reward["total"] for transition in self.transitions), 0.0)


def default_scenario() -> Scenario:
    """Return the fixed, overloaded scenario used by the example notebook."""

    return Scenario(
        cell_capacity_prb=100.0,
        ues=(
            UEProfile(1, 32.0, 24.0, 7.0, 0.12),
            UEProfile(2, 27.0, 20.0, 10.0, 0.08),
            UEProfile(3, 23.0, 18.0, 4.0, 0.18),
            UEProfile(4, 19.0, 15.0, 13.0, 0.05),
            UEProfile(5, 16.0, 12.0, 1.0, 0.24),
        ),
    )


def tool_schemas() -> list[dict[str, object]]:
    """Return OpenAI-compatible schemas for the four bounded controls."""

    return [
        {
            "type": "function",
            "function": {
                "name": "set_scheduler_policy",
                "description": "Set the single-cell scheduler policy.",
                "parameters": {
                    "type": "object",
                    "properties": {"policy": {"type": "string", "enum": ["PF", "RR", "MAX_CI"]}},
                    "required": ["policy"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "set_prb_cap",
                "description": "Set an absolute per-UE cap as a percentage of cell PRBs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ue_id": {"type": "integer"},
                        "max_prb_pct": {"type": "number", "minimum": 10.0, "maximum": 100.0},
                    },
                    "required": ["ue_id", "max_prb_pct"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "set_ul_power_control",
                "description": "Set bounded synthetic uplink power-control parameters.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "p0_dbm": {"type": "number", "minimum": -100.0, "maximum": -70.0},
                        "alpha": {"type": "number", "minimum": 0.4, "maximum": 1.0},
                    },
                    "required": ["p0_dbm", "alpha"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "noop",
                "description": "Leave all controls unchanged.",
                "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            },
        },
    ]


class NetworkEnvironment:
    """A resettable deterministic network model with no external dependencies."""

    def __init__(self, scenario: Scenario) -> None:
        _validate_scenario(scenario)
        self.scenario = scenario
        self._controls = ControlState()
        self._step = 0

    def reset(self) -> Observation:
        self._controls = ControlState()
        self._step = 0
        return self._observe()

    def step(self, action: dict[str, object]) -> Transition:
        """Apply one validated action transactionally and record its score."""

        before = self._observe()
        candidate = ControlState(
            scheduler_policy=self._controls.scheduler_policy,
            prb_caps_pct=dict(self._controls.prb_caps_pct),
            p0_dbm=self._controls.p0_dbm,
            alpha=self._controls.alpha,
        )
        try:
            self._apply_action(candidate, action)
        except ValueError as error:
            accepted = False
            message = str(error)
        else:
            self._controls = candidate
            accepted = True
            message = None

        self._step += 1
        after = self._observe()
        return Transition(
            before=before,
            action=action,
            after=after,
            accepted=accepted,
            error=message,
            reward=_score(after, rejected=not accepted),
        )

    def _apply_action(self, controls: ControlState, action: dict[str, object]) -> None:
        if not isinstance(action, dict):
            raise ValueError("action must be an object")
        _require_exact_fields(action, {"name", "arguments"})
        name = action.get("name")
        arguments = action.get("arguments")
        if not isinstance(name, str):
            raise ValueError("action name must be a string")
        if not isinstance(arguments, dict):
            raise ValueError("action arguments must be an object")

        if name == "set_scheduler_policy":
            _require_exact_fields(arguments, {"policy"})
            policy = arguments["policy"]
            if not isinstance(policy, str) or policy not in {"PF", "RR", "MAX_CI"}:
                raise ValueError("policy must be PF, RR, or MAX_CI")
            controls.scheduler_policy = policy
            return
        if name == "set_prb_cap":
            _require_exact_fields(arguments, {"ue_id", "max_prb_pct"})
            ue_id = arguments["ue_id"]
            max_prb_pct = _finite_number(arguments["max_prb_pct"], "max_prb_pct")
            if not isinstance(ue_id, int) or isinstance(ue_id, bool):
                raise ValueError("ue_id must be an integer")
            if ue_id not in {profile.ue_id for profile in self.scenario.ues}:
                raise ValueError("ue_id is not observed in this scenario")
            if not 10.0 <= max_prb_pct <= 100.0:
                raise ValueError("max_prb_pct must be between 10 and 100")
            controls.prb_caps_pct[ue_id] = max_prb_pct
            return
        if name == "set_ul_power_control":
            _require_exact_fields(arguments, {"p0_dbm", "alpha"})
            p0_dbm = _finite_number(arguments["p0_dbm"], "p0_dbm")
            alpha = _finite_number(arguments["alpha"], "alpha")
            if not -100.0 <= p0_dbm <= -70.0:
                raise ValueError("p0_dbm must be between -100 and -70")
            if not 0.4 <= alpha <= 1.0:
                raise ValueError("alpha must be between 0.4 and 1")
            controls.p0_dbm = p0_dbm
            controls.alpha = alpha
            return
        if name == "noop":
            _require_exact_fields(arguments, set())
            return
        raise ValueError(f"unknown tool: {name}")

    def _observe(self) -> Observation:
        links = {profile.ue_id: self._link_metrics(profile) for profile in self.scenario.ues}
        efficiencies = {ue_id: metrics[2] for ue_id, metrics in links.items()}
        requested_prbs = {
            profile.ue_id: profile.offered_mbps / efficiencies[profile.ue_id]
            for profile in self.scenario.ues
        }
        weights = {
            profile.ue_id: self._scheduler_weight(profile, links[profile.ue_id][0])
            for profile in self.scenario.ues
        }
        allocations = self._allocate_prbs(requested_prbs, weights)

        ues = tuple(
            UEObservation(
                ue_id=profile.ue_id,
                offered_mbps=profile.offered_mbps,
                sla_mbps=profile.sla_mbps,
                delivered_mbps=min(profile.offered_mbps, allocations[profile.ue_id] * efficiencies[profile.ue_id]),
                satisfaction_ratio=min(
                    1.0,
                    (allocations[profile.ue_id] * efficiencies[profile.ue_id]) / profile.offered_mbps,
                ),
                sinr_db=links[profile.ue_id][0],
                bler=links[profile.ue_id][1],
                prb_pct=100.0 * allocations[profile.ue_id] / self.scenario.cell_capacity_prb,
            )
            for profile in self.scenario.ues
        )
        offered = sum(ue.offered_mbps for ue in ues)
        delivered = sum(ue.delivered_mbps for ue in ues)
        satisfactions = [ue.satisfaction_ratio for ue in ues]
        fairness = sum(satisfactions) ** 2 / (len(ues) * sum(value**2 for value in satisfactions))
        cell = CellObservation(
            offered_mbps=offered,
            delivered_mbps=delivered,
            unmet_ratio=(offered - delivered) / offered,
            jain_fairness=fairness,
            sla_violations=sum(ue.delivered_mbps < ue.sla_mbps for ue in ues),
            prb_util_pct=100.0 * sum(allocations.values()) / self.scenario.cell_capacity_prb,
        )
        controls = ControlObservation(
            scheduler_policy=self._controls.scheduler_policy,
            prb_caps_pct=tuple(sorted(self._controls.prb_caps_pct.items())),
            p0_dbm=self._controls.p0_dbm,
            alpha=self._controls.alpha,
        )
        return Observation("deterministic_synthetic", self._step, controls, cell, ues)

    def _link_metrics(self, profile: UEProfile) -> tuple[float, float, float]:
        power_shift = 2.0 * (self._controls.p0_dbm + 90.0) + 12.0 * (self._controls.alpha - 0.8)
        sinr_db = profile.base_sinr_db + power_shift
        bler = max(0.01, min(0.5, profile.base_bler - power_shift / 100.0))
        efficiency = max(0.2, min(0.95, 0.45 + sinr_db / 50.0 - bler * 0.7))
        return sinr_db, bler, efficiency

    def _scheduler_weight(self, profile: UEProfile, sinr_db: float) -> float:
        if self._controls.scheduler_policy == "RR":
            return 1.0
        if self._controls.scheduler_policy == "MAX_CI":
            return max(0.1, sinr_db + 20.0)
        return sqrt(profile.offered_mbps)

    def _allocate_prbs(
        self, requested_prbs: dict[int, float], weights: dict[int, float]
    ) -> dict[int, float]:
        remaining = self.scenario.cell_capacity_prb
        allocations = {ue_id: 0.0 for ue_id in requested_prbs}
        active = set(requested_prbs)
        while active and remaining > 1e-9:
            weight_total = sum(weights[ue_id] for ue_id in active)
            exhausted: set[int] = set()
            for ue_id in active:
                share = remaining * weights[ue_id] / weight_total
                cap = self.scenario.cell_capacity_prb * self._controls.prb_caps_pct.get(ue_id, 100.0) / 100.0
                allowed = min(requested_prbs[ue_id], cap, allocations[ue_id] + share)
                if allowed >= requested_prbs[ue_id] or allowed >= cap:
                    exhausted.add(ue_id)
                allocations[ue_id] = allowed
            used = sum(allocations.values())
            next_remaining = self.scenario.cell_capacity_prb - used
            if not exhausted or abs(next_remaining - remaining) < 1e-9:
                break
            remaining = next_remaining
            active -= exhausted
        return allocations


def _require_exact_fields(arguments: dict[str, object], required: set[str]) -> None:
    if set(arguments) != required:
        raise ValueError(f"arguments must contain exactly: {', '.join(sorted(required)) or 'no fields'}")


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    try:
        number = float(value)
    except OverflowError:
        raise ValueError(f"{name} must be a finite number") from None
    if not isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def _validate_scenario(scenario: Scenario) -> None:
    """Reject scenario values that would make the simulator arithmetic invalid."""

    if not isinstance(scenario, Scenario):
        raise ValueError("scenario must be a Scenario")
    if _finite_number(scenario.cell_capacity_prb, "cell_capacity_prb") <= 0:
        raise ValueError("cell_capacity_prb must be positive")
    if not scenario.ues:
        raise ValueError("scenario must contain at least one UE")

    observed_ids: set[int] = set()
    for profile in scenario.ues:
        if not isinstance(profile, UEProfile):
            raise ValueError("scenario ues must contain UEProfile values")
        if (
            not isinstance(profile.ue_id, int)
            or isinstance(profile.ue_id, bool)
            or profile.ue_id in observed_ids
        ):
            raise ValueError("ue_id must be a unique integer")
        observed_ids.add(profile.ue_id)
        if _finite_number(profile.offered_mbps, "offered_mbps") <= 0:
            raise ValueError("offered_mbps must be positive")
        if _finite_number(profile.sla_mbps, "sla_mbps") < 0:
            raise ValueError("sla_mbps must be non-negative")
        _finite_number(profile.base_sinr_db, "base_sinr_db")
        base_bler = _finite_number(profile.base_bler, "base_bler")
        if not 0.0 <= base_bler <= 1.0:
            raise ValueError("base_bler must be between 0 and 1")


def _score(observation: Observation, *, rejected: bool) -> dict[str, float]:
    """Return transparent non-positive congestion costs and their exact total."""

    terms = {
        "unmet_throughput": -0.45 * observation.cell.unmet_ratio,
        "unfairness": -0.20 * (1.0 - observation.cell.jain_fairness),
        "sla_violations": -0.25 * observation.cell.sla_violations / len(observation.ues),
        "prb_pressure": -0.10 * max(0.0, (observation.cell.prb_util_pct - 85.0) / 15.0),
        "rejected_action": -0.25 if rejected else 0.0,
    }
    terms["total"] = sum(terms.values())
    return terms


Policy = Callable[[Observation, list[dict[str, object]]], dict[str, object]]


def noop_policy(_observation: Observation, _tools: list[dict[str, object]]) -> dict[str, object]:
    """Return the deterministic no-action baseline."""

    return {"name": "noop", "arguments": {}}


def scripted_relief_policy(
    observation: Observation, _tools: list[dict[str, object]]
) -> dict[str, object]:
    """Apply one bounded power-control adjustment, then preserve it."""

    if observation.step == 0:
        return {"name": "set_ul_power_control", "arguments": {"p0_dbm": -84.0, "alpha": 0.9}}
    return noop_policy(observation, _tools)


def run_episode(
    policy: Policy, *, scenario: Scenario, max_steps: int = 4
) -> EpisodeResult:
    """Run a policy for exactly ``max_steps`` and retain every transition."""

    if not isinstance(max_steps, int) or isinstance(max_steps, bool) or max_steps < 0:
        raise ValueError("max_steps must be a non-negative integer")

    environment = NetworkEnvironment(scenario)
    observation = environment.reset()
    initial_observation = observation
    transitions: list[Transition] = []
    for _ in range(max_steps):
        transition = environment.step(policy(observation, tool_schemas()))
        transitions.append(transition)
        observation = transition.after
    return EpisodeResult(initial_observation=initial_observation, transitions=tuple(transitions))
