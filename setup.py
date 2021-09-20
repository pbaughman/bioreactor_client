from setuptools import setup

setup(
    name="bioreactor_client",
    version="1.0",
    desciption="A code exercise to build a client for a simulated bioreactor API",
    author="Peter Baughman",
    packages=["bioreactor_client"],
    install_requires=[
        "requests",
    ],
    extras_require={
        "tests": ["pytest", "mock"],
    },
    entry_points={
        "console_scripts": ["run_reactor=bioreactor_client.cmd:main"]
    },
)
