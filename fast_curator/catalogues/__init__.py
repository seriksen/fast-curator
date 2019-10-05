import uproot
from collections import defaultdict


class XrootdExpander():
    """
    Expand wild-carded file paths, including with xrootd-served files
    """
    from .. import xrootd_glob

    @staticmethod
    def expand_file_list(files):
        full_list = []
        for name in files:
            expanded = XrootdExpander.xrootd_glob.glob(name)
            full_list += map(str, expanded)
        return full_list

    @staticmethod
    def check_entries(*args, **kwargs):
        return check_entries_uproot(*args, **kwargs)


class LocalGlobExpander():
    """
    Expand wild-carded file paths on the local file system
    """
    import glob

    @staticmethod
    def expand_file_list(files):
        full_list = []
        for name in files:
            expanded = LocalGlobExpander.glob.glob(name)
            full_list += map(str, expanded)
        return full_list

    @staticmethod
    def check_entries(*args, **kwargs):
        return check_entries_uproot(*args, **kwargs)


def check_entries_uproot(files, tree_names, no_empty, confirm_tree=True):
    no_empty = no_empty or confirm_tree
    if not isinstance(tree_names, (tuple, list)):
        tree_names = [tree_names]

    if not no_empty:
        n_entries = {tree: uproot.numentries(files, tree) for tree in tree_names}
    else:
        n_entries = {tree: 0 for tree in tree_names}
        missing_trees = defaultdict(list)
        for tree in tree_names:
            totals = uproot.numentries(files, tree, total=False)
            for name, entries in totals.items():
                n_entries[tree] += entries
                if no_empty and entries <= 0:
                    files.remove(name)
                if confirm_tree and entries == 0:
                    if tree not in uproot.open(name):
                        missing_trees[tree].append(name)
        if missing_trees:
            files = set(sum((list(v) for v in missing_trees.values()), []))
            msg = "Missing at least one tree (%s) for %d file(s): %s"
            msg = msg % (", ".join(missing_trees), len(missing_trees), ", ".join(files))
            raise RuntimeError(msg)

    if len(n_entries) == 1:
        n_entries = list(n_entries.values())[0]
    return files, n_entries, branches


known_expanders = dict(xrootd=XrootdExpander,
                       local=LocalGlobExpander,
                       )


def get_file_list_expander(expander):
    if expander not in known_expanders:
        msg = "Unknown file expander requested, '%s'. Valid options: %s"
        raise RuntimeError(msg % (expander, ", ".join(known_expanders.keys())))
    return known_expanders[expander]
