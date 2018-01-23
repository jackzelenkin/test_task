from setuptools import setup

setup(
  name='test_task',
  version='1.0',
  description='Test task',
  author='Oleksandr Iakovenko',
  author_email='alex.jakovenko@gmail.com',
  packages=['test_task'],
  install_requires=['pytest', 'pyhamcrest', 'flask'],
)
