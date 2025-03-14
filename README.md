# LiveKit Notes

These are my notes for migrating to LiveKit [Agents 1.0](https://github.com/livekit/agents/tree/dev-1.0) API.

## API Guide and Docs

Guide is broken down into chapters and are found in `./sections/NNN_*`. A composite document is generated from the individual chapters.

### Building `API_GUIDE.md`

**Setup Virtual Environment**
```
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

pip install -r bin/requirements.txt
```

**Build API_GUIDE.md**

Concatenate all chapters into a common file and generate a table of contents.

```
source .venv/bin/activate

./bin/build_doc.sh && python bin/create_toc.py
```

## Examples

### Usage

**Setup Virtual Environment**
```
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

pip install -r bin/requirements.txt
```

**Run Example**

```
source .venv/bin/activate

python basic_example/EXAMPLE.py dev
```

## Cursor Rules

Cursor projects to have custom [rules](https://docs.cursor.com/context/rules-for-ai#project-rules-recommended). 

To use copy cursor/rules/* to your project root directory `.cusor/rules/*`

