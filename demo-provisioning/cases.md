# Demo 案例與預期結果

規格:`specs/sprint-retry.md`(REQ-003、REQ-004)。

| diff | 內容 | 預期 |
| --- | --- | --- |
| 01-full-compliance | 指數退避重試 + 錯誤記錄 + 封鎖 revoked→provisioned | REQ-003 covered、REQ-004 covered |
| 02-missing-backoff | 有重試與錯誤記錄與狀態限制,但沒有 sleep 退避 | REQ-003 missing(缺退避)、REQ-004 covered |
| 03-out-of-spec | 完整實作兩條,另外新增 metrics.py 與 list_devices | 兩條 covered、metrics / list_devices 為 out-of-spec |
| 04-violates-transition | 重試完整,但狀態機仍允許 revoked→provisioned | REQ-003 covered、REQ-004 missing |
| 05-unrelated-change | 只改 docstring | 兩條 missing,docstring 為 out-of-spec 或無影響 |
