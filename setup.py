from setuptools import setup

import rypak

def readme():
    with open("README.rst", "r") as f:
        return f.read()

setup(
    name="rypak",
    version=rypak.__version__,
    author=rypak.__author__,
    description="lossless file size reduction for certain file types",
    long_description=readme(),
    packages=["rypak"],
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Utilities",
    ],
    entry_points={
        'console_scripts': ['rypak=rypak:main'],
    },
)