from setuptools import setup

setup(
    name='maximshumilo_tools',
    version='0.1.0',
    packages=['ms_tools', 'ms_tools.flask', 'ms_tools.flask.sql', 'ms_tools.flask.mongo', 'ms_tools.flask.common',
              'ms_tools.common'],
    url='https://t.me/MaximShumilo',
    license='',
    author='Maxim Shumilo',
    author_email='shumilo.mk@gmail.com',
    description='My development tools',
    install_requires=['flask', 'requests', 'marshmallow', 'mongoengine', 'natsort']
)
