from setuptools import find_packages, setup

setup(
    name="evsim",
    version="0.0.1",
    description="Virtual Power Plant EV Simulation",
    author="Tobias Richter",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=["click", "gym", "pandas", "numpy>=1.16.1", "simpy >=3.0.0"],
    entry_points="""
            [console_scripts]
            evsim=evsim.evsim:cli
        """,
)
