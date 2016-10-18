from setuptools import setup

setup(name='dyngraph',
      version='0.2',
      description='Dynamic graph view',
      url='https://git.joachim.cc/cgit.cgi/dyngraph/',
      author='Jona JOACHIM',
      author_email='jona@joachim.cc',
      license='ISC',
      packages=['dyngraph'],
      install_requires=[
          'pyqtgraph',
          'pandas'
      ],
      scripts = [
          'scripts/dyngraph.pyw'
      ]
)
