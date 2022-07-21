from setuptools import setup
from setuptools import find_packages

setup(
    name='FootballArticlesGenerator',
    version='',
    packages=find_packages(),
    url='https://github.com/Mokeas/BcThesis',
    license='',
    author='Mokeas',
    author_email='mokeasonline@gmail.com',
    description='Software producing football articles',
    entry_points={
        'console_scripts': [
            'FootballArticlesGenerator.run = FootballArticlesGenerator.run:main'
        ]
    }
)
