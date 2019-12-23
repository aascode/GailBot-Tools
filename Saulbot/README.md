
# Saulbot

## About

Saulbot is named after [Saul Albert](http://twitter.com/saul), a former member of the Human Interaction Lab at Tufts University, and is a transcript analysis tool that can be used to extract turns containing specific keywords in a [CAlite](https://github.com/saulalbert/CABNC/wiki/CHAT-CA-lite) or [CLAN/CHAT](http://dali.talkbank.org/clan/) transcript, including the transcript and audio a specific time before and after the said turn.

## Functionality

This tool allows the user to do the following:
* Extract turns with specified keywords in a transcript.
* Extract a certain amount of audio and text before and after the transcript.
* Output the timings of the transcript and audio into a separate directory.
* Specify the keywords to target.

## Pre-requisites

Saulbot needs the following libraries:
  1. pydub
  2. turncolor
  3. progressbar

These can be installed simply by running the following command (once requirements.txt has been downloaded):
* pip install -r requirements.txt

## Usage

Saulbot is a very flexible tool that uses the 'config.json' file (in the structured json format) for initial configuration. 

The json file consists of a list consisting of one main dictionary. The main dictionary has:
* "OIRs" : The value to this key is a list of keywords (case insensitive) to be targeted in the transcript.
* "time_range" : The range of time (in seconds) before and after the turn with the specified keyword to include in the extracted transcript and audio. For example, 60 will instruct Saulbot to extract 60 seconds of audio/transcript before and 60 seconds of audio/transcript after the turn with the keyword.
* "time_thresh" : This parameter is defined in seconds and is used to remove redundant transcript extractions (in cases where the turns with the keywords are close together). Ideally, this should be equal to the "time_range" parameter.
* "extraction_mode" : The value here can be either "solo" or "in_line". "solo" mode extracts keywords only if they occur as a separate turn in the transcript whereas "in_line" mode targets the keywords in any turn in the transcript.

**NOTE:** An example 'config.json' file is included in the repository

The program runs with the following command-line command:
* python OIRP.py -transcript [transcript_filename.S.ca] -config config.json -audio [audio_filename.wav]

## Contribute

Please send feedback, bugs & requests to:
* hilab-dev@elist.tufts.edu

## Collaborators and Acknowledgments

The [HiLab](https://sites.tufts.edu/hilab/people/), including

* [Saul Albert](http://twitter.com/saul)
* [Jan P. Deruiter](http://twitter.com/jpderuiter)
* [Muhammad Umair](http://sites.tufts.edu/hilab/people)
* [Julia Mertens](https://twitter.com/therealjmertens)
