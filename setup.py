from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='geebam',
    version='0.1.4',
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
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: GIS',
    ),
    author='Lukasz Tracewski',
    author_email='lukasz.tracewski@outlook.com',
    description='Google Earth Engine Batch Assets Manager',
    long_description=readme(),
    install_requires=[
        'retrying',
        'requests',
        'earthengine-api',
        'requests_toolbelt',
        'bs4',
        'pytest',
        'future'
    ],
    entry_points={
        'console_scripts': [
            'geebam=geebam:main',
        ],
    }
)
