from setuptools import setup

setup(name = 'dyngraph',
      version = '0.3',
      description = 'Dynamic graph view',
      url = 'https://github.com/jaj42/dyngraph',
      author = 'Jona JOACHIM',
      author_email = 'jona@joachim.cc',
      license = 'ISC',
      install_requires = ['pyqtgraph', 'pandas'],
      scripts = ['scripts/dyngraph.py'],
      packages = ['dyngraph', 'dyngraph.ui'],
)
