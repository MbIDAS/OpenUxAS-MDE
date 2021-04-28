import os.path


def get_filename_in_path(path, filename):
    for p in path:
        full_filename = os.path.join(p, filename)
        if os.path.isfile(full_filename):
            return full_filename
    return filename

