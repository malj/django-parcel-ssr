import time
from io import BytesIO
from subprocess import Popen


def wait_for_signal(stream: BytesIO, signal: str) -> None:
    while True:
        raw_text = stream.readline().strip(b' ')
        if raw_text:
            text = raw_text.decode('utf-8')[:-1]
            if text == signal:
                break
            else:
                print(text)
        else:
            time.sleep(0.1)


def read_output(process: Popen) -> None:
    stdout, stderr = process.communicate()
    print(stdout.decode('utf-8'))
    if stderr:
        raise EnvironmentError(stderr.decode('utf-8'))
