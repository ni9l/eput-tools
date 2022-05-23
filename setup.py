from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="eputgen",
    version="1.0.0",
    description="Package containing tooling for ePUT sytem",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ni9l/eput-tools/",
    author="Nicholas Linse",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords="eput, embedded systems, code generator, development",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.7, <4",
    install_requires=[
        "strictyaml",
        "importlib_resources; python_version < \"3.9\""
    ],
    package_data={"eputgen": ["c/eput_utils.c", "c/eput_utils.h"]},
    entry_points={
        "console_scripts": [
            "eputgen=eputgen:main",
        ],
    }
)
