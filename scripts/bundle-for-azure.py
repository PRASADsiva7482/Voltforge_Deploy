#!/usr/bin/env python3
import os
import zipfile
import shutil

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AZURE_DEPLOY_DIR = os.path.join(ROOT_DIR, "azureDeploy")
OUTPUT_ZIP = os.path.join(AZURE_DEPLOY_DIR, "voltforge-azure-bundle.zip")

EXCLUDE_DIRS = {
    'node_modules', '.git', 'target', 'dist', '.toolchains',
    'training_runs', '__pycache__', '.pytest_cache', '.venv',
    '.idea', '.vscode'
}

EXCLUDE_EXTENSIONS = {
    '.npz', '.pt', '.bin'
}

AI_RUNTIME_ITEMS = {
    'api', 'api_contract', 'engine', 'model', 'context_compiler',
    'data_governance', 'electronics_corpus', 'engineering_tools',
    'evaluation', 'feedback_governance', 'grounding', 'memory_store',
    'internet_retrieval', 'local_retrieval', 'task_schema', 'hardware_coverage', 'tests',
    'circuit_verifier.py', 'web_search_engine.py', 'observability.py',
    'config.py', 'main.py', 'app.py', 'dataset.txt', 'requirements.txt',
    'Dockerfile'
}

print("[*] Creating clean package for Azure deployment...")

if os.path.exists(OUTPUT_ZIP):
    os.remove(OUTPUT_ZIP)

with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zf:
    # 1. azureDeploy (exclude existing zip files)
    for root, dirs, files in os.walk(AZURE_DEPLOY_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f.endswith('.zip'):
                continue
            abs_path = os.path.join(root, f)
            rel_path = os.path.relpath(abs_path, ROOT_DIR)
            zf.write(abs_path, rel_path)

    # 2. Voltforge_UI (exclude node_modules, dist)
    ui_dir = os.path.join(ROOT_DIR, "Voltforge_UI")
    for root, dirs, files in os.walk(ui_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            abs_path = os.path.join(root, f)
            rel_path = os.path.relpath(abs_path, ROOT_DIR)
            zf.write(abs_path, rel_path)

    # 3. Voltforge_BL (exclude target)
    bl_dir = os.path.join(ROOT_DIR, "Voltforge_BL")
    for root, dirs, files in os.walk(bl_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            abs_path = os.path.join(root, f)
            rel_path = os.path.relpath(abs_path, ROOT_DIR)
            zf.write(abs_path, rel_path)

    # 4. Voltforge_AI (only runtime items)
    ai_dir = os.path.join(ROOT_DIR, "Voltforge_AI")
    for item in AI_RUNTIME_ITEMS:
        item_path = os.path.join(ai_dir, item)
        if not os.path.exists(item_path):
            continue
        if os.path.isfile(item_path):
            rel_path = os.path.relpath(item_path, ROOT_DIR)
            zf.write(item_path, rel_path)
        else:
            for root, dirs, files in os.walk(item_path):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in EXCLUDE_EXTENSIONS:
                        continue
                    abs_path = os.path.join(root, f)
                    rel_path = os.path.relpath(abs_path, ROOT_DIR)
                    zf.write(abs_path, rel_path)

size_mb = round(os.path.getsize(OUTPUT_ZIP) / (1024 * 1024), 2)
print(f"[+] Clean package created successfully: {OUTPUT_ZIP} ({size_mb} MB)")
