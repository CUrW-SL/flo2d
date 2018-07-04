from setuptools import setup, find_packages

setup(
    name='flo2d_server',
    version='0.0.1',
    packages=find_packages(),
    url='http://www.curwsl.org',
    license='MIT',
    author='thilinamad',
    author_email='madumalt@gamil.com',
    description='REST API for running FLO2D models at curwsl',
    install_requires=['FLASK', 'Flask-Uploads', 'Flask-JSON'],
    zip_safe=True
)
