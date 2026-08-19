# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Tests for the deterministic synthetic 5G network environment."""

import json
from math import isfinite
from pathlib import Path
import sys

import pytest

EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXAMPLE_ROOT))

from network_environment import (
    EpisodeResult,
    NetworkEnvironment,
    default_scenario,
    noop_policy,
    run_episode,
    scripted_relief_policy,
    tool_schemas,
)


def test_reset_is_deterministic_and_marks_observation_synthetic():
    first = NetworkEnvironment(default_scenario()).reset().to_dict()
    second = NetworkEnvironment(default_scenario()).reset().to_dict()

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
    action = {"name": "set_prb_cap", "arguments": {"ue_id": 1, "max_prb_pct": 35.0}}

    first = env.step(action)
    second = env.step(action)

    assert first.accepted and second.accepted
    assert first.after.cell.to_dict() == second.after.cell.to_dict()
    assert [ue.to_dict() for ue in first.after.ues] == [ue.to_dict() for ue in second.after.ues]


def test_rejected_action_does_not_mutate_controls():
    env = NetworkEnvironment(default_scenario())
    before = env.reset()

    rejected = env.step({"name": "set_prb_cap", "arguments": {"ue_id": 99, "max_prb_pct": 50}})

    assert not rejected.accepted
    assert rejected.before.to_dict() == before.to_dict()
    assert rejected.after.cell.to_dict() == before.cell.to_dict()
    assert rejected.reward["rejected_action"] < 0


def test_booleans_non_finite_values_and_missing_fields_are_rejected_without_mutation():
    for action in (
        {"name": "set_prb_cap", "arguments": {"ue_id": True, "max_prb_pct": 50}},
        {"name": "set_ul_power_control", "arguments": {"p0_dbm": float("nan"), "alpha": 0.8}},
        {"name": "set_scheduler_policy", "arguments": {}},
    ):
        env = NetworkEnvironment(default_scenario())
        before = env.reset()
        rejected = env.step(action)

        assert not rejected.accepted
        assert rejected.after.cell.to_dict() == before.cell.to_dict()


def test_json_shaped_scheduler_policies_are_rejected_without_crashing():
    for policy in ([], {}):
        env = NetworkEnvironment(default_scenario())
        before = env.reset()

        rejected = env.step({"name": "set_scheduler_policy", "arguments": {"policy": policy}})

        assert not rejected.accepted
        assert rejected.error
        assert rejected.after.cell.to_dict() == before.cell.to_dict()
        assert isfinite(rejected.reward["rejected_action"])


def test_extra_top_level_action_fields_are_rejected_without_mutation():
    env = NetworkEnvironment(default_scenario())
    before = env.reset()

    rejected = env.step({"name": "noop", "arguments": {}, "unexpected": "field"})

    assert not rejected.accepted
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


def test_transition_and_observation_are_json_serializable():
    env = NetworkEnvironment(default_scenario())
    observation = env.reset()
    transition = env.step({"name": "set_scheduler_policy", "arguments": {"policy": "RR"}})

    assert json.loads(json.dumps(observation.to_dict()))["source"] == "deterministic_synthetic"
    assert json.loads(json.dumps(transition.to_dict()))["accepted"] is True


def test_run_episode_records_the_requested_fixed_horizon_and_total_reward():
    episode = run_episode(noop_policy, scenario=default_scenario(), max_steps=3)

    assert isinstance(episode, EpisodeResult)
    assert len(episode.transitions) == 3
    assert [transition.before.step for transition in episode.transitions] == [0, 1, 2]
    assert [transition.after.step for transition in episode.transitions] == [1, 2, 3]
    assert episode.total_reward == sum(transition.reward["total"] for transition in episode.transitions)


def test_episode_result_is_strictly_json_serializable():
    episode = run_episode(scripted_relief_policy, scenario=default_scenario(), max_steps=4)

    assert json.loads(json.dumps(episode.to_dict(), allow_nan=False))["total_reward"] == episode.total_reward


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
