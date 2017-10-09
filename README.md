# nix-kernel

Simple jupyter wrapper for nix-repl!  Does not yet support completion :'(  But could in future.

Based upon https://github.com/takluyver/bash_kernel, modified for jupyter use case.

## Installation

### Using nix
Clone the repo, and `nix-env -i -f .`.  This installs a nix-kernel executable.
Then, you simply need to create a `nix/kernel.json` file containing an argv like `["nix-kernel",
"-f", "{connection_file}"`

### Using setup tools
Simply install the setup.py file in the repo.  A kernel will be installed into your environment.
