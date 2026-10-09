"""LLM 呼叫。預設本地 Ollama。

實驗用:SPEC2PATCH_BACKEND=claude-cli 改走本機 `claude -p`(使用 Claude 訂閱額度,
不需要 API key)。僅供比較模型能力,不是正式的後端切換機制。
"""
import json
import os
import subprocess
import tempfile
import urllib.request

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
BACKEND = os.environ.get("SPEC2PATCH_BACKEND", "ollama")
MODEL = os.environ.get("SPEC2PATCH_MODEL", "llama3.1:8b")


def _claude_cli(system: str, user: str, timeout: int) -> str:
    cmd = ["claude", "-p", "--output-format", "json", "--tools", "",
           "--no-session-persistence", "--system-prompt", system]
    if os.environ.get("SPEC2PATCH_MODEL"):
        cmd += ["--model", os.environ["SPEC2PATCH_MODEL"]]
    # 在空目錄執行,避免載入任何專案的 CLAUDE.md / 設定
    with tempfile.TemporaryDirectory() as cwd:
        out = subprocess.run(cmd, input=user, capture_output=True, text=True,
                             timeout=timeout, cwd=cwd)
    data = json.loads(out.stdout)
    if data.get("is_error"):
        raise RuntimeError(data.get("result", "claude cli error"))
    return data["result"]


def chat_json(system: str, user: str, timeout: int = 300) -> str:
    if BACKEND == "claude-cli":
        return _claude_cli(system, user, timeout)
    body = {
        "model": MODEL,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())["message"]["content"]
