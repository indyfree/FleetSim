import os
from subprocess import check_call

def post_save(model, os_path, contents_manager):
    """post-save hook for converting notebooks to .py scripts"""
    if model['type'] != 'notebook':
        return # only do this for notebooks
    d, fname = os.path.split(os_path)
    check_call(['jupyter', 'nbconvert', '--to', 'script', fname], cwd=d)

c.FileContentsManager.post_save_hook = post_save

# Ignore file types
c.ContentsManager.hide_globs = ['nbconfig', 'migrated', '__pycache__',  '*.py', '*.pyc', '*.pyo', '.DS_Store', '*.so', '*.dylib', '*~']

# Remove data_rate_limit
c.NotebookApp.iopub_data_rate_limit = 0
