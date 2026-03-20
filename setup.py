# from setuptools import setup, find_packages

# setup(
    # name="Dossenge",
    # version="0.1",
    # description="My First Package",
    # packages=find_packages(),
    # python_requires='>=3.0',
# )

# Copyright (c) 2026 Dossenge
# Released under the MIT License (see LICENSE file for details)

from setuptools import setup, find_packages

setup(
    name='dossenge',
    version='1.3',
    description='Dossenge 1.3',
    long_description=open('README.md','r',encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='Dossenge',
    url='http://github.com/Dossenge/Dossenge.git',
    packages=find_packages(),  # Include all packages, subpackages and modules
    install_requires=[
        # List of dependencies
        'toml',
        'requests'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Natural Language :: Chinese (Simplified)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.13',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.5',
    entry_points={
        'console_scripts': [
            'dossenge = Dossenge.Dossenge:dossenge',
        ],
    },
    license='MIT',
    license_files=['LICENSE'], 
)
