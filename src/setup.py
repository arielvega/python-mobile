'''
Created on 26/10/2011

@author: ariel
'''

from setuptools import setup, find_packages  
  
setup(name='python-mobile',
      version='0.3',
      description='Una utilidad para realizar operaciones con teléfonos celulares/modems',
      author='Grupo Uremix',
      author_email='uremix@googlegroups.com',
      url='https://github.com/arielvega/python-mobile/',
      license='GPL',
      py_modules=[],
      packages = find_packages(),
      install_requires = ['python-serial']
)