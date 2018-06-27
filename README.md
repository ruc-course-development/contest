# contest
A ```CON```sole application ```TEST```er

[![Build Status](https://travis-ci.org/Lnk2past/contest.svg?branch=master)](https://travis-ci.org/Lnk2past/contest)

# intro
I wrote this for a class that I teach to help with grading. contest consumes a yaml file that configures how it should interact with the inputs and outputs of the specified program.

The user is able to define what is pumped into the program's stdin and then what should come through stdout and stderr. You can specify what output files should be generated as well as test their content. Users can also specify command line arguments and hook in additional tests that are not easily exercised by doing simple comparisons.

```contest``` requires ```Python 3``` and ```pyyaml```

# todo
add configuration option for file output

add return code checking

add test recipe generator

# details
## overview
A set of tests for a particular executable are defined in a single test recipe. This recipe is a YAML file that allows the test developer to specify the executable, inputs, and outputs of the program over any number of test cases. The ```test_skeleton.yaml``` is just an empty recipe that shows what can be specified. Entries that are to be left empty can be removed from the recipe altogether to avoid clutter. e.g. your program may not interact with ```stdin``` and so you can just remove it from your tests.

### learning by example
Each test case is defined under the ```test-cases``` node in the recipe; simply add a new section as desired. You will just need to make sure each test is named uniquely. Here is an example of a test recipe (taken from ```exampels/native_console_app```):

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

1. The name of the ```executable``` to run is
    ```
    hello_world.exe
    ```
2. We have a single test-case named
    ```
    standard
    ```
3. We define the input to ```stdin```, which is a single entry:
    ```
    Lnk2past
    ```
4. We define the output to ```stdout```, which is:
    ```
    Hello! What is your name?
    Welcome to the world, Lnk2past!
    ```

This is really the equivalent of the following in some shell environment:
```
~/project> ./main.exe
Hello! What is your name?
Lnk2past
Welcome to the world, Lnk2past!
~/project>
```

This means that when running the executable ```hello_world.exe``` we can expect the input in step 3 to yield the output in step 4. ```contest``` does this comparison for you! This allows you to write tests that would reflect actual use cases of your executable. Add as many tests as you like to cover various pathways through your program and to cover the various errors your program may encounter.

Check out the other examples under the ```examples``` directory.

### test directories

```contest``` will run each test-case in a separate directory, and will create those directories in the same directory containing the test recipe. This ensures minimal conflict between test cases. For example, if your test recipe contains tests "foo" and "bar" and is located in "C:\Users\Lnk2past\MyProject", then you can expact the following directory structure:

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

### filtering tests

You can filter your test-recipes to only run a select few. This may be useful during debugging to only run your new test without needing to run the entire test recipe. You can do this via the ```--filter``` option. This expects some ```regular expression``` to filter on. e.g. we can test only those tests that are marked with a specific keyword in their names, say "tracking", by doing the following:

```
python contest.py test_recipe.yaml --filter "tracking"
```

Likewise, you can exclude specific tests in order if they are problematic or if you are focusing on other tests. simply use the ```--exclude-filters``` or ```--exclude``` for short. So long as you know ```regex``` you can do whatever you like for filtering your tests!