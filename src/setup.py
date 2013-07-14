# -*- coding: utf-8 -*-
#
#
# Copyright 2011,2013 Luis Ariel Vega Soliz and contributors.
# ariel.vega@uremix.org
#
# This file is part of python-mobile.
#
#    python-mobile is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    python-mobile is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with UADH.  If not, see <http://www.gnu.org/licenses/>.
#
#


'''
Created on 26/10/2011

@author: Luis Ariel Vega Soliz (ariel.vega@uremix.org)
@contact: Uremix Team (http://uremix.org)

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
      install_requires = ['pyserial']
)
