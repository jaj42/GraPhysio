from setuptools import setup

setup(name='dyngraph',
      version='0.1',
      description='Dynamic graph view',
      url='http://joachim.cc/',
      author='Jona JOACHIm',
      author_email='jona@joachim.cc',
      license='ISC',
      packages=['frontend'],
      install_requires=[
          'pyqtgraph',
      ],
      zip_safe=False)
