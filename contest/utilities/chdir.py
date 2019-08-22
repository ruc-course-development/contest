import os


class ChangeDirectory:
    """
    Temporary directory change for context statements.
    """
    def __init__(self, path):
        self.old_path = os.getcwd()
        self.new_path = path = path

    def __enter__(self):
        os.chdir(self.new_path)

    def __exit__(self, type, value, traceback):
        os.chdir(self.old_path)
