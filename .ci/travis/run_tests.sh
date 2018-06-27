set -x
pwd
find . -name "*.exe"
python contest.py examples/many_cases/contest_recipe.yaml
python contest.py examples/native_console_app/contest_recipe.yaml
python contest.py examples/output_file/contest_recipe.yaml
python contest.py examples/python_console_app/contest_recipe.yaml