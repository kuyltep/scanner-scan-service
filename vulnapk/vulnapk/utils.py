import sys
import threading


class ProgressBarManager:
    bars: dict[str, dict[str, int]]
    lock: threading.Lock

    def __init__(self):
        self.lock = threading.Lock()
        self.bars = {}

    def create_progress_bar(self, name: str, total: int, bar_length: int = 40) -> None:
        with self.lock:
            self.bars[name] = {"current": 0, "total": total, "bar_length": bar_length}

    def update_progress_bar(self, name: str, current: int) -> None:
        with self.lock:
            if name in self.bars:
                self.bars[name]["current"] = current
                self._display_progress_bar(name)

    def _display_progress_bar(self, name: str) -> None:
        bar_info = self.bars[name]
        current = bar_info["current"]
        total = bar_info["total"]
        bar_length = bar_info["bar_length"]

        progress = current / total
        block = int(bar_length * progress)
        bar = "=" * block + "-" * (bar_length - block)
        percentage = progress * 100
        sys.stdout.write(f"\r{name}: [{bar}] {percentage:.2f}% ({current}/{total})")
        sys.stdout.flush()

        if current == total:
            print()


# Example usage:
# manager = ProgressBarManager()
# manager.create_progress_bar('bar1', 100)
# manager.update_progress_bar('bar1', 50)
