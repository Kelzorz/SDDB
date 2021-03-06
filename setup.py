import setuptools

with open("requirements.txt") as fh:
    requirements = fh.read()

with open("LICENSE") as fh:
    license = fh.read()

with open("README.md") as fh:
    long_description = fh.read()

setuptools.setup(
    name="DBDiscord",
    version="0.0.1",
    author="Kelzorz",
    author_email="43789359+Kelzorz@users.noreply.github.com",
    description="Using Discord as a simple database",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license=license,
    url="https://github.com/Kelzorz/DBDiscord",
    project_urls={
        "Issue tracker" : "https://github.com/Kelzorz/DBDiscord/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3"
        "License :: BEERWARE"
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Database",
    ],
    install_requires=requirements,
    packages=["DBDiscord"],
    python_requires=">=3.5.3"
)