import main

import os
import json
from copy import copy



def get_all_keebs(dir="keebs/"):
    keeb_defs = {}
    filenames = os.listdir(dir)
    filenames = [f for f in filenames if f.endswith(".json")]

    for filename in filenames:
        path = os.path.join(dir, filename)
        main.load_file(path)
        keeb_defs[filename] = copy(main.info)

    # cleaning jic
    main.info = {}

    return keeb_defs

d = get_all_keebs()

def get_nonbroken_keebs():
    d = get_all_keebs()
    a = {n:k for n,k in d.items() if not k.get("broken_keys", [])}
    return a

def get_typical_key_counts():
    counts = []
    d = get_nonbroken_keebs()
    for n, k in d.items():
        count = len(k["raw"].values())
        counts.append(count)
    return counts

