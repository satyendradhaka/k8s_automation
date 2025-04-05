import subprocess


def runKubectlCommand(args):
    result = subprocess.run(
        ["kubectl"] + args,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()
