"""后台任务框架：Worker-QObject 移入 QThread，结果经信号回传主线程。

UI 卡死的根源是旧版在主线程同步执行检索；所有耗时操作必须经由本模块执行。
"""
from __future__ import annotations

import threading
from typing import Callable, Optional

from PySide6.QtCore import QObject, QThread, Signal, Slot


class Reporter:
    """传给 job 的回调集合：进度与文本消息均以队列信号安全回主线程。"""

    def __init__(self, worker: "Worker"):
        self._worker = worker

    def progress(self, done: int, total: int) -> None:
        self._worker.progress.emit(done, total)

    def message(self, text: str) -> None:
        self._worker.message.emit(text)


# job(reporter, cancel_event) -> 任意结果对象
JobFn = Callable[[Reporter, threading.Event], object]
ProgressCb = Optional[Callable[[int, int], None]]
MessageCb = Optional[Callable[[str], None]]


class Worker(QObject):
    progress = Signal(int, int)
    message = Signal(str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, job: JobFn, parent=None):
        super().__init__(parent)
        self._job = job
        self.cancel_event = threading.Event()

    @Slot()
    def run(self):
        try:
            result = self._job(Reporter(self), self.cancel_event)
        except Exception as err:  # 后台线程兜底，避免异常静默
            self.failed.emit(f"{type(err).__name__}: {err}")
            return
        self.finished.emit(result)


class TaskRunner(QObject):
    """在独立线程执行一个 job；同一 runner 同时只跑一个任务。"""

    busy_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: Optional[QThread] = None
        self._worker: Optional[Worker] = None

    @property
    def busy(self) -> bool:
        return self._thread is not None

    def cancel(self) -> None:
        if self._worker is not None:
            self._worker.cancel_event.set()

    def start(
        self,
        job: JobFn,
        *,
        on_progress: ProgressCb = None,
        on_message: MessageCb = None,
        on_finished: Callable[[object], None],
        on_failed: Callable[[str], None],
    ) -> None:
        if self.busy:
            return
        thread = QThread(self)
        worker = Worker(job)
        worker.moveToThread(thread)
        if on_progress is not None:
            worker.progress.connect(on_progress)
        if on_message is not None:
            worker.message.connect(on_message)
        worker.finished.connect(on_finished)
        worker.failed.connect(on_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.started.connect(worker.run)
        thread.finished.connect(self._on_thread_finished)
        self._thread = thread
        self._worker = worker
        self.busy_changed.emit(True)
        thread.start()

    def _on_thread_finished(self) -> None:
        thread = self.sender()
        if self._worker is not None:
            self._worker.deleteLater()
        if thread is not None:
            thread.deleteLater()
        self._thread = None
        self._worker = None
        self.busy_changed.emit(False)
