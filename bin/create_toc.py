import re
from pathlib import Path

def generate_toc(md_content):
    toc = []
    in_code_block = False
    for line in md_content.split('\n'):
        # Skip code blocks
        if line.startswith(('```', '~~~')):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
            
        # Only match proper markdown headers (must have space after #)
        match = re.match(r'^(#+)\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            # Convert title to anchor link
            anchor = re.sub(r'[^\w\s-]', '', title).lower()
            anchor = re.sub(r'\s+', '-', anchor)
            # Create TOC entry with proper indentation
            indent = '  ' * (level - 1)
            toc.append(f'{indent}- [{title}](#{anchor})')
    return '\n'.join(toc)

def update_api_guide():
    path = Path('API_GUIDE.md')
    content = path.read_text()
    
    if '[_TOC_]' not in content:
        print("No TOC placeholder found")
        return

    # Generate new TOC and replace placeholder
    new_toc = generate_toc(content)
    updated_content = content.replace('[_TOC_]', new_toc)
    
    # Write back to file
    path.write_text(updated_content)
    print(f"Updated TOC in {path}")

if __name__ == '__main__':
    update_api_guide() 