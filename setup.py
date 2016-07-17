try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='gee_asset_manager',
    version='0.0.1',
    packages=['batch_manager'],
    url='https://github.com/tracek/gee_asset_manager',
    license='Apache 2.0',
    author='Lukasz Tracewski',
    author_email='lukasz.tracewski@outlook.com',
    description='Google Earth Engine assets manager',
    install_requires=[
        'retrying',
        'requests',
        'ee'
    ]
)
