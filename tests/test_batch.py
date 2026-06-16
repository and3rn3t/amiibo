"""Tests for batch mode."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from amiibo_flipper.batch import BatchCommand, BatchResult, BatchRunner, create_batch_from_yaml


def test_batch_command_creation() -> None:
    """Test BatchCommand creation."""
    cmd = BatchCommand(name="fetch", kwargs={"output": "data/amiibo.json"})
    assert cmd.name == "fetch"
    assert cmd.kwargs["output"] == "data/amiibo.json"


def test_batch_result_initialization() -> None:
    """Test BatchResult initialization."""
    result = BatchResult(
        commands_run=3,
        commands_succeeded=2,
        commands_failed=1,
        failures=[("sync", "SD path not found")],
        outputs={"fetch": {"count": 100}},
    )
    assert result.commands_run == 3
    assert result.commands_succeeded == 2
    assert result.commands_failed == 1


def test_batch_runner_initialization() -> None:
    """Test BatchRunner initialization."""
    runner = BatchRunner()
    assert runner.result.commands_run == 0
    assert runner.result.commands_succeeded == 0
    assert runner.result.commands_failed == 0


def test_batch_runner_unknown_command() -> None:
    """Test BatchRunner with unknown command."""
    runner = BatchRunner()
    commands = [BatchCommand(name="unknown_cmd", kwargs={})]
    result = runner.run(commands)

    assert result.commands_run == 1
    assert result.commands_failed == 1
    assert len(result.failures) == 1


def test_create_batch_from_yaml() -> None:
    """Test parsing batch commands from YAML."""
    yaml_content = """
commands:
  - name: fetch
    output: data/amiibo.json
  - name: export
    input: data/amiibo.json
    output: flipper-export
"""
    commands = create_batch_from_yaml(yaml_content)

    assert len(commands) == 2
    assert commands[0].name == "fetch"
    assert commands[0].kwargs["output"] == "data/amiibo.json"
    assert commands[1].name == "export"


def test_create_batch_from_empty_yaml() -> None:
    """Test parsing batch from empty YAML."""
    yaml_content = "commands: []"
    commands = create_batch_from_yaml(yaml_content)
    assert len(commands) == 0


def test_create_batch_preserves_kwargs() -> None:
    """Test that all kwargs are preserved from YAML."""
    yaml_content = """
commands:
  - name: convert-bin
    source: /path/to/source
    output: /path/to/output
    flatten: true
    overwrite: false
"""
    commands = create_batch_from_yaml(yaml_content)

    assert len(commands) == 1
    cmd = commands[0]
    assert cmd.name == "convert-bin"
    assert cmd.kwargs["source"] == "/path/to/source"
    assert cmd.kwargs["flatten"] is True
    assert cmd.kwargs["overwrite"] is False
