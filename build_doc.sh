#!/bin/bash

# Start with fresh API guide
echo "" > API_GUIDE.md

# Process each documentation section
for file in section*.md; do
    # Remove trailing newlines and append content
    sed -e :a -e '/^\n*$/!{$d;N;ba' -e '}' "$file" >> API_GUIDE.md
    # Add two blank lines between sections
    echo -e "\n\n" >> API_GUIDE.md
done

# Remove the last two blank lines added after final section
truncate -s -2 API_GUIDE.md

# Generate table of contents
python bin/create_toc.py 