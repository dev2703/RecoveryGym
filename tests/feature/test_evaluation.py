"""Feature tests — evaluation suite, comparison matrix, world model, training."""

from core.evaluation.suite import METHODS, run_comparison, run_evaluation
from core.sim.wam_provider import WAMProvider
from schemas.benchmark import BenchmarkProfile
from training.finetune import finetune_smolvla


def test_quick_profile_returns_metrics_and_baseline():
    result = run_evaluation(profile=BenchmarkProfile.QUICK, episodes=4, seed_base=0)
    assert len(result["episodes"]) == 4
    assert len(result["baseline_episodes"]) == 4
    assert "final_success_rate" in result["metrics"]
    assert "final_success_rate" in result["baseline_metrics"]


def test_ood_profile_marks_every_episode_ood():
    result = run_evaluation(
        profile=BenchmarkProfile.OOD, episodes=3, compare_baseline=False, seed_base=5
    )
    assert all(e["is_ood"] for e in result["episodes"])
    assert all(e["split"] == "ood" for e in result["episodes"])


def test_evaluation_honours_requested_policy():
    result = run_evaluation(episodes=2, policy_id="smolvla", compare_baseline=False)
    assert all(e["method"] == "smolvla" for e in result["episodes"])


def test_comparison_matrix_covers_four_methods():
    result = run_comparison(known_episodes=3, ood_episodes=2, seed_base=10)
    assert {row["method"] for row in result["summary_table"]} == set(METHODS)
    for row in result["summary_table"]:
        assert 0.0 <= row["known_success_pct"] <= 100.0
        assert 0.0 <= row["ood_success_pct"] <= 100.0


def test_methods_differ_in_recovery_ownership():
    assert METHODS["baseline"].recovery is None
    assert METHODS["smolvla_zeroshot"].recovery is None
    assert METHODS["rule"].recovery is not None
    assert METHODS["smolvla_finetuned"].recovery is not None


def test_wam_counterfactual_is_cached():
    wam = WAMProvider(use_mock=True)
    trajectory = {"steps": [{"t": i} for i in range(5)], "seed": 1}
    perturbation = {"step": 2, "type": "OBJECT_SLIP", "severity": 0.4}
    first = wam.counterfactual(trajectory, perturbation)
    assert first == wam.counterfactual(trajectory, perturbation)
    assert "counterfactual" in first


def test_finetune_reports_dataset_without_claiming_training(tmp_path):
    dataset = tmp_path / "d.jsonl"
    dataset.write_text('{"episode_id":"e1","failure_type":"OBJECT_SLIP","actions":[{"dx":0.1}]}\n')
    manifest = finetune_smolvla(str(dataset), output_dir=str(tmp_path / "out"))
    assert manifest["num_episodes"] == 1
    assert manifest["trained"] is False
    assert manifest["dataset"]["with_action_chunks"] == 1


def test_finetune_handles_missing_dataset(tmp_path):
    manifest = finetune_smolvla(str(tmp_path / "missing.jsonl"), output_dir=str(tmp_path / "out"))
    assert manifest["status"] == "pipeline_ready_empty_dataset"
    assert manifest["num_episodes"] == 0
