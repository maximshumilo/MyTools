from setuptools import setup

with open("README.rst", "r") as fh:
    long_description = fh.read()


setup(
    name='maximshumilo_tools',
    version='0.1.4',
    packages=['ms_tools', 'ms_tools.flask', 'ms_tools.flask.sql', 'ms_tools.flask.mongo', 'ms_tools.flask.common',
              'ms_tools.common'],
    url='https://t.me/MaximShumilo',
    license='',
    author='Maxim Shumilo',
    author_email='shumilo.mk@gmail.com',
    install_requires=['flask', 'requests', 'marshmallow', 'mongoengine'],
    include_package_data=True,
    long_description=long_description,

)
