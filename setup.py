import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os"], "excludes": ["tkinter"]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(name = 'dyngraph',
      version = '0.3',
      description = 'Dynamic graph view',
      url = 'https://git.joachim.cc/cgit.cgi/dyngraph/',
      author = 'Jona JOACHIM',
      author_email = 'jona@joachim.cc',
      license = 'ISC',
      install_requires = ['pyqtgraph', 'pandas'],
      scripts = ['scripts/dyngraph.pyw'],
      packages = ['dyngraph', 'dyngraph.ui'],
      options = {"build_exe" : build_exe_options},
      executables = [Executable("scripts/dyngraph.pyw", base=base)]
)
