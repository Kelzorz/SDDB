import setuptools

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read()

with open("LICENSE", "r", encoding="utf-8") as fh:
    license = fh.read()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="SDDB",
    version="0.0.2",
    author="Kelzorz",
    author_email="43789359+Kelzorz@users.noreply.github.com",
    # description="Using Discord as a simple database",
    # description_content_type="text/markdown",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    license=license,
    url="https://github.com/Kelzorz/SDDB",
    project_urls={
        "Issue tracker" : "https://github.com/Kelzorz/SDDB/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3"
        "License :: BEERWARE"
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Database",
    ],
    install_requires=requirements,
    packages=["SDDB"],
    python_requires=">=3.5.3"
)