"""
"""

from copy import deepcopy
from os.path import join as pjoin
import platform
import sys

from setuptools.extension import Extension

from tools.cythexts import cyproc_exts, get_pyx_sdist
from tools.setup_helpers import (install_scripts_bat, add_flag_checking,
                                 make_np_ext_builder)
from tools.version_helpers import get_comrec_build


# Define extensions
EXTS = []

# We use some defs from npymath, but we don't want to link against npymath lib
ext_kwargs = {
    'include_dirs': ['src'],  # We add np.get_include() later
    'define_macros': [("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")]
    }

for modulename, other_sources, language in (
        ('furyspeed.videoframe', [], 'c'),
        ):
    pyx_src = pjoin(*modulename.split('.')) + '.pyx'
    EXTS.append(Extension(modulename, [pyx_src] + other_sources,
                          language=language,
                          **deepcopy(ext_kwargs)))  # deepcopy lists

build_ext, need_cython = cyproc_exts(EXTS, '0.29.24', 'pyx-stamps')
# Add openmp flags if they work
simple_test_c = """int main(int argc, char** argv) { return(0); }"""
omp_test_c = """#include <omp.h>
int main(int argc, char** argv) { return(0); }"""

msc_flag_defines = [[['/openmp'], [], omp_test_c, 'HAVE_VC_OPENMP'],
                    ]
gcc_flag_defines = [[['-msse2', '-mfpmath=sse'], [], simple_test_c, 'USING_GCC_SSE2'],
                    ]

if 'clang' not in platform.python_compiler().lower():
    gcc_flag_defines += [[['-fopenmp'], ['-fopenmp'], omp_test_c,
                          'HAVE_OPENMP'], ]

# Test if it is a 32 bits version
if not sys.maxsize > 2 ** 32:
    # This flag is needed only on 32 bits
    msc_flag_defines += [[['/arch:SSE2'], [], simple_test_c, 'USING_VC_SSE2'], ]

flag_defines = msc_flag_defines if 'msc' in platform.python_compiler().lower() else gcc_flag_defines

extbuilder = add_flag_checking(build_ext, flag_defines, 'furyspeed')
extbuilder = make_np_ext_builder(extbuilder)

build_ext = extbuilder
install_scripts = install_scripts_bat
sdist = get_pyx_sdist(include_dirs=['src'])
