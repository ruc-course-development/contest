# contest
A CONsole application TESTer

[![Build Status](https://travis-ci.org/Lnk2past/contest.svg?branch=master)](https://travis-ci.org/Lnk2past/contest)

# intro
I wrote this for a class that I teach to help with grading. contest consumes a yaml file that configures how it should interact with the inputs and outputs of the specified program.

The user is able to define what is pumped into the program's stdin and then what should come through stdout and stderr. You can specify what output files should be generated as well as test their content. Users can also specify command line arguments and hook in additional tests that are not easily exercised by doing simple comparisons.

contest requires Python 3 and pyyaml

# todo
add configuration option for file output
