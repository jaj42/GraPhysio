from setuptools import setup

setup(name='dyngraph',
      version='0.1',
      description='Dynamic graph view',
      url='http://joachim.cc/',
      author='Jona JOACHIM',
      author_email='jona@joachim.cc',
      license='ISC',
      packages=['dyngraph'],
      install_requires=[
          'pyqtgraph',
          'pandas'
      ],
      zip_safe=False)
