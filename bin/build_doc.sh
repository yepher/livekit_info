#!/bin/bash

# Change to project root directory (one level up from script location)
cd "$(dirname "$0")/.." || exit 1

rm -f API_GUIDE.md

# Start fresh with do_not_edit.md
cat do_not_edit.md > API_GUIDE.md

# Add separator and TOC placeholder
# echo -e "\n\n[_TOC_]\n\n---\n" >> API_GUIDE.md

# Process numbered sections in order
while IFS= read -r file; do
    echo "Appending: $file"
    # Append section content with preserved newlines
    cat "$file" >> API_GUIDE.md
    # Add two blank lines between sections
    echo -e "\n\n" >> API_GUIDE.md
done < <(ls sections/[0-9][0-9][0-9]_*.md | sort -V)

# Trim final newlines and generate TOC
truncate -s -2 API_GUIDE.md
python bin/create_toc.py


