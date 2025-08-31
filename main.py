import sys

# e.g. sys.version_info(major=3, minor=12, micro=2, releaselevel='final', serial=0)
if sys.version_info < (3, 12):
    raise RuntimeError("Python 3.12 or higher is required.")

import datetime
from typing import Dict, Any

def dummy() -> Dict[str, Any]:
    # see: https://discord.com/developers/docs/resources/webhook#execute-webhook
    return {
        "content": "y = ax + b",
        "embeds": [
            {
            "title": "時間測試",
            "description": "主內容...",
            "color": 5814783,
            "fields": [
                {
                    "name": "field1",
                    "value": f"自動化時間：{datetime.datetime.now().strftime("%d/%m/%y - %H:%M:%S")} UTF +8"
                }
            ],
            "footer": {
                    "text": "來自自動化軟體",
                    "icon_url": "https://media.discordapp.net/attachments/1409722406498734132/1411631337374486588/images.jpg?ex=68b55ba1&is=68b40a21&hm=5352703c73712f2cd9494f87a53c72db289b7963b9da7c098c2e51fd2e991ea7&=&format=webp"
                }
            }
        ],
        "username": "Bot♫",
        "avatar_url": "https://media.discordapp.net/attachments/1409722406498734132/1411631337374486588/images.jpg?ex=68b55ba1&is=68b40a21&hm=5352703c73712f2cd9494f87a53c72db289b7963b9da7c098c2e51fd2e991ea7&=&format=webp",
        "attachments": [],
        "flags": 4096
    }

from services.clock import *
from services.process import *

def main():
    # set clock
    clock = IntervalClock(60)
    # clock = DailyClock(
    #     ["11:15", "22:00:15"], # 每天的 11:15, 22:00:15 觸發
    # )

    # make process
    p = ProcessUnit(
        dummy,  # function callback -> 你的任務
        clock   # clock you set
    )

    # 開始執行
    p.run()

if __name__ == "__main__":
    main()