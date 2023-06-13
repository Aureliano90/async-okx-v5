from setuptools import setup, find_packages

setup(
    name="async_okx_v5",
    version="0.2.0",
    packages=find_packages(),
    url="https://github.com/Aureliano90/async-okx-v5",
    license="Apache-2.0",
    author="Aureliano",
    author_email="shuhui.1990+@gmail.com",
    description="Async OKx v5 API. Elegant.",
    python_requires=">=3.10",
    install_requires=[
        "aiohttp[speedups]~=3.8.4",
        "aiostream~=0.4.5",
        "charset-normalizer~=3.1.0",
        "python-dotenv~=1.0.0",
        "websockets~=11.0.3",
    ],
)
