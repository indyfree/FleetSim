from setuptools import find_packages, setup

setup(
    name="evsim",
    version="0.0.1",
    description="Virtual Power Plant EV Simulation",
    author="Tobias Richter",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=["Click"],
    entry_points="""
            [console_scripts]
            evsim=evsim.simulation:simulate
        """,
)
