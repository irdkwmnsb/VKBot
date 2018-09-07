import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="VKPy",
    version="0.1.0",
    author="irdkwmnsb",
    author_email="me@alzhanov.ru",
    description="VK bot development micro framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/irdkwmnsb/VKPy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)