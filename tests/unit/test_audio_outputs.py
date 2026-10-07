"""Tests for AudioOutputs, which lists and toggles outputs via a host command."""

import subprocess
from unittest.mock import MagicMock

import pytest

from pikaraoke.lib import audio_outputs as ao
from pikaraoke.lib.audio_outputs import AudioOutputs

LISTING = "hdmi on Monitor speakers\ndante off Dante (mixer)\n"


@pytest.fixture
def run(monkeypatch):
    """Stand in for subprocess.run, answering 'list' with LISTING."""
    mock = MagicMock(return_value=subprocess.CompletedProcess([], 0, stdout=LISTING))
    monkeypatch.setattr(ao.subprocess, "run", mock)
    return mock


def test_unavailable_without_a_command(run):
    outputs = AudioOutputs(None)

    assert outputs.available is False
    assert outputs.get_outputs() == []
    run.assert_not_called()


def test_list_parses_id_state_and_label(run):
    outputs = AudioOutputs("karaoke-audio")

    assert outputs.get_outputs() == [
        {"id": "hdmi", "label": "Monitor speakers", "enabled": True},
        {"id": "dante", "label": "Dante (mixer)", "enabled": False},
    ]
    assert run.call_args.args[0] == ["karaoke-audio", "list"]


def test_list_skips_lines_it_does_not_understand(run):
    run.return_value = subprocess.CompletedProcess([], 0, stdout="hdmi on\nnoise\nusb maybe USB\n")

    assert AudioOutputs("karaoke-audio").get_outputs() == [
        {"id": "hdmi", "label": "hdmi", "enabled": True}
    ]


def test_list_is_empty_when_the_command_fails(run):
    run.side_effect = subprocess.CalledProcessError(1, "karaoke-audio")

    assert AudioOutputs("karaoke-audio").get_outputs() == []


def test_set_enabled_runs_the_command_for_a_listed_output(run):
    AudioOutputs("sudo -n karaoke-audio").set_enabled("dante", True)

    assert ["sudo", "-n", "karaoke-audio", "dante", "on"] in [c.args[0] for c in run.call_args_list]


def test_set_enabled_refuses_an_unlisted_output(run):
    AudioOutputs("karaoke-audio").set_enabled("--help", False)

    assert all(c.args[0] == ["karaoke-audio", "list"] for c in run.call_args_list)
