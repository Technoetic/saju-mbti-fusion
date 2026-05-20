#!/bin/bash
# 다른 PC 첫 실행 시: .claude/commands/ 복원 (vault 백업 → .claude/)
# 사용법: bash bootstrap-claude-commands.sh
# 의무: vault/ 가 본 PC에 동기화되어 있어야 함 (Obsidian Sync)

set -e

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

if [ ! -d "vault/templates" ]; then
  echo "❌ vault/templates/ 부재 — Obsidian Sync 또는 별도 vault 동기화 의무"
  echo "   본 스크립트는 vault 백업 사본을 .claude/commands/로 복원"
  exit 1
fi

mkdir -p .claude/commands/flyio

# 백업 사본 → .claude/commands/ 복원
RESTORE_COUNT=0
for backup in vault/templates/SLASH_COMMAND_*.md; do
  [ -f "$backup" ] || continue
  basename=$(basename "$backup")
  # SLASH_COMMAND_onboard.md → onboard.md
  # SLASH_COMMAND_flyio_index.md → flyio/index.md
  name=${basename#SLASH_COMMAND_}
  name=${name%.md}

  case "$name" in
    flyio_*)
      sub=${name#flyio_}
      target=".claude/commands/flyio/${sub}.md"
      ;;
    *)
      target=".claude/commands/${name}.md"
      ;;
  esac

  cp "$backup" "$target"
  echo "✅ $backup → $target"
  RESTORE_COUNT=$((RESTORE_COUNT + 1))
done

echo ""
echo "복원 완료: ${RESTORE_COUNT} 파일"
echo "Claude Code 재시작 후 /flyio 사용 가능 (인자 없이 → 부트스트랩 자동 수행)"
