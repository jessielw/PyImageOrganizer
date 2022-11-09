import os

from setuptools import setup, find_packages

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: MacOS",
    "Operating System :: POSIX :: Linux",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
]

with open(os.path.join(os.path.dirname(__file__), "README.md")) as fd:
    ext_long_desc = fd.read()

setup(
    name="PyImageOrganizer",
    version="1.1",
    description="Sorts images/videos/random files into folders by year, month, date/time",
    long_description=ext_long_desc,
    long_description_content_type="text/markdown",
    url="https://github.com/jlw4049/PyImageOrganizer",
    author="Jessie Wilson",
    author_email="jessielw4049@gmail.com",
    license="MIT",
    classifiers=classifiers,
    keywords="PyImageOrganizer",
    packages=find_packages(),
    install_requires=["pymediainfo", "Pillow"],
)
