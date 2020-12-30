from setuptools import setup, find_packages, findall

import versioneer

setup(
    name='gui-statue-saver-win',
    description='GUI statue saver for windows',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author='xxc',
    packages=find_packages("src"),
    py_modules=[],
    package_dir={
        '': 'src'
    },
    package_data={
        'gui_status_capture': [
            '*'
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.8',
    ],
    install_requires=[
        "lxml",
        "pywin32",
    ],
    entry_points={
        "console_scripts": [

        ],
    }
)
