import time
import datetime as dt
from typing import Optional
from typing import override  # Python 3.12+
from abc import ABC, abstractmethod
from queue import Queue


class BaseClock(ABC):
    @abstractmethod
    def start_point(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def sleep(self) -> None:
        raise NotImplementedError


class IntervalClock(BaseClock):
    """每隔 x 秒觸發一次(x >= 60)"""
    def __init__(self, seconds: float) -> None:
        if seconds < 60:
            raise ValueError("seconds must be >= 60")
        self.seconds = float(seconds)
        self.base_time: Optional[float] = None
        self.nth = 1

    @override
    def start_point(self) -> None:
        self.base_time = time.monotonic()
        self.nth = 1

    @override
    def sleep(self) -> None:
        assert self.base_time is not None, "must call start_point() first"
        # 對齊到 base_time + n*interval，避免累積漂移
        target_mono = self.base_time + self.seconds * self.nth
        delay = target_mono - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        self.nth += 1



class DailyClock(BaseClock):
    """
    每天固定時刻觸發一次。
    - time_list: ["HH:MM", "HH:MM:SS", ...] (長度須小於 20)
    - tz: 整點偏移（小時），例如 +8 → UTC+8
    """
    def __init__(self, time_list: list[str], tz: int = 8) -> None:
        assert time_list, "time_list must not be empty"
        assert len(time_list) <= 20, "len(time_list) must <= 20"

        self.tz = dt.timezone(dt.timedelta(hours=tz))
        self._started = False

        # 1) parse "HH:MM[:SS]" -> datetime.time
        times: list[dt.time] = [self._parse_time(s) for s in time_list]

        # 2) 轉成「今天」對應的 datetime
        today = dt.datetime.now(self.tz).date()
        targets = [dt.datetime.combine(today, t, self.tz) for t in times]

        # 3) 依時間排序，建立 FIFO queue (單調佇列)
        targets.sort()
        q: Queue[dt.datetime] = Queue()
        for d in targets:
            q.put_nowait(d)
        self.time_queue = q

    @override
    def start_point(self) -> None:
        # 僅作為啟動旗標；實際等待邏輯每次都用 "now" 計算
        # 先偷懶，我懶的在寫奇怪的分類方式了
        self._started = True

    @override
    def sleep(self) -> None:
        assert self._started, "must call start_point() first"

        start = time.monotonic()
        while not self.time_queue.empty():
            target = self.time_queue.get_nowait()

            now = dt.datetime.now(self.tz)
            seconds = (target - now).total_seconds()

            # +1 天
            self.time_queue.put_nowait(target + dt.timedelta(days=1))

            # 扣除本函式到目前的計算耗時
            # 避免誤差
            seconds -= (time.monotonic() - start)

            if seconds > 0:
                time.sleep(seconds)
                break
            # 若 seconds <= 0，代表這個目標已過，繼續看佇列下一個

    # --- helpers ---
    def _parse_time(self, s: str) -> dt.time:
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return dt.datetime.strptime(s, fmt).time()
            except ValueError:
                pass
        raise ValueError(f"invalid time string: {s!r}")
