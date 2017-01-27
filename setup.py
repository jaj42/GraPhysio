from setuptools import setup

setup(name = 'graphysio',
      version = '0.4',
      description = 'Graphical visualization of physiologic time series',
      url = 'https://github.com/jaj42/graphysio',
      author = 'Jona JOACHIM',
      author_email = 'jona@joachim.cc',
      license = 'ISC',
      install_requires = ['pyqtgraph', 'pandas'],
      scripts = ['scripts/graphysio.py'],
      packages = ['graphysio', 'graphysio.ui'],
)
