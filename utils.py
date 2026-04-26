import time
import sys
import threading
import itertools

#region I/O Utils
def print_as_orecle(message):
    print(f"Orecle > {message}")


def input_to_orecle():
    print("You > ", end="")
    return input()
#endregion


def start_spinner(message="Thinking"):
    stop_event = threading.Event()
    clear_width = len(message) + 3

    def spin():
        for char in itertools.cycle("|/-\\"):
            if stop_event.is_set():
                break
            sys.stdout.write(f"\r{message} {char}")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * clear_width + "\r")
        sys.stdout.flush()

    thread = threading.Thread(target=spin, daemon=True)
    thread.start()

    class SpinnerHandle:
        def set(self):
            stop_event.set()
            thread.join()

    return SpinnerHandle()
