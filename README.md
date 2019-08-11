# contest
[![Build Status](https://travis-ci.org/Lnk2past/contest.svg?branch=master)](https://travis-ci.org/Lnk2past/contest)

A `CON`sole application `TEST`er

## Introduction
`contest` is a testing application that exercises a program with configured input and then checks the output with some expected content. Simply put, `contest` is a driver that facilitates supplying input to and validating output from a specific executable. `contest` itself is not obscenely robust, but lets the developer implement what is needed as they need it.

## Installation
```
pip install contest
```

You may install from this repo, clone and simply:
```
python setup.py install
```

## Motivation
I wrote this for a class that I teach to help with grading. Given the configuration driven nature of it (how else should a testing framework/tool work?) `contest` lets me define multiple test cases for particular programs (assignments) so that not only is grading easier for me, but I can integrate assignments into a grading pipeline so that I can do as little work as possible and my students can get immediate feedback on submissions.

## How It Works
### Overview
YAML is the preferred choice of input for `contest` for a few reasons, but most notably for its easy to follow syntax and allowance of multiline strings (sorry JSON). `contest` consumes an input file that specifies at least one executable and then whatever additional information is provided. Check out the test skeleton below to see what can be specified; the main ones though are the input and output streams `stdout`, `stderr`, and `stderr` as well and CLI inputs `argv`. You can specify newly generated files that you expect to be created and even go further and specify custom tests (as `Python` files) that cover the things simple I/O comparisons do not.

#### Test Skeleton
```python
executable:
test-cases:
    standard:
        executable:
        returncode:
        argv: []
        stdin: |
        stdout: |
        stderr: |
        ofstreams:
            - base-file:
              test-file:
        extra-tests: []
```

## Development Environment
I am coding this to work with latest Python. I have ~~absolutely no~~ little interest in backwards compatibility. While earlier versions and standards may work right now, I do not guarantee any of that moving forward. I will not hinder development for the sake of supporting something older. Given the range of development environments currently at my disposal there will be some compatibility for a bit.

I have a few primary development environments at the moment and so you can for expect support for at least the following:
- **Python 3.5.3** and GCC 6.3.0 (Raspbian)
- **Python 3.6.7** and GCC 7.3.0 (Ubuntu 18.04.2)
- **Python 3.6.8** and MSVC v1916 (Windows 10, Visual C++ 2017 (15.9))
- **Python 3.7.3** and MSVC v1916 (Windows 10, Visual C++ 2017 (15.9))

## Basic Usage
Given some configuration you can run `contest` using the following:
```
contest <path to configuration file>
```

This will parse the configuration and run the specified test cass(s). In the configuration file each test case is defined under the `test-cases` node in the recipe; simply add a new section as desired. You will just need to make sure each test is named uniquely. Here is an example of a test recipe (taken from `exampels/native_console_app`):

```
executable: hello_world.exe
test-cases:
    standard:
        stdin: |
            Lnk2past
        stdout: |
            Hello! What is your name?
            Welcome to the world, Lnk2past!
```

Let us break down what this is specifying:

1. The name of the `executable` to run is
    ```
    hello_world.exe
    ```
2. We have a single test-case named
    ```
    standard
    ```
3. We define the input to `stdin`, which is a single entry:
    ```
    Lnk2past
    ```
4. We define the output to `stdout`, which is:
    ```
    Hello! What is your name?
    Welcome to the world, Lnk2past!
    ```

This is really the equivalent of the following in some shell environment:
```
~/project> ./hello_world.exe
Hello! What is your name?
Lnk2past
Welcome to the world, Lnk2past!
~/project>
```

This means that when running the executable `hello_world.exe` we can expect the input in step 3 to yield the output in step 4. `contest` does this comparison for you! This allows you to write tests that would reflect actual use cases of your executable. Add as many tests as you like to cover various pathways through your program and to cover the various errors your program may encounter.

Check out the other examples under the `examples` directory.

### Test Directories

`contest` will run each test-case in a separate directory, and will create those directories in the same directory containing the test recipe. This ensures minimal conflict between test cases. For example, if your test recipe contains tests "foo" and "bar" and is located in "C:\Users\Lnk2past\MyProject", then you can expact the following directory structure:

```
C:\Users\Lnk2past\MyProject\
|---src\...
|---include\...
|---contest_recipe.yaml
|---test_output\
    |---foo\...
    |---bar\...
```

Even if your test-case produces no output on disk, the test-output directory will be created.

### Filtering Tests

You can filter your test-recipes to only run a select few. This may be useful during debugging to only run your new test without needing to run the entire test recipe. You can do this via the `--filter` option. This expects some `regular expression` to filter on. e.g. we can test only those tests that are marked with a specific keyword in their names, say "tracking", by doing the following:

```
python contest.py test_recipe.yaml --filter "tracking"
```

Likewise, you can exclude specific tests in order if they are problematic or if you are focusing on other tests. simply use the `--exclude-filters` or `--exclude` for short. So long as you know `regex` you can do whatever you like for filtering your tests!

## TODO
- add configuration option for file output
- improve testing
    - add more test cases
    - test custom test examples
