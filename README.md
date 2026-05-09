# Venv Package Search

Web app for searching packages in your Python virtual environment. Created by Claude Code.

## Setup

Download the app.py and locate it to your HOME directory. Then modify the following to fit your environment.

```python
VENV_SEARCH_DIRS = [
    os.path.expanduser("~/.venv"),
    os.path.expanduser("~/venv"),
    os.path.expanduser("~/.uvenv"),
]
```

## Run

```shell
~$ python3 app.py
```
Open the web borwser with http://localhost:8765.

## Limitations

Tested only on macOS. Unix-like OS are probably OK. 
