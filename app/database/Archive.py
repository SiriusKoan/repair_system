import hashlib
import io
import re  # regex
import tarfile
from pathlib import Path

import ujson


class Archive():

    pattern = re.compile(r"^.*\.tar\.xz$")

    class Hash():
        defaultMethod = "sha256"

        def __init__(self, method: str = defaultMethod):
            self.h = hashlib.new(method)

        def __call__(self, s: bytes) -> str:
            c = self.h.copy()
            c.update(s)
            return c.hexdigest()

    def getFileNames(self):
        return self.archive.getnames()

    def read(self, filepath: str, hash_check=True) -> dict:
        if self.mode != "r":
            return dict()
        s = self.archive.extractfile(filepath).read()

        if hash_check:
            m1 = self.hash(s)
            m2 = self.hash_dict["files"][filepath]
            if m1 == m2:
                print("Hash '{hash_method}' matches '{filepath}'".format(
                    hash_method=self.hash_dict["hash_method"], filepath=filepath))
            else:
                print(
                    "Hash '{hash_method}' does not match '{filepath}'\n"
                    "Original: {m2}\n"
                    "Current : {m1}".format(
                        hash_method=self.hash_dict["hash_method"], filepath=filepath, m1=m1, m2=m2
                    )
                )
                print("Abort reading")
                return dict()
        return ujson.loads(s.decode("utf-8"))

    def write(self, filepath: str, data: dict, hash_gen=True):
        """
        filepath represent relative path to archive root
        e.g. 'f/123.txt' will create a folder 'f' and write to 'f/123.txt'
        """
        if self.mode != "w":
            return False
        s = ujson.dumps(data, ensure_ascii=False, escape_forward_slashes=False)
        encoded = s.encode("utf-8")

        stream = io.BytesIO(encoded)
        tarinfo = tarfile.TarInfo(name=filepath)
        tarinfo.size = len(encoded)
        self.archive.addfile(tarinfo, stream)

        if hash_gen:
            m = self.hash(encoded)
            self.hash_dict["files"][filepath] = m
        return True

    def __init__(self, path: Path, mode: str):
        """
        mode is "r" or "w", None for auto detection
        """
        self.path = Path(path)
        if mode not in {"r", "w"}:
            print("Invalid mode '{mode}' for '{path}'!".format(mode=mode, path=self.path))
            return None
        self.mode = mode

        if type(self).pattern.match(self.path.name):
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.archive = tarfile.open(self.path, mode + ":xz")
        else:
            print("Invalid filename '{filename}', must be '*.tar.xz'!".format)
            return None

        # hash
        if mode == "r":
            if "hash.json" in self.getFileNames():
                self.hash_dict = self.read("hash.json", hash_check=False)
                self.hash = type(self).Hash(self.hash_dict["hash_method"])
            else:
                print("No hash file found in '{path}'".format(path=self.path))
        else:
            self.hash = type(self).Hash()
            self.hash_dict = {
                "hash_method": type(self).Hash.defaultMethod,
                "files": dict()
            }

    def __del__(self):
        if self.mode == "w":
            self.write("hash.json", self.hash_dict, False)
        self.archive.close()
