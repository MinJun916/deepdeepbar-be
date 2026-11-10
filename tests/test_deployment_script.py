import os
import re
import subprocess
import tempfile
import textwrap
from pathlib import Path
from unittest import TestCase


class DeploymentScriptTests(TestCase):
    def run_deploy(self, fail_migration: bool):
        workflow = Path(__file__).resolve().parents[1] / ".github/workflows/deploy.yml"
        script = textwrap.dedent(workflow.read_text().split("script: |\n", 1)[1])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = script.replace("${{ secrets.PROJECT_PATH }}", directory)
            script = re.sub(r"\$\{\{[^}]+\}\}", "test", script)
            docker = root / "docker"
            docker.write_text(
                "#!/bin/sh\n"
                'echo "$*" >> "$DEPLOY_CHECK_LOG"\n'
                'if [ "$1 $2" = "compose run" ] && [ "$FAIL_MIGRATION" = 1 ]; then\n'
                "  exit 23\n"
                "fi\n"
            )
            docker.chmod(0o700)
            log = root / "commands.log"
            result = subprocess.run(
                ["bash", "-c", script],
                env={
                    **os.environ,
                    "PATH": f"{directory}:/usr/bin:/bin",
                    "DEPLOY_CHECK_LOG": str(log),
                    "FAIL_MIGRATION": "1" if fail_migration else "0",
                },
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode, log.read_text().splitlines()

    def test_migration_precedes_service_replacement(self):
        code, commands = self.run_deploy(False)
        self.assertEqual(code, 0)
        migration = "compose run --rm --no-deps -T deepdeepbar-be alembic upgrade head"
        replacement = "compose up -d --force-recreate deepdeepbar-be"
        self.assertLess(commands.index(migration), commands.index(replacement))

    def test_migration_failure_keeps_running_service(self):
        code, commands = self.run_deploy(True)
        self.assertEqual(code, 23)
        self.assertFalse(any(command.startswith("compose up ") for command in commands))
        self.assertFalse(
            any(command.startswith("image prune ") for command in commands)
        )
