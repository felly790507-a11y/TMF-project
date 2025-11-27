# src/recorder.py
import csv
from pathlib import Path

class TickRecorder:
    def __init__(self, filename: str = 'tick_record.csv'):
        self.path = Path(filename)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = None
        self._writer = None

    def open(self):
        if self._file is None:
            self._file = open(self.path, 'a', newline='', encoding='utf-8')
            self._writer = csv.writer(self._file)

    def record(self, tick: dict):
        self.open()
        self._writer.writerow([tick.get('time'), tick.get('price'), tick.get('volume')])

    def close(self):
        if self._file:
            self._file.close()
            self._file = None
