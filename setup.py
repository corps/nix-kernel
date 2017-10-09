import sys
import os
import json
import pkgutil

from distutils import log
from distutils.command.install import install
from setuptools import setup
try:
    from jupyter_client.kernelspec import install_kernel_spec
except ImportError:
    from IPython.kernel.kernelspec import install_kernel_spec
from IPython.utils.tempdir import TemporaryDirectory

kernel_json = {
    'argv': [sys.executable,
             '-m', 'nix-kernel',
             '-f', '{connection_file}'],
    'display_name': 'nix',
    'language': 'Nix',
    'name': 'nix',
}


class install_with_kernelspec(install):
    def run(self):
        install.run(self)
        with TemporaryDirectory() as td:
            os.chmod(td, 0o755)  # Starts off as 700, not user readable
            with open(os.path.join(td, 'kernel.json'), 'w') as f:
                json.dump(kernel_json, f, sort_keys=True)
            log.info('Installing kernel spec')
            kernel_name = kernel_json['name']
            try:
                install_kernel_spec(td, kernel_name, user=self.user,
                                    replace=True)
            except:
                install_kernel_spec(td, kernel_name, user=not self.user,
                                    replace=True)

setup(name='nix-kernel',
      version='0.1.0',
      description='A nix-repl kernel for Jupyter',
      author='Zach Collins',
      author_email='recursive.cookie.jar@gmail.com',
      license='MIT',
      url="https://github.com/corps/nix-kernel",
      cmdclass={'install': install_with_kernelspec},
      install_requires=[
          'pexpect >= 4.0',
          'notebook >= 4.0'],
      packages=['nix-kernel'],
      classifiers=[
          'Framework :: IPython',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Topic :: System :: Shells',
      ]
      )
