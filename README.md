# eput-tools
Tooling for integrating devices with ePUT

## eputgen

This python package contains various utility functions to generate files for use in development of ePUT devices.
To get started either launch the package directly on the command line or import it in a script and use the export_* functions to generate files.

### Installation

You can either install the package with pip or import package folder directly.

Building and installing the package with pip:
```bash
git clone <repository URL>
cd eput-tools
python3 -m pip intall .
```

### Usage

To use the CLI, launch the module directly.
From source:
```bash
python3 -m eputgen [args]
```
When installed with pip:
```bash
eputgen [args]
```

Otherwise import the eputgen package in your script to call the available functions directly.

For documentation, read the function docstrings or launch the CLI with `-h`. 

## Tests

Currently, only a few tests for the C utility library included in generated C code are implemented.
To run it, googletest needs to be installed.
```bash
git clone <repository URL>
cd eput-tools/tests
make test_eput_utils.exe
./test_eput_utils.exe
```
