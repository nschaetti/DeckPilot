from pathlib import Path

from typer.testing import CliRunner

from deckpilot.cli import app

runner = CliRunner()
SIM_CONFIG = Path("config/simulators/original.toml")


def test_devices_lists_simulator_decks():
    result = runner.invoke(
        app,
        [
            "devices",
            "--use-simulator",
            "--simulator-config",
            str(SIM_CONFIG),
        ],
    )

    assert result.exit_code == 0
    assert "Detected Stream Deck devices" in result.stdout
    assert "SIM-ORIGINAL-001" in result.stdout


def test_show_by_serial_displays_details():
    result = runner.invoke(
        app,
        [
            "show",
            "--serial",
            "SIM-ORIGINAL-001",
            "--use-simulator",
            "--simulator-config",
            str(SIM_CONFIG),
        ],
    )

    assert result.exit_code == 0
    assert "Stream Deck #0" in result.stdout
    assert "SIM-ORIGINAL-001" in result.stdout


def test_show_requires_identifier():
    result = runner.invoke(app, ["show"])

    assert result.exit_code != 0
    assert "Provide either --index or --serial" in result.stdout
