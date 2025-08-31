# DC – Push/Process Helper

一個極簡、可擴充的**訊息推送輔助套件**。
你只需要撰寫「任務邏輯」函式（回傳 Discord Webhook payload），再選一個排程時鐘（Clock），就能跑起長駐的推送流程。

> 最終部署使用 **Docker**；進程守護（重啟/生存監控）交給容器平台處理。

## 目錄結構

```
dc/
├─ main.py                 # 入口：寫入你的邏輯、組裝 Clock → ProcessUnit → run()
├─ services/
│  ├─ clock.py             # 時鐘抽象：BaseClock、IntervalClock、DailyClock …（內含 parsing/sleep 邏輯）
│  ├─ process.py           # ProcessUnit：封裝 clock + 任務 callback，並負責訊息送出
│  └─ __init__.py
├─ bot.json                # Webhook 目標清單（陣列字串）
└─ README.md               # 本文件
```

## 系統需求

* Python **3.12+**（`main.py` 會強制檢查版本）
* 依賴：`requests`（用於呼叫 Discord Webhook）
* 可連網（對 Discord 域名）

## 快速開始（本機）

1. 在 `bot.json` 放入**你的** Discord Webhook（可複數）：

```json
[
  "https://discord.com/api/webhooks/xxxx/xxxx"
]
```

2. 在 `main.py` 內撰寫你的邏輯與時鐘（示意）：

```python
from typing import Dict, Any
from services.clock import IntervalClock, DailyClock
from services.process import ProcessUnit

def my_job() -> Dict[str, Any]:
    # 需符合 Discord Webhook payload 規範的最小結構
    return {
        "content": "hello world"
    }

def main():
    # 兩種 clock 例子：擇一啟用
    # 1) 每 60 秒觸發
    clock = IntervalClock(60)

    # 2) 每天固定時刻觸發（24h 制，支援 HH:MM 或 HH:MM:SS）
    # clock = DailyClock(["11:15", "22:00:15"])

    p = ProcessUnit(
        my_job,   # 你的任務 callback（無參數、回傳 dict）
        clock     # 選定時鐘
    )
    p.run()      # 進入長駐循環 -> 搭配 docker 的邏輯，可以外部管理它

if __name__ == "__main__":
    main()
```

> 概念： 你可以自己製作 callback function （`my_job`），只要符合堆定<br>
某種程度來說，可擴展空間非常大

3. 執行

```bash
cd dc
python3 main.py
```

## 核心概念

### 1 任務函式（你的邏輯）

* 介面：**無參數 → 回傳 `Dict[str, Any]`**
* 回傳物件會直接送往 `bot.json` 裡每個 webhook：

  * 支援欄位：`content`、`embeds`、…（遵循 Discord Webhook API）
* 失敗會拋例外（`requests` 的 `raise_for_status()`），由外層/容器處理重試策略(你需要自己想）

### 2 Clock（排程時鐘）

已內建：

* `IntervalClock(seconds: int)`：每 N 秒觸發
* `DailyClock(times: list[str])`：每天指定時刻觸發（字串支援 `HH:MM` 或 `HH:MM:SS`）

  * 內部已處理今天已過時刻→排到明天；內建 queue 決定下一個醒來點；sleep 使用 OS 計時器

> 註：`services/clock.py` 已封裝 `BaseClock` 抽象、sleep 計時、時間字串解析等邏輯。若你要新規則（例如 Weekly），可在同檔加上新時鐘類別並實作 `start_point()` / `sleep()`。

### 3) ProcessUnit（執行器）

* `ProcessUnit(callback, clock)`：主循環如下

  1. `clock.start_point()` 計算初始基準
  2. 進入無限循環：`clock.sleep()` → 執行 `callback()` → 將回傳 payload 逐一 POST 到 `bot.json` 內 webhook
* Webhook 送出點在 `services/process.py`，以 `requests.post(json=...)` 實做，**逐一重試交由容器層面或外部策略**。

## 設定：`bot.json`

* 型別：`list[str]`
* 每個元素是一個 Discord Webhook URL
* 範例：

```json
[
  "https://discord.com/api/webhooks/xxxx/xxxx",
  "https://discord.com/api/webhooks/yyyy/yyyy"
]
```

> 在 Docker 部署時，建議「掛載檔案」或密鑰管理注入該檔。

## 使用 docker
透過 docker 容器管理，具有以下優勢：
1. 環境隔離、穩定
2. 可以各自 stop/start 而不需要撰寫複雜的程式管理 process
