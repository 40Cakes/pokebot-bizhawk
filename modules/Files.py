import os

# TODO
def read_file(file: str): # Simple function to read data from a file, return False if file doesn't exist
    if os.path.exists(file):
        with open(file, mode="r", encoding="utf-8") as open_file:
            return open_file.read()
    else:
        return False

def write_file(file: str, value: str, mode: str = "w"): # Simple function to write data to a file, will create the file if doesn't exist
    dirname = os.path.dirname(file)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(file, mode=mode, encoding="utf-8") as save_file:
        save_file.write(value)
        return True
