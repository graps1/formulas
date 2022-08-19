from setuptools import setup, find_packages

setup(
        name="formulas",
        version="1.0",
        install_requires=[
            "lark"
        ],
        packages=find_packages(
            include=[
                "formulas"
            ],
            exclude=[
            ]
        )
)
