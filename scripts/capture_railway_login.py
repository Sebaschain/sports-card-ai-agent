import subprocess
import time
import os


def capture_login():
    print("Starting railway login --browserless (interactive mode)...")

    # We use a simple subprocess and try to read from it.
    # On Windows, we might need to set creationflags to simulate a console
    process = subprocess.Popen(
        ["railway", "login", "--browserless"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
    )

    # Note: CREATE_NEW_CONSOLE might make it hard to read stdout here.
    # Let's try without it first but with shell=True and stdin redirected.

    process = subprocess.Popen(
        ["railway", "login", "--browserless"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
        text=True,
        bufsize=1,
        shell=True,
    )

    start_time = time.time()
    all_output = ""

    while time.time() - start_time < 20:
        line = process.stdout.readline()
        if line:
            print(f"Captured: {line.strip()}")
            all_output += line
            if "Waiting for login" in line or "pairing code" in line.lower():
                # Give it a bit more time to print the code
                time.sleep(2)
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    all_output += line
                break
        else:
            time.sleep(0.5)

    print("\n--- FULL CAPTURED OUTPUT ---")
    print(all_output)
    print("--- END ---")
    process.terminate()


if __name__ == "__main__":
    capture_login()
