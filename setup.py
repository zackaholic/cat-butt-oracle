from setuptools import setup, find_packages

setup(
    name="fluidnc",
    version="0.1.0",
    description="FluidNC streaming module for controlling CNC machines",
    author="Cat Butt Project",
    packages=find_packages(),
    install_requires=[
        "pyserial>=3.4",
    ],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries",
    ],
)