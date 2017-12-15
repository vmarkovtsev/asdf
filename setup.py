#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import sys
import glob
import builtins
import subprocess as sp

import ah_bootstrap
from setuptools import setup


from astropy_helpers.setup_helpers import (
    register_commands, get_debug_option, get_package_info)
from astropy_helpers.git_helpers import get_git_devstr
from astropy_helpers.version_helpers import _get_version_py_str

# Get some values from the setup.cfg
from configparser import ConfigParser
conf = ConfigParser()
conf.read(['setup.cfg'])
metadata = dict(conf.items('metadata'))

PACKAGENAME = metadata.get('package_name', 'packagename')
DESCRIPTION = metadata.get('description', 'package description')
AUTHOR = metadata.get('author', '')
AUTHOR_EMAIL = metadata.get('author_email', '')
LICENSE = metadata.get('license', 'unknown')
URL = metadata.get('url', '')

def readme():
    with open('README.md') as ff:
        return ff.read()

# Store the package name in a built-in variable so it's easy
# to get from other parts of the setup infrastructure
builtins._PACKAGE_NAME_ = 'asdf'

# VERSION should be PEP386 compatible (http://www.python.org/dev/peps/pep-0386)
VERSION = '1.3.2.dev'

# Indicates if this version is a release version
RELEASE = 'dev' not in VERSION

if not RELEASE:
    VERSION += get_git_devstr(False)

# Get root of asdf-standard documents
ASDF_STANDARD_ROOT = os.environ.get('ASDF_STANDARD_ROOT', 'asdf-standard')

# Populate the dict of setup command overrides; this should be done before
# invoking any other functionality from distutils since it can potentially
# modify distutils' behavior.
cmdclassd = register_commands('asdf', VERSION, RELEASE)

# Freeze build information in version.py
# We no longer use generate_version_py from astropy_helpers because it imports
# the asdf module, and we no longer want to enable that kind of bad behavior
def generate_version_file():
    version_py = os.path.join(os.path.curdir, 'asdf', 'version.py')
    with open(version_py, 'w') as f:
        f.write(_get_version_py_str('asdf', VERSION, None, RELEASE, False))
generate_version_file()


# Get configuration information from all of the various subpackages.
# See the docstring for setup_helpers.update_package_files for more
# details.
package_info = get_package_info()

# Add the project-global data
package_info['package_data'].setdefault('asdf', []).append('data/*')

# The schemas come from a git submodule, so we deal with them here
schema_root = os.path.join(ASDF_STANDARD_ROOT, "schemas")

package_info['package_dir']['asdf.schemas'] = schema_root
package_info['packages'].append('asdf.schemas')

# The reference files come from a git submodule, so we deal with them here
reference_file_root = os.path.join(ASDF_STANDARD_ROOT, "reference_files")
if not os.path.exists(reference_file_root):
    ret = sp.call(['git', 'submodule', 'update', '--init', ASDF_STANDARD_ROOT])
    if ret != 0 or not os.path.exists(reference_file_root):
        sys.stderr.write("Failed to initialize 'asdf-standard' submodule\n")
        sys.exit(ret or 1)

package_info['package_dir']['asdf.reference_files'] = reference_file_root
for dirname in os.listdir(reference_file_root):
    package_info['package_dir']['asdf.reference_files.' + dirname] = os.path.join(
        reference_file_root, dirname)
package_info['packages'].append('asdf.reference_files')

#Define entry points for command-line scripts
entry_points = {}
entry_points['console_scripts'] = [
    'asdftool = asdf.commands.main:main',
]
entry_points['asdf_extensions'] = [
    'builtin = asdf.extension:BuiltinExtension'
]

# Add the dependencies which are not strictly needed but enable otherwise skipped tests
extras_require = []
if os.getenv('CI'):
    extras_require.extend(['lz4>=0.10'])


setup(name=PACKAGENAME,
      version=VERSION,
      description=DESCRIPTION,
      python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*',
      install_requires=[
          'semantic_version>=2.3.1',
          'pyyaml>=3.10',
          'jsonschema>=2.3.0',
          'six>=1.9.0',
          'numpy>=1.8',
          'astropy>=1.3',
      ] + extras_require,
      tests_require=['pytest-astropy'],
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      license=LICENSE,
      url=URL,
      long_description=readme(),
      cmdclass=cmdclassd,
      zip_safe=False,
      use_2to3=True,
      entry_points=entry_points,
      **package_info
)
