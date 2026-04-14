from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from textwrap import dedent
from zoneinfo import ZoneInfo
import json
import sqlite3
import subprocess
import argparse
import os


AUTOMATION_ID = "daily-product-loop"
AUTOMATION_NAME = "Daily Product Loop"
AUTOMATION_RRULE = "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA,SU;BYHOUR=9;BYMINUTE=0"
AUTOMATION_MODEL = "gpt-5.4"
AUTOMATION_REASONING = "xhigh"
AUTOMATION_EXECUTION_ENVIRONMENT = "local"

LAUNCH_AGENT_LABEL = "com.researchatlas.daily-report"
LAUNCH_AGENT_HOUR = 9
LAUNCH_AGENT_MINUTE = 12


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def shanghai_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Shanghai"))


def quote_toml(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
        .replace('"', '\\"')
    )
    return f'"{escaped}"'


def list_literal(items: list[str]) -> str:
    if not items:
        return "[]"
    return "[" + ", ".join(quote_toml(item) for item in items) + "]"


def build_automation_prompt(project_root: Path) -> str:
    research_skill = Path.home() / ".codex" / "skills" / "research-product-iteration" / "SKILL.md"
    visual_skill = Path.home() / ".codex" / "skills" / "visual-iteration-report" / "SKILL.md"
    return dedent(
        f"""
        Use [{'$'}research-product-iteration]({research_skill}) first, then [{'$'}visual-iteration-report]({visual_skill}) after the markdown report is ready.

        Follow [/Users/yugugaode/Documents/New project/docs/PRODUCT_ITERATION_HARNESS.md]({project_root / 'docs' / 'PRODUCT_ITERATION_HARNESS.md'}) and keep the run small-batch.

        For today's Asia/Shanghai date:
        - prepare or update one dated markdown report under [{project_root / 'reports' / 'product-iterations'}]({project_root / 'reports' / 'product-iterations'})
        - scan official competitor product pages for paper reading and literature discovery products
        - write 3 to 5 concise competitor signals
        - choose at most one low-risk product improvement and implement it only if it is safe
        - run `python3 -m unittest discover -s tests -p 'test_*.py'`
        - run `python3 -m compileall backend frontend tests scripts`
        - render the desktop reading brief so it lands in [/Users/yugugaode/Desktop/Research Atlas 日报](/Users/yugugaode/Desktop/Research Atlas 日报)
        - update `$CODEX_HOME/automations/{AUTOMATION_ID}/memory.md` with the latest focus, what changed, and the next candidate

        Keep user-facing copy product-first. End with exactly one inbox item that tells me what changed and what I should look at next.
        """
    ).strip()


def build_memory_seed() -> str:
    now = shanghai_now().strftime("%Y-%m-%d %H:%M %Z")
    return dedent(
        f"""
        # Daily Product Loop Memory

        - Last setup: {now}
        - Current focus: make the daily product loop reliable in both Codex and the desktop archive.
        - Guardrails:
          - keep one bounded change per run
          - keep public copy product-first
          - prefer readable desktop output over verbose internal notes
        """
    ).strip() + "\n"


def build_launch_wrapper(project_root: Path) -> str:
    return dedent(
        f"""#!/bin/zsh
        set -euo pipefail

        export TZ=Asia/Shanghai
        export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

        PROJECT_ROOT="{project_root}"
        PYTHON_BIN="/usr/bin/python3"
        PREPARE_SCRIPT="$PROJECT_ROOT/scripts/prepare_iteration_report.py"
        RENDER_SCRIPT="$PROJECT_ROOT/scripts/render_iteration_report.py"
        REPORTS_DIR="$PROJECT_ROOT/reports/product-iterations"
        LAUNCH_LOG_DIR="$HOME/Library/Logs/ResearchAtlas"
        LOG_FILE="$LAUNCH_LOG_DIR/daily-report-run.log"
        DESKTOP_DIR="$HOME/Desktop/Research Atlas 日报"
        STATUS_NOTE="$DESKTOP_DIR/launchd-访问说明.txt"
        REPORT_DATE="${{REPORT_DATE_OVERRIDE:-$(date '+%Y-%m-%d')}}"

        mkdir -p "$LAUNCH_LOG_DIR" "$DESKTOP_DIR"

        if [[ ! -r "$PREPARE_SCRIPT" || ! -r "$RENDER_SCRIPT" || ! -w "$REPORTS_DIR" ]]; then
          {{
            echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] launchd cannot access the repo under Documents."
            echo "repo=$PROJECT_ROOT"
          }} >> "$LOG_FILE"
          cat > "$STATUS_NOTE" <<'EOF'
Research Atlas 日报后台同步当前没有拿到项目目录的访问权限。

已确认的现象：
- 系统级 launchd 可以正常触发
- 但它不能读写位于 ~/Documents 下的仓库文件

最直接的解决方法：
1. 把仓库移到一个非受保护目录，比如 ~/Workspace
2. 或者给 /bin/zsh 和 /usr/bin/python3 授予 Full Disk Access
3. 做完后重新运行：
   python3 scripts/install_daily_automation.py

说明：
- Codex 应用内的每日 9 点自动化已经创建完成
- 现在缺的是系统后台进程对 Documents 的访问能力
EOF
          exit 1
        fi

        {{
          echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] start daily report sync for $REPORT_DATE"
          if ! "$PYTHON_BIN" "$PREPARE_SCRIPT" --date "$REPORT_DATE"; then
            cat > "$STATUS_NOTE" <<'EOF'
Research Atlas 日报后台同步已经触发，但系统后台进程当前不能打开项目目录中的日报脚本。

最直接的解决方法：
1. 把仓库移到一个非受保护目录，比如 ~/Workspace
2. 或者给 /bin/zsh 和 /usr/bin/python3 授予 Full Disk Access
3. 做完后重新运行：
   python3 scripts/install_daily_automation.py

说明：
- Codex 应用内的每日 9 点自动化已经创建完成
- 当前受限的是系统后台进程访问 ~/Documents 下的工程文件
EOF
            exit 1
          fi
          if ! "$PYTHON_BIN" "$RENDER_SCRIPT" --date "$REPORT_DATE"; then
            cat > "$STATUS_NOTE" <<'EOF'
Research Atlas 日报的桌面渲染步骤已触发，但系统后台进程当前不能完成项目文件的读取或写入。

建议处理方式：
1. 把仓库移到一个非受保护目录，比如 ~/Workspace
2. 或者给 /bin/zsh 和 /usr/bin/python3 授予 Full Disk Access
3. 做完后重新运行：
   python3 scripts/install_daily_automation.py

说明：
- Codex 应用内的每日 9 点自动化已经创建完成
- 当前受限的是系统后台进程访问 ~/Documents 下的工程文件
EOF
            exit 1
          fi
          echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] finished daily report sync for $REPORT_DATE"
        }} >> "$LOG_FILE" 2>&1

        rm -f "$STATUS_NOTE"
        """
    ).strip() + "\n"


@dataclass
class AutomationRecord:
    created_at: int
    updated_at: int
    next_run_at: int
    last_run_at: int | None


def next_run_ms(now: datetime) -> int:
    candidate = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    return int(candidate.timestamp() * 1000)


def ensure_automation_files(project_root: Path) -> tuple[Path, Path]:
    home = codex_home()
    automation_dir = home / "automations" / AUTOMATION_ID
    automation_dir.mkdir(parents=True, exist_ok=True)

    now = shanghai_now()
    timestamp_ms = int(now.timestamp() * 1000)
    automation_toml = automation_dir / "automation.toml"
    memory_md = automation_dir / "memory.md"
    launch_wrapper = automation_dir / "run_daily_report.sh"

    toml_lines = [
        "version = 1",
        f"id = {quote_toml(AUTOMATION_ID)}",
        'kind = "cron"',
        f"name = {quote_toml(AUTOMATION_NAME)}",
        f"prompt = {quote_toml(build_automation_prompt(project_root))}",
        'status = "ACTIVE"',
        f"rrule = {quote_toml(AUTOMATION_RRULE)}",
        f"model = {quote_toml(AUTOMATION_MODEL)}",
        f"reasoning_effort = {quote_toml(AUTOMATION_REASONING)}",
        f"execution_environment = {quote_toml(AUTOMATION_EXECUTION_ENVIRONMENT)}",
        f"cwds = {list_literal([str(project_root)])}",
        f"created_at = {timestamp_ms}",
        f"updated_at = {timestamp_ms}",
        "",
    ]
    automation_toml.write_text("\n".join(toml_lines), encoding="utf-8")
    if not memory_md.exists():
        memory_md.write_text(build_memory_seed(), encoding="utf-8")
    launch_wrapper.write_text(build_launch_wrapper(project_root), encoding="utf-8")
    launch_wrapper.chmod(0o755)

    return automation_toml, memory_md


def ensure_automation_db(project_root: Path) -> AutomationRecord:
    database_path = codex_home() / "sqlite" / "codex-dev.db"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    now = shanghai_now()
    now_ms = int(now.timestamp() * 1000)
    next_run_at = next_run_ms(now)
    prompt = build_automation_prompt(project_root)
    cwds = json.dumps([str(project_root)], ensure_ascii=False)

    connection = sqlite3.connect(database_path)
    try:
        current = connection.execute(
            "SELECT created_at, last_run_at FROM automations WHERE id = ?",
            (AUTOMATION_ID,),
        ).fetchone()
        created_at = int(current[0]) if current else now_ms
        last_run_at = int(current[1]) if current and current[1] is not None else None
        connection.execute(
            """
            INSERT OR REPLACE INTO automations (
                id, name, prompt, status, next_run_at, last_run_at,
                cwds, rrule, model, reasoning_effort, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                AUTOMATION_ID,
                AUTOMATION_NAME,
                prompt,
                "ACTIVE",
                next_run_at,
                last_run_at,
                cwds,
                AUTOMATION_RRULE,
                AUTOMATION_MODEL,
                AUTOMATION_REASONING,
                created_at,
                now_ms,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    return AutomationRecord(
        created_at=created_at,
        updated_at=now_ms,
        next_run_at=next_run_at,
        last_run_at=last_run_at,
    )


def build_launch_agent_plist(project_root: Path) -> str:
    wrapper_path = codex_home() / "automations" / AUTOMATION_ID / "run_daily_report.sh"
    launch_log_dir = Path.home() / "Library" / "Logs" / "ResearchAtlas"
    stdout_path = launch_log_dir / "daily-report.out.log"
    stderr_path = launch_log_dir / "daily-report.err.log"
    return dedent(
        f"""<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
          <dict>
            <key>Label</key>
            <string>{LAUNCH_AGENT_LABEL}</string>
            <key>ProgramArguments</key>
            <array>
              <string>/bin/zsh</string>
              <string>{wrapper_path}</string>
            </array>
            <key>EnvironmentVariables</key>
            <dict>
              <key>PATH</key>
              <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
              <key>TZ</key>
              <string>Asia/Shanghai</string>
            </dict>
            <key>StartCalendarInterval</key>
            <dict>
              <key>Hour</key>
              <integer>{LAUNCH_AGENT_HOUR}</integer>
              <key>Minute</key>
              <integer>{LAUNCH_AGENT_MINUTE}</integer>
            </dict>
            <key>RunAtLoad</key>
            <false/>
            <key>StandardOutPath</key>
            <string>{stdout_path}</string>
            <key>StandardErrorPath</key>
            <string>{stderr_path}</string>
          </dict>
        </plist>
        """
    ).strip() + "\n"


def install_launch_agent(project_root: Path, run_now: bool) -> Path:
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    launch_agents_dir.mkdir(parents=True, exist_ok=True)
    log_dir = Path.home() / "Library" / "Logs" / "ResearchAtlas"
    log_dir.mkdir(parents=True, exist_ok=True)

    plist_path = launch_agents_dir / f"{LAUNCH_AGENT_LABEL}.plist"
    plist_path.write_text(build_launch_agent_plist(project_root), encoding="utf-8")

    uid = str(os.getuid())
    subprocess.run(["/bin/launchctl", "bootout", f"gui/{uid}", str(plist_path)], check=False)
    subprocess.run(["/bin/launchctl", "bootstrap", f"gui/{uid}", str(plist_path)], check=True)
    subprocess.run(["/bin/launchctl", "enable", f"gui/{uid}/{LAUNCH_AGENT_LABEL}"], check=False)
    if run_now:
        subprocess.run(["/bin/launchctl", "kickstart", "-k", f"gui/{uid}/{LAUNCH_AGENT_LABEL}"], check=True)

    return plist_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Install the daily Codex automation and desktop report scheduler.")
    parser.add_argument("--run-now", action="store_true", help="Trigger the desktop report sync once after installation.")
    args = parser.parse_args()

    project_root = repo_root()
    ensure_automation_files(project_root)
    record = ensure_automation_db(project_root)
    plist_path = install_launch_agent(project_root, run_now=args.run_now)

    print(f"automation_id={AUTOMATION_ID}")
    print(f"automation_next_run_at={record.next_run_at}")
    print(f"launch_agent={plist_path}")


if __name__ == "__main__":
    main()
