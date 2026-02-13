import subprocess
import time
import os
import sys


def capture():
    env = dict(os.environ)
    env["RAILWAY_TOKEN"] = ""

    print("Initiating capture...")
    with open("full_login_log.txt", "w", encoding="utf-8") as f:
        p = subprocess.Popen(
            ["railway", "login", "--browserless"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            shell=True,
            env=env,
        )

        # Wait and read
        start = time.time()
        while time.time() - start < 15:
            line = p.stdout.readline()
            if line:
                f.write(line)
                f.flush()
                # Stop if we hit the waiting message
                if "Waiting for login" in line:
                    break
            else:
                time.sleep(0.1)
        p.terminate()
    print("Capture finished.")


if __name__ == "__main__":
    capture()
