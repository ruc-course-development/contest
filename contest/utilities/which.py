import os
import pathlib


def on_path(exe):
    path = os.environ['PATH']
    for d in path.split(os.pathsep):
        p = pathlib.Path(d)
        c = list(p.glob('*' + exe))
        c.extend(list(p.glob('*' + exe + '.exe')))
        for e in c:
            if exe in str(e):
                return True
    return False