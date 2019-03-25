from setuptools import find_packages, setup

setup(
    name="evsim",
    version="0.0.1",
    description="Virtual Power Plant EV Simulation",
    author="Tobias Richter",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "Click>=7.0",
        "dataclasses>=0.6",
        "gym>=0.12",
        "keras-rl>=0.4.2",
        "numpy>=1.16.1",
        "pandas>=0.23.4",
        "simpy >=3.0.11",
    ],
    entry_points="""
            [console_scripts]
            evsim=evsim.evsim:cli
        """,
)
