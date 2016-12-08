from setuptools import setup, find_packages

setup(
    name='abnf',
    version='0.1',
    description='Parse ABNF grammars',
    url='https://github.com/lanzz/abnf',
    license='MIT',
    keywords='abnf parser',
    author='Mihail Milushev',
    author_email='mihail.milushev@lanzz.org',

    packages=find_packages(),
    python_requires='>=3.5',

    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest-cov',
        'pytest-flake8',
    ],
)
