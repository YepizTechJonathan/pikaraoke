"""Switch audio outputs on and off through a host-provided command.

Routing PiKaraoke's sound to several outputs at once (an HDMI screen, a
network audio device, a USB interface) depends entirely on how the host's
sound system is set up, so PiKaraoke does not do the routing itself. The host
supplies a command, and PiKaraoke only lists and toggles what it reports:

    <command> list            one line per output: "<id> <on|off> <label>"
    <command> <id> on|off     turn one output on or off
"""

import logging
import shlex
import subprocess

_TIMEOUT_S = 10


class AudioOutputs:
    """Lists and toggles audio outputs through the configured command."""

    def __init__(self, command: str | None) -> None:
        self._command = shlex.split(command) if command else []

    @property
    def available(self) -> bool:
        return bool(self._command)

    def get_outputs(self) -> list[dict]:
        """Return the outputs the command reports, or an empty list if it fails."""
        if not self.available:
            return []
        output = self._run("list")
        if output is None:
            return []
        outputs = []
        for line in output.splitlines():
            parts = line.split(maxsplit=2)
            if len(parts) < 2 or parts[1] not in ("on", "off"):
                if line.strip():
                    logging.warning(f"Ignoring unrecognised audio output line: {line!r}")
                continue
            output_id, state = parts[0], parts[1]
            label = parts[2] if len(parts) == 3 else output_id
            outputs.append({"id": output_id, "label": label, "enabled": state == "on"})
        return outputs

    def set_enabled(self, output_id: str, enabled: bool) -> list[dict]:
        """Turn one output on or off, then return the refreshed list.

        Only ids the command itself listed are passed back to it.
        """
        if output_id not in {output["id"] for output in self.get_outputs()}:
            logging.warning(f"Refused unknown audio output: {output_id!r}")
        else:
            self._run(output_id, "on" if enabled else "off")
        return self.get_outputs()

    def _run(self, *args: str) -> str | None:
        try:
            result = subprocess.run(
                [*self._command, *args],
                capture_output=True,
                text=True,
                timeout=_TIMEOUT_S,
                check=True,
            )
        except (OSError, subprocess.SubprocessError) as e:
            logging.error(f"Audio output command failed ({' '.join(args)}): {e}")
            return None
        return result.stdout
