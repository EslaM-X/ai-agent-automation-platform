"""Tests for the agent-platform CLI (thin interface over the evaluation harness).

The CLI must delegate to the existing runner functions - no duplicated
business logic. These tests exercise the subcommands against the real
evaluation harness with a temporary output path.
"""

import json

import pytest

from cli.main import main

CASES = "evaluation/cases"


def test_evaluate_returns_zero_and_writes_report(tmp_path):
    out = tmp_path / "latest.json"
    rc = main(["evaluate", "--cases", CASES, "--out", str(out)])
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["cases_passed"] == report["cases_total"]
    assert report["cases_total"] == 17


def test_gate_passes_against_baseline(tmp_path):
    out = tmp_path / "latest.json"
    rc = main(["gate", "--cases", CASES, "--out", str(out)])
    assert rc == 0


def test_inspect_reports_persisted_state(tmp_path, capsys):
    out = tmp_path / "latest.json"
    main(["evaluate", "--cases", CASES, "--out", str(out)])
    rc = main(["inspect", "--latest", str(out)])
    assert rc == 0
    captured = capsys.readouterr().out
    assert "17/17 passed" in captured


def test_inspect_case_detail(tmp_path, capsys):
    out = tmp_path / "latest.json"
    main(["evaluate", "--cases", CASES, "--out", str(out)])
    rc = main(["inspect", "--latest", str(out), "--case", "EVAL-001"])
    assert rc == 0
    captured = capsys.readouterr().out
    assert "case [EVAL-001]" in captured


def test_inspect_missing_state_fails(tmp_path):
    rc = main(["inspect", "--latest", str(tmp_path / "missing.json")])
    assert rc == 1


def test_inspect_unknown_case_fails(tmp_path, capsys):
    out = tmp_path / "latest.json"
    main(["evaluate", "--cases", CASES, "--out", str(out)])
    rc = main(["inspect", "--latest", str(out), "--case", "NOPE-000"])
    assert rc == 1
    assert "no case with id" in capsys.readouterr().out


def test_requires_subcommand():
    with pytest.raises(SystemExit):
        main([])
