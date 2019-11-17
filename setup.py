from setuptools import setup, find_packages

from urlmonitor import VERSION

with open("README.md") as rdf:
    long_descr = rdf.read()

setup(
    name="urlmonitor",
    version=VERSION,
    packages=find_packages(),
    entry_points={"console_scripts": ["urlmonitor=urlmonitor.minder:main"]},
    author="Javier Llopis",
    author_email="javier@llopis.me",
    url="https://github.com/destrangis/urlmonitor",
    description="Check url and run actions if changed",
    long_description_content_type="text/markdown",
    long_description=long_descr,
    install_requires=["PyYAML>=5.1", "requests>=2.21"],
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet",
        "Topic :: Office/Business",
        "Topic :: System",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: Utilities",
    ],
)
