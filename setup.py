import sys
from cx_Freeze import setup, Executable

import os.path
PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

base = 'Win32GUI' if sys.platform=='win32' else None

buildOptions = dict(packages = [],
                    excludes = ['zmq'],
                    includes = ['numpy.core._methods', 'numpy.lib.format'],
                    include_files = [
                        os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tk86t.dll'),
                        os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tcl86t.dll'),
                     ],
                    )

executables = [
    Executable('scripts/graphysioui.py', base=base)
]

setup(name = 'graphysio',
      version = '0.92',
      description = 'Graphical visualization of physiologic time series',
      url = 'https://github.com/jaj42/graphysio',
      author = 'Jona JOACHIM',
      author_email = 'jona@joachim.cc',
      license = 'ISC',
      python_requires = '>=3.4',
      install_requires = ['pyqtgraph', 'pandas', 'numpy', 'scipy'],
      scripts = ['scripts/graphysioui.py'],
      packages = ['graphysio'],
      include_package_data = True,
      options = dict(build_exe = buildOptions),
      executables = executables
)
