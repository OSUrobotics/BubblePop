#!/usr/bin/env python
from setuptools import setup
import os

root = 'media'
media_files =  [(root, [os.path.join(root, f) for f in files])
    for root, dirs, files in os.walk(root)]

setup(name='BubblePop',
      version='1.0',
      description='A simple bubble popping game',
      author='Dan Lazewatsky',
      author_email='dan@lazewatsky.com',
      url='https://github.com/OSUrobotics/BubblePop',
      license='BSD',
      scripts=['bubblepop.py'],
      data_files=media_files,
      install_requires=['pygame>=1.9.1', 'numpy>=1.7']
      )