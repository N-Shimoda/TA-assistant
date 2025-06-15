#!/bin/bash

# 引数チェック
if [ $# -lt 1 ]; then
  echo "Usage: $0 <ROOT_DIR>"
  exit 1
fi

# 対象ディレクトリ
ROOT_DIR="$1"

# 対象拡張子
EXTENSIONS="pdf jpeg jpg png docx xlsx pptx"

# 削除したファイル数カウント
count=0

# "提出物の添付ファイル" ディレクトリを再帰的に検索
find "$ROOT_DIR" -type d -name "提出物の添付ファイル" | while read -r dir; do
  for ext in $EXTENSIONS; do
    # +数字が含まれるファイルをgrepでフィルタ
    find "$dir" -maxdepth 1 -type f -name "*.${ext}" | grep -E '\+[0-9]+\.'"$ext"$ | while read -r file; do
      echo "Deleting: $file"
      rm "$file"
      count=$((count + 1))
    done
  done
done

echo "✅ 合計 $count 件の複製ファイルを削除しました。"