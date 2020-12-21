from setuptools import setup

setup(
    name = "lmbd-cli",
    version= "0.0.2",
    packages=['src'],
    entry_points={
        'console_scripts':[
            'lmbd = src.__main__:start'
        ]
    }
)