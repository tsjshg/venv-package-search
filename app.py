#!/usr/bin/env python3
"""Venv Package Search — local web app to search packages across virtual environments."""

import glob
import json
import os
import re
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

VENV_SEARCH_DIRS = [
    os.path.expanduser("~/.venv"),
    os.path.expanduser("~/venv"),
    os.path.expanduser("~/.uvenv"),
]

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Venv Package Search</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #0f172a;
    color: #e2e8f0;
    min-height: 100vh;
    padding: 2rem 1rem;
  }
  h1 {
    text-align: center;
    font-size: 1.8rem;
    font-weight: 700;
    color: #a78bfa;
    margin-bottom: 0.25rem;
  }
  .subtitle {
    text-align: center;
    color: #64748b;
    font-size: 0.9rem;
    margin-bottom: 2rem;
  }
  .search-wrap {
    max-width: 640px;
    margin: 0 auto 2rem;
    position: relative;
  }
  input[type="text"] {
    width: 100%;
    padding: 0.85rem 1rem 0.85rem 3rem;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    color: #e2e8f0;
    font-size: 1.05rem;
    outline: none;
    transition: border-color 0.2s;
  }
  input[type="text"]:focus { border-color: #a78bfa; }
  input[type="text"]::placeholder { color: #475569; }
  .search-icon {
    position: absolute;
    left: 1rem;
    top: 50%;
    transform: translateY(-50%);
    color: #475569;
    font-size: 1.1rem;
    pointer-events: none;
  }
  #status {
    text-align: center;
    color: #64748b;
    font-size: 0.85rem;
    margin-bottom: 1.5rem;
    min-height: 1.2em;
  }
  #status.loading { color: #a78bfa; }
  #status.found { color: #34d399; }
  #status.empty { color: #f87171; }
  .results {
    max-width: 900px;
    margin: 0 auto;
    display: grid;
    gap: 0.75rem;
  }
  .card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    gap: 0.5rem;
  }
  .card:hover { border-color: #a78bfa44; }
  .venv-name {
    font-weight: 600;
    font-size: 1rem;
    color: #c4b5fd;
  }
  .badges {
    display: flex;
    gap: 0.4rem;
    align-items: center;
    flex-wrap: wrap;
    justify-content: flex-end;
  }
  .pkg-version {
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 0.85rem;
    background: #312e81;
    color: #a5b4fc;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    white-space: nowrap;
  }
  .py-version {
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 0.78rem;
    background: #14532d;
    color: #86efac;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    white-space: nowrap;
  }
  .venv-path {
    font-size: 0.78rem;
    color: #94a3b8;
    font-family: "SF Mono", "Fira Code", monospace;
    grid-column: 1 / -1;
    margin-top: 0.15rem;
  }
  .intro {
    text-align: center;
    color: #334155;
    margin-top: 4rem;
    font-size: 0.95rem;
  }
  .intro span { font-size: 2rem; display: block; margin-bottom: 0.5rem; }
</style>
</head>
<body>
<h1>Venv Package Search</h1>
<p class="subtitle">Search packages across all your Python virtual environments</p>

<div class="search-wrap">
  <span class="search-icon">&#128269;</span>
  <input type="text" id="q" placeholder="Type a package name, e.g. numpy, torch, pandas..." autofocus>
</div>
<div id="status"></div>
<div class="results" id="results">
  <div class="intro"><span>&#128013;</span>Start typing to search across your venvs</div>
</div>

<script>
const input = document.getElementById('q');
const status = document.getElementById('status');
const results = document.getElementById('results');
let timer;

function setStatus(msg, cls) {
  status.textContent = msg;
  status.className = cls || '';
}

function render(data, query) {
  if (!query) {
    results.innerHTML = '<div class="intro"><span>&#128013;</span>Start typing to search across your venvs</div>';
    setStatus('');
    return;
  }
  if (!data.length) {
    results.innerHTML = '';
    setStatus('No virtual environments contain "' + query + '"', 'empty');
    return;
  }
  setStatus('Found in ' + data.length + ' virtual environment' + (data.length > 1 ? 's' : ''), 'found');
  results.innerHTML = data.map(r => `
    <div class="card">
      <span class="venv-name">${esc(r.venv)}</span>
      <span class="badges">
        <span class="pkg-version">${esc(r.version)}</span>
        <span class="py-version">py ${esc(r.python)}</span>
      </span>
      <span class="venv-path">${esc(r.path)}</span>
    </div>`).join('');
}

function esc(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

async function search(q) {
  if (!q.trim()) { render([], ''); return; }
  setStatus('Searching...', 'loading');
  results.innerHTML = '';
  try {
    const resp = await fetch('/api/search?q=' + encodeURIComponent(q));
    const data = await resp.json();
    render(data, q);
  } catch(e) {
    setStatus('Error: ' + e.message, 'empty');
  }
}

input.addEventListener('input', () => {
  clearTimeout(timer);
  timer = setTimeout(() => search(input.value), 250);
});
</script>
</body>
</html>
"""


def find_venvs():
    """Return list of (name, base_path) for all detected virtual environments."""
    venvs = []
    for search_dir in VENV_SEARCH_DIRS:
        if not os.path.isdir(search_dir):
            continue
        for entry in sorted(os.scandir(search_dir), key=lambda e: e.name):
            if entry.is_dir() and os.path.isdir(os.path.join(entry.path, "lib")):
                venvs.append((entry.name, entry.path, search_dir))
    return venvs


def get_python_version(venv_path):
    """Read Python version from pyvenv.cfg, fallback to lib dir name."""
    cfg = os.path.join(venv_path, "pyvenv.cfg")
    if os.path.isfile(cfg):
        with open(cfg) as f:
            for line in f:
                if line.startswith("version"):
                    return line.split("=", 1)[1].strip()
    lib_dir = os.path.join(venv_path, "lib")
    if os.path.isdir(lib_dir):
        for name in sorted(os.listdir(lib_dir), reverse=True):
            if name.startswith("python"):
                return name[len("python"):]
    return "?"


def get_site_packages(venv_path):
    """Return the site-packages path inside a venv, or None."""
    lib_dir = os.path.join(venv_path, "lib")
    if not os.path.isdir(lib_dir):
        return None
    for pyver in sorted(os.listdir(lib_dir), reverse=True):
        sp = os.path.join(lib_dir, pyver, "site-packages")
        if os.path.isdir(sp):
            return sp
    return None


def load_packages():
    """Build index: {normalized_pkg_name: [{venv, version, path}]}"""
    index = {}
    venvs = find_venvs()
    for venv_name, venv_path, parent_dir in venvs:
        sp = get_site_packages(venv_path)
        if not sp:
            continue
        py_version = get_python_version(venv_path)
        for entry in os.scandir(sp):
            m = re.match(r"^(.+?)-([^-]+)\.dist-info$", entry.name)
            if m and entry.is_dir():
                pkg = m.group(1).lower().replace("-", "_").replace(".", "_")
                version = m.group(2)
                display_name = m.group(1)
                index.setdefault(pkg, []).append({
                    "venv": venv_name,
                    "version": version,
                    "path": venv_path,
                    "display": display_name,
                    "python": py_version,
                })
    return index


class Handler(BaseHTTPRequestHandler):
    index = {}

    def log_message(self, fmt, *args):
        pass  # suppress default access log

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/search":
            params = urllib.parse.parse_qs(parsed.query)
            q = params.get("q", [""])[0].strip().lower().replace("-", "_").replace(".", "_")
            results = []
            for pkg_key, entries in self.index.items():
                if q and q in pkg_key:
                    for e in entries:
                        results.append({
                            "venv": e["venv"],
                            "version": e["version"],
                            "path": e["path"],
                            "python": e["python"],
                        })
            # Sort by venv name
            results.sort(key=lambda r: r["venv"])
            body = json.dumps(results).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif parsed.path in ("/", "/index.html"):
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_response(404)
            self.end_headers()


def main():
    port = int(os.environ.get("PORT", 8765))
    print("Scanning virtual environments...")
    Handler.index = load_packages()
    venv_count = len(find_venvs())
    pkg_count = len(Handler.index)
    print(f"  Found {venv_count} venv(s), {pkg_count} unique packages indexed.")
    print(f"  Scanned: {[d for d in VENV_SEARCH_DIRS if os.path.isdir(d)]}")
    print(f"\nStarting server at http://localhost:{port}")
    print("Press Ctrl+C to stop.\n")
    server = HTTPServer(("localhost", port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
