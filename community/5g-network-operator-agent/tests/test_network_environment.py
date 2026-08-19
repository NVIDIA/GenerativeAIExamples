# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Tests for the deterministic synthetic 5G network environment."""

import json
import sys
from pathlib import Path

import pytest

EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXAMPLE_ROOT))

from network_environment import (  # noqa: E402
    NetworkEnvironment,
    Scenario,
    UEProfile,
    default_scenario,
    noop_policy,
    run_episode,
    scripted_relief_policy,
    tool_schemas,
)


def test_reset_is_deterministic_and_marks_observation_synthetic():
    environment = NetworkEnvironment(default_scenario())
    first = environment.reset().to_dict()
    environment.step({"name": "set_ul_power_control", "arguments": {"p0_dbm": -84, "alpha": 0.9}})
    second = environment.reset().to_dict()

    assert first == second
    assert first["source"] == "deterministic_synthetic"
    assert first["cell"]["sla_violations"] > 0


def test_tool_schemas_expose_exactly_the_bounded_network_actions():
    schemas = tool_schemas()
    names = {schema["function"]["name"] for schema in schemas}

    assert names == {"set_scheduler_policy", "set_prb_cap", "set_ul_power_control", "noop"}
    power = next(schema for schema in schemas if schema["function"]["name"] == "set_ul_power_control")
    properties = power["function"]["parameters"]["properties"]
    assert properties["p0_dbm"]["minimum"] < properties["p0_dbm"]["maximum"]
    assert properties["alpha"]["minimum"] < properties["alpha"]["maximum"]


def test_power_control_parameters_change_the_next_kpis():
    low = NetworkEnvironment(default_scenario())
    high = NetworkEnvironment(default_scenario())
    low.reset()
    high.reset()

    low_after = low.step(
        {"name": "set_ul_power_control", "arguments": {"p0_dbm": -96, "alpha": 0.7}}
    ).after
    high_after = high.step(
        {"name": "set_ul_power_control", "arguments": {"p0_dbm": -84, "alpha": 0.9}}
    ).after

    assert low_after.cell.delivered_mbps != high_after.cell.delivered_mbps


def test_reapplying_an_absolute_control_is_idempotent():
    env = NetworkEnvironment(default_scenario())
    env.reset()
    action = {"name": "set_prb_cap", "arguments": {"ue_id": 1, "max_prb_pct": 10.0}}

    first = env.step(action)
    second = env.step(action)

    assert first.accepted and second.accepted
    assert next(ue.prb_pct for ue in first.after.ues if ue.ue_id == 1) == 10.0
    assert first.after.cell.to_dict() == second.after.cell.to_dict()
    assert [ue.to_dict() for ue in first.after.ues] == [ue.to_dict() for ue in second.after.ues]


@pytest.mark.parametrize(
    "action",
    (
        {"name": "set_prb_cap", "arguments": {"ue_id": 99, "max_prb_pct": 50}},
        {"name": "set_prb_cap", "arguments": {"ue_id": True, "max_prb_pct": 50}},
        {"name": "set_prb_cap", "arguments": {"ue_id": 1, "max_prb_pct": 101}},
        {"name": "set_ul_power_control", "arguments": {"p0_dbm": float("nan"), "alpha": 0.8}},
        {"name": "set_ul_power_control", "arguments": {"p0_dbm": -101, "alpha": 0.8}},
        {"name": "set_ul_power_control", "arguments": {"p0_dbm": -90, "alpha": 1.1}},
        {"name": "set_scheduler_policy", "arguments": {}},
        {"name": "set_scheduler_policy", "arguments": {"policy": "INVALID"}},
        {"name": "set_scheduler_policy", "arguments": {"policy": []}},
        {"name": "set_scheduler_policy", "arguments": {"policy": {}}},
        {"name": "noop", "arguments": {}, "unexpected": "field"},
    ),
)
def test_invalid_actions_are_rejected_without_mutation(action):
    env = NetworkEnvironment(default_scenario())
    before = env.reset()

    rejected = env.step(action)

    assert not rejected.accepted
    assert rejected.before.to_dict() == before.to_dict()
    assert rejected.error
    assert rejected.after.cell.to_dict() == before.cell.to_dict()
    assert rejected.reward["rejected_action"] < 0


def test_reward_total_is_the_exact_sum_of_its_decomposed_terms():
    env = NetworkEnvironment(default_scenario())
    env.reset()

    transition = env.step({"name": "noop", "arguments": {}})
    terms = transition.reward

    assert terms["total"] == sum(value for name, value in terms.items() if name != "total")
    assert all(value <= 0 for value in terms.values())


def test_scheduler_policy_changes_kpis_and_observation_is_json_serializable():
    env = NetworkEnvironment(default_scenario())
    before = env.reset()
    after = env.step({"name": "set_scheduler_policy", "arguments": {"policy": "RR"}}).after

    assert after.cell.to_dict() != before.cell.to_dict()
    assert json.loads(json.dumps(after.to_dict()))["source"] == "deterministic_synthetic"


def test_run_episode_records_the_requested_fixed_horizon_and_total_reward():
    episode = run_episode(noop_policy, scenario=default_scenario(), max_steps=3)

    assert len(episode.transitions) == 3
    assert [transition.before.step for transition in episode.transitions] == [0, 1, 2]
    assert [transition.after.step for transition in episode.transitions] == [1, 2, 3]
    assert episode.total_reward == sum(transition.reward["total"] for transition in episode.transitions)


def test_scripted_relief_beats_noop_on_the_bundled_scenario():
    noop_episode = run_episode(noop_policy, scenario=default_scenario(), max_steps=4)
    relief_episode = run_episode(scripted_relief_policy, scenario=default_scenario(), max_steps=4)

    assert relief_episode.total_reward > noop_episode.total_reward


def test_zero_step_episode_keeps_the_reset_observation_and_has_no_reward():
    episode = run_episode(noop_policy, scenario=default_scenario(), max_steps=0)

    assert episode.initial_observation.step == 0
    assert episode.transitions == ()
    assert episode.total_reward == 0.0


def test_negative_max_steps_is_rejected():
    with pytest.raises(ValueError, match="max_steps"):
        run_episode(noop_policy, scenario=default_scenario(), max_steps=-1)


def test_malformed_policy_action_is_recorded_as_a_rejected_transition():
    def malformed_policy(_observation, _tools):
        return {"name": "not_a_tool", "arguments": {}}

    episode = run_episode(malformed_policy, scenario=default_scenario(), max_steps=1)

    assert len(episode.transitions) == 1
    assert not episode.transitions[0].accepted
    assert episode.transitions[0].error == "unknown tool: not_a_tool"


@pytest.mark.parametrize(
    ("scenario", "message"),
    (
        (Scenario(float("nan"), (UEProfile(1, 1.0, 0.0, 0.0, 0.0),)), "cell_capacity_prb"),
        (Scenario(0.0, (UEProfile(1, 1.0, 0.0, 0.0, 0.0),)), "cell_capacity_prb"),
        (Scenario(100.0, ()), "at least one UE"),
        (
            Scenario(100.0, (UEProfile(1, 1.0, 0.0, 0.0, 0.0), UEProfile(1, 1.0, 0.0, 0.0, 0.0))),
            "unique integer",
        ),
        (Scenario(100.0, (UEProfile(1.5, 1.0, 0.0, 0.0, 0.0),)), "unique integer"),
        (Scenario(100.0, (UEProfile(1, 0.0, 0.0, 0.0, 0.0),)), "offered_mbps"),
        (Scenario(100.0, (UEProfile(1, 1.0, -1.0, 0.0, 0.0),)), "sla_mbps"),
        (Scenario(100.0, (UEProfile(1, 1.0, 0.0, float("inf"), 0.0),)), "base_sinr_db"),
        (Scenario(100.0, (UEProfile(1, 1.0, 0.0, 0.0, 1.1),)), "base_bler"),
    ),
)
def test_environment_rejects_structurally_or_arithmetically_invalid_scenarios(scenario, message):
    with pytest.raises(ValueError, match=message):
        NetworkEnvironment(scenario)
