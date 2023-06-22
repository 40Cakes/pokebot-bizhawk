import io
import json
import mmap


def LoadJsonMmap(size, file):
    """
    Loads a JSON object from a memory mapped file
    BizHawk writes game information to memory mapped files every few frames (see pokebot.lua)
    See https://tasvideos.org/Bizhawk/LuaFunctions (comm.mmfWrite)
    :param size: Map size
    :param file: File to load
    :return: JSON object or None if failed
    """
    try:
        shmem = mmap.mmap(0, size, file)
        if shmem:
            bytes_io = io.BytesIO(shmem)
            byte_str = bytes_io.read()
            json_obj = json.loads(
                byte_str.decode("utf-8").split("\x00")[0])  # Only grab the data before \x00 null chars
            return json_obj
        return None
    except:
        return None
