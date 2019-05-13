from setuptools import setup

setup(name = 'graphysio',
      version = '0.104',
      description = 'Graphical visualization of physiologic time series',
      url = 'https://github.com/jaj42/graphysio',
      author = 'Jona JOACHIM',
      author_email = 'jona@joachim.cc',
      license = 'ISC',
      python_requires = '>=3.4',
      install_requires = ['pyqtgraph', 'pandas', 'numpy', 'scipy', 'sympy'],
      scripts = ['scripts/graphysioui.py'],
      packages = ['graphysio', 'graphysio.plotwidgets', 'graphysio.ui'],
      include_package_data = True
)
