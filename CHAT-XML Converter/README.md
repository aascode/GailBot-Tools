
# CHAT-XML Converter

## About

CHAT-XML converter is a tool designed to allow unidirectional conversion between the [CHAT] (http://dali.talkbank.org/clan/)transcription format and the [XML] (https://en.wikipedia.org/wiki/XML) format. XML documents can are both human and machien readbale and can be further converted to almost all major formats.

## Functionality

This tool allows the user to do the following:
* Unidirectional conversion between CHAT and XML formats.

## Pre-requisites

Saulbot needs the following libraries:
  1. argparse
  2. Codecs
  3. Subprocess
  4. lxml 

These can be installed simply by running the following command (once requirements.txt has been downloaded):
* pip install -r requirements.txt

## Usage

CHAT-XML Converter is fairly simple to use. It takes as input a CHAT file (with the .cha extension) and outputs an XML file with the same name as the original file.

The program runs with the following command-line command:
* python chatter.py -files [Names of files] 
* python chatter.py -directory [Name of directory with all CHAT files]

## Contribute

Please send feedback, bugs & requests to:
* hilab-dev@elist.tufts.edu

## Collaborators and Acknowledgments

The [HiLab](https://sites.tufts.edu/hilab/people/), including

* [Saul Albert](http://twitter.com/saul)
* [Jan P. Deruiter](http://twitter.com/jpderuiter)
* [Muhammad Umair](http://sites.tufts.edu/hilab/people)
* [Julia Mertens](https://twitter.com/therealjmertens)
