import sys

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize

ALL = '-f' in sys.argv

from Cython.Compiler import Options
directive_defaults = Options.directive_defaults
Options.docstrings = False
if sys.argv[0].count('profile'):
    directive_defaults['profile'] = True

# performance stuff
directive_defaults['cdivision'] = True
directive_defaults['infer_types'] = True
directive_defaults['wraparound'] = False

ext_modules = []
libraries = []
include_dirs = ['.']

names = [
    'collision'
]

for name in names:
    ext_modules.append(Extension(name, ['./' + name.replace('.', '/') + '.pyx'],
        include_dirs = include_dirs))

EXTENSIONS_NAME = 'porcupyne extensions'

if ALL:
    setup(
        name = EXTENSIONS_NAME,
        cmdclass = {'build_ext': build_ext},
        ext_modules = ext_modules
    )

else:
    setup(
        name = EXTENSIONS_NAME,
        ext_modules = cythonize(ext_modules)
    )
