from setuptools import setup, find_packages

setup(
    name="pyfsmanager",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "colorama>=0.4.6",
    ],
    extras_require={
        "win32": ["pywin32>=306"],
    },
    entry_points={
        "console_scripts": [
            "pyfs=pyfsmanager.cli:main",
            "pyfs-gui=pyfsmanager.gui:main",
        ],
    },
)
