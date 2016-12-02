try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='geebam',
    version='0.1.0',
    packages=['gee_asset_manager'],
    # package_dir=['gee_asset_manager'],
    package_data={'gee_asset_manager': ['logconfig.json']},
    url='https://github.com/tracek/gee_asset_manager',
    license='Apache 2.0',
    author='Lukasz Tracewski',
    author_email='lukasz.tracewski@outlook.com',
    description='Google Earth Engine Batch Assets Manager',
    install_requires=[
        'retrying',
        'requests',
        'earthengine-api',
        'requests_toolbelt',
        'bs4'
    ],
    entry_points={
        'console_scripts': [
            'geebam=geebam:main',
        ],
    },
    scripts=['geebam.py']
)
