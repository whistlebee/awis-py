from setuptools import setup, find_packages


setup(
    name='awis-py',
    version='0.0.2',
    url='https://github.com/whistlebee/awis-py',
    packages=find_packages(),
    install_requires=['requests', 'lxml'],
    python_requires='>=3.6'
)
