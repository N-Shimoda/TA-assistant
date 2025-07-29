#!/bin/bash
# Argument check
if [ $# -lt 1 ]; then
  echo "Usage: $0 <ROOT_DIR>"
  exit 1
fi

# Target directory
ROOT_DIR="$1"

# Target file extensions
EXTENSIONS="pdf jpeg jpg png heic docx xlsx pptx"

# Temporary file to record deleted file names
tmpfile=$(mktemp)

# Recursively search for directories named "提出物の添付ファイル"
find "$ROOT_DIR" -type d -name "提出物の添付ファイル" | while read -r dir; do
  for ext in $EXTENSIONS; do
    find "$dir" -maxdepth 1 -type f -name "*.${ext}" | grep -E '\+[0-9]+\.'"$ext"$ | while read -r file; do
      echo "Deleting: $file"
      rm "$file"
      echo "$file" >> "$tmpfile"
    done
  done
done

deleted_count=$(wc -l < "$tmpfile")
rm "$tmpfile"
echo "✅ 合計 $deleted_count 件の複製ファイルを削除しました。"