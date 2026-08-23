"""Unit tests — simulator."""

from core.simulator.pick_place import PickPlaceEnv
from policies.nominal import NominalPolicy
from schemas.task import TaskConfig


def test_reset_is_deterministic():
    task = TaskConfig()
    a = PickPlaceEnv(task, seed=42).snapshot()
    b = PickPlaceEnv(task, seed=42).snapshot()
    assert a == b


def test_different_seeds_same_task_layout():
    task = TaskConfig()
    a = PickPlaceEnv(task, seed=1).snapshot()
    b = PickPlaceEnv(task, seed=2).snapshot()
    assert a["object_x"] == b["object_x"]
    assert a["target_x"] == b["target_x"]


def test_step_moves_ee_within_bounds():
    env = PickPlaceEnv(TaskConfig(), seed=0)
    env.step({"dx": 0.5, "dy": 0.5, "toggle_gripper": False})
    assert 0.0 <= env.state["ee_x"] <= 1.0
    assert 0.0 <= env.state["ee_y"] <= 1.0


def test_grasp_when_close():
    env = PickPlaceEnv(TaskConfig(), seed=0)
    env.state["ee_x"] = env.state["object_x"]
    env.state["ee_y"] = env.state["object_y"]
    env.step({"dx": 0.0, "dy": 0.0, "toggle_gripper": True})
    assert env.state["grasped"] is True


def test_slip_releases_object():
    env = PickPlaceEnv(TaskConfig(), seed=0)
    env.state["grasped"] = True
    env.state["gripper_open"] = False
    before = env.state["object_y"]
    env.force_slip(0.5, "negative_y")
    assert env.state["grasped"] is False
    assert env.state["object_y"] < before


def test_nominal_policy_completes_ten_times():
    task = TaskConfig()
    for seed in range(10):
        env = PickPlaceEnv(task, seed=seed)
        policy = NominalPolicy()
        policy.reset(task)
        for _ in range(task.max_steps):
            obs = env.get_observation()
            action = policy.act(obs, task.instruction)
            _, done = env.step(action)
            if done:
                break
        assert env.is_success(), f"seed {seed} failed"
