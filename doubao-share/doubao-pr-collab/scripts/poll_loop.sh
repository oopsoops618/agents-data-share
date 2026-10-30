#!/bin/bash
# PR 留言板轮询哨兵：在定时任务执行窗口内每 2 分钟轮询一次。
# 用法: poll_loop.sh <owner/repo> <pr_num> <token_file> [窗口秒数，默认 3000≈50分钟]
# 退出码: 7=终止(PR关闭/[定稿]) 8=有新任务(打印编号) 9=脚本失败 0=窗口安静结束
set -u

OWNER_REPO="$1"; PR_NUM="$2"; TOKEN_FILE="$3"; WINDOW="${4:-3000}"
TOKEN=$(cat "$TOKEN_FILE")
API="https://api.github.com/repos/$OWNER_REPO"
DIR="$(cd "$(dirname "$0")" && pwd)"
END=$((SECONDS + WINDOW))
TICK=0

while [ $SECONDS -lt $END ]; do
  TICK=$((TICK + 1))

  # 1) PR 状态
  STATE=$(curl -s -m 20 -H "Authorization: Bearer $TOKEN" "$API/pulls/$PR_NUM" \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('state',''))" 2>/dev/null)
  if [ "$STATE" != "open" ]; then
    echo "[$(date '+%H:%M:%S')] tick$TICK PR 已关闭(state=$STATE) → 终止"
    exit 7
  fi

  # 2) 评论解析 + 去重
  OUT=$(python3 "$DIR/find_tasks.py" "$OWNER_REPO" "$PR_NUM" --token-file "$TOKEN_FILE" 2>/tmp/doubao_poll_err.txt)
  RC=$?
  if [ "$RC" -ne 0 ]; then
    echo "[$(date '+%H:%M:%S')] tick$TICK find_tasks 失败: $(cat /tmp/doubao_poll_err.txt)"
    exit 9
  fi
  if grep -q 'FINAL' /tmp/doubao_poll_err.txt; then
    echo "[$(date '+%H:%M:%S')] tick$TICK 发现[定稿] → 终止"
    exit 7
  fi
  if [ "$OUT" != "NONE" ] && [ -n "$OUT" ]; then
    echo "[$(date '+%H:%M:%S')] tick$TICK 新任务:"
    echo "$OUT"
    exit 8
  fi

  echo "[$(date '+%H:%M:%S')] tick$TICK 无新任务"
  sleep 120
done

echo "[$(date '+%H:%M:%S')] 窗口结束，安静退出"
exit 0
