from setuptools import setup, find_packages

setup(name='data-gatecountq',
      version='0.2',
      packages=find_packages(),
      install_requires=[
          'celery',
          'pymongo',
          'requests',
          'python-dateutil',
          'tzlocal',
      ],
      )
