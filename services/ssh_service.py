import subprocess
import os
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


class SshService:
    @staticmethod
    def execute_command_on(
        address: str, username: str, password: str, command: str
    ) -> bool:
        console: Console = Console()
        try:
            if ":" in address:
                address, port = address.split(":")
            else:
                port = 22

            identity_file = os.path.expanduser("~/.ssh/id_rsa")

            ssh_command = [
                "sshpass",
                "-p",
                password,
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-i",
                identity_file,
                f"{username}@{address}",
                "-p",
                str(port),
                command,
            ]

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task_id = progress.add_task(
                    f"Executing command on {address}...", start=True
                )

                process = subprocess.Popen(
                    ssh_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=True,
                )

                stdout, stderr = process.communicate()

                progress.update(task_id, description=f"Command executed on {address}")
                progress.stop_task(task_id)

            if process.returncode == 0:
                console.print(
                    f"[green]Command executed successfully on {address}[/green]"
                )
                return True
            else:
                console.print(
                    f"[red]Failed to execute command on {address}: {stderr}[/red]"
                )
                return False
        except Exception as e:
            console.print(f"[red]Failed to execute command on {address}: {e}[/red]")
            return False
