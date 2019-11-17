import subprocess


def action_object(name, arglst, url, content, variables, log):
    log.debug("{} running: '{}'".format(name, arglst[0]))
    log.debug("\twith args: {}".format(", ".join(arglst[1:])))

    try:
        proc = subprocess.run(
            arglst, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except FileNotFoundError as excpt:
        return {"return_code": 127, "stdout": "", "stderr": "", "error": str(excpt)}

    return {
        "return_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "error": "",
    }
