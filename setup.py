#!/usr/bin/env python

__version__ = '0.0'

from setuptools import setup

setup(name='django-netezza',
      version=__version__,
      description='Django Netezza backend using pyodbc',
      long_description=open('README.rst').read(),
      keywords='Django,Netezza',
      author='Marc Abramowitz',
      author_email="marc@bluekai.com",
      url='https://github.com/msabramo/django-netezza',
      license='BSD',
      zip_safe=False,
      packages=['netezza', 'netezza.pyodbc'],
      install_requires=['Django>=1.3', 'pyodbc>=2.1.8'],
     )
