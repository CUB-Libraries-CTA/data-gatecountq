from setuptools import setup, find_packages

setup(name='data-gatecountq',
      version='0.3',
      packages=find_packages(),
      install_requires=[
          'celery==4.3.0',
          'pymongo',
          'requests',
          'python-dateutil',
          'tzlocal',
      ],
      )
