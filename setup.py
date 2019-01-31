from distutils.core import setup

import recrepo

setup(
    name="recrepo",
    version=recrepo.__version__,
    py_modules=["recrepo"],
    author=recrepo.__author__,
    author_email="aka.tkf@gmail.com",
    # url="https://github.com/tkf/recrepo",
    license=recrepo.__license__,
    # description="recrepo - THIS DOES WHAT",
    long_description=recrepo.__doc__,
    # keywords="KEYWORD, KEYWORD, KEYWORD",
    classifiers=[
        "Development Status :: 3 - Alpha",
        # see: http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
    install_requires=[
        # "SOME_PACKAGE",
    ],
)
