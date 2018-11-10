from setuptools import find_packages, setup

setup(
    name='vppsim',
    packages=find_packages('src'),
    version='0.0.1',
    description='Virtual Power Plant EV Simulation',
    author='Tobias R.',
    package_dir={"": "src"},
)