from setuptools import setup

setup(
    name = "lmbd-cli",
    version= "0.0.2",
    packages=['lmbd_deploy'],
    entry_points={
        'console_scripts':[
            'lmbd = lmbd_deploy.__main__:start'
        ]
    }
)