from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

def requirements():
    with open('requirements.txt') as f:
        return f.read().splitlines()

setup(
    name='geebam',
    version='0.1.7',
    packages=['gee_asset_manager'],
    package_data={'gee_asset_manager': ['logconfig.json']},
    url='https://github.com/tracek/gee_asset_manager',
    license='Apache 2.0',
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: GIS',
    ),
    author='Lukasz Tracewski',
    author_email='lukasz.tracewski@outlook.com',
    description='Google Earth Engine Batch Assets Manager',
    long_description=readme(),
    long_description_content_type="text/markdown",
    install_requires=requirements(),
    entry_points={
        'console_scripts': [
            'geebam=geebam:main',
        ],
    }
)
