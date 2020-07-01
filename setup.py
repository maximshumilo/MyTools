from setuptools import setup

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='maximshumilo_tools',
    version='0.1.2',
    packages=['ms_tools', 'ms_tools.flask', 'ms_tools.flask.sql', 'ms_tools.flask.mongo', 'ms_tools.flask.common',
              'ms_tools.common'],
    url='https://t.me/MaximShumilo',
    license='',
    author='Maxim Shumilo',
    author_email='shumilo.mk@gmail.com',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=['flask', 'requests', 'marshmallow', 'mongoengine', 'unittests']
)
