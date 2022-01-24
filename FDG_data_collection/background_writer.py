import threading
from queue import Queue
from typing import TextIO


class BackgroundTextWriter(threading.Thread):
    def __init__(self, target: TextIO):
        super().__init__(daemon=True)
        self._queue = Queue()
        self._target = target

    def __call__(self, line):
        self._queue.put(line)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()

    def end(self):
        self._queue.join()

    def run(self) -> None:
        while True:
            line = self._queue.get()
            print(line, file=self._target, flush=False)
            self._queue.task_done()
