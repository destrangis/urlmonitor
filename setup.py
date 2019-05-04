from setuptools import setup, find_packages

with open("VERSION") as vf:
    VERSION = vf.read().strip()

with open("README.rst") as rdf:
    long_descr = rdf.read()

setup(
    name="urlmonitor",
    version=VERSION,
    packages=find_packages(),
    entry_points = {
        'console_scripts': ['urlmonitor=urlmonitor.minder:main'],
    },
    author="Javier Llopis",
    author_email="javier@llopis.me",
    url="http://localhost:8000/stuff",
    description="Check url and run actions if changed",
    long_description_content_type="text/x-rst",
    long_description=long_descr,
    install_requires = [
        "PyYAML>=5.1",
        "requests>=2.21",
        ],
    include_package_data=True
)
