# Natural Language Generation system writing football articles
_**Bachelor thesis at Faculty of Mathematics and Physics, Charles University, Czech Republic, 2023**_

**Abstract of the thesis**: Journalism could become a tedious job as its main concern is to create as many
articles as possible, usually prioritising quantity over quality. Some articles are quite
routine and they need to exist just because most of the population prefers text over raw
data. The idea is to ease this job and generate articles, particularly about football in
Czech language, automatically from non-linguistic data.
This thesis is concerned with analysing implementation of such a linguistic software
and moreover offers a brief overview of a Natural Language Generation (NLG) process.
The major focus of this overview is on benefits and drawbacks of different approaches to
NLG as well as describing NLG tasks and its challenges you need to overcome in order
to produce a similar human language (not only Czech) producing program. 

## Content of the project
In the project, there are three directories:

* **_BcText_**: the textual version of the thesis along with CZ/EN abstract</li>
* **_FootballArticlesGenerator_**: Python software that produces football articles</li>
* **_MatchData_**: directory to store JSON data about matches to then serve as inputs, only one example match is in this directory: _example_match.json_.</li>

## Text of the thesis

Text of the thesis describes the project _FootballArticlesGenerator_ in depth as well as the process of Natural Language Generation (NLG) in general. The target audience of the thesis are computer scientists, which are interested (but relatively new) in the field of computational linguistic. The aim of the text is to broaden reader's knowledge in the field of NLG as well as give an idea how to approach similar project. 

Note: University's bachelor thesis template (version 2020-04-17) was used when setting in TeX. 

## FootballArticlesGenerator

Project is written purely in Python. Project contains separate modules, which are described briefly in the code as comments or in detail in the thesis. 

## How to run the program
* Install Python (version 3.7+)
* Install Python requests module

```
python -m pip install requests
```

* Clone the repository:

```
git clone https://github.com/Mokeas/BcThesis
```

* If you want results to be complete, you need to acquire authorization key for Genja API (Contact Geneea at [geneea.com](https://geneea.com/)). Without the key, the program will still run, but the linguistic realisation will not be performed and therefore the outputted text will be the intended input for Genja.

* To run the program just change directory to the FootballArticlesGenerator:
```
cd FootballArticlesGenerator
```
* and run _run.py_ with _-k_ argument inserting key for Genja:
```
python run.py -k insert_key_here
```

## Arguments
Every argument is optional:
* ```-h, --help```: Show help message and exit.
* ```-m MATCH_DATA, --match_data MATCH_DATA```: Defines JSON file with match data (default=..\MatchData\example_match.json).
* ```-c TEXT_COUNT, --text_count TEXT_COUNT```: Changes number of generated texts (default=3).
* ```-o, --short_output```: Prints detailed output. If missing, prints only result articles.
* ```-k KEY, --key KEY```: Sets authorization key for Genja API.