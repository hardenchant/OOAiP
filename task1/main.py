import os
from base64 import b64encode, b64decode

import pyscrypt


class ScryptPasswordHasher:
    """
    Hash and check password by scrypt
    """
    def __init__(self, n=2048, r=8, p=1, derived_key_length=32):
        # iterations count
        self.n = n
        # block size
        self.r = r
        # parallelism factor
        self.p = p
        # how many bytes to generate as output
        self.derived_key_length = derived_key_length

    def get_password_hash(self, password: str, salt: str = None) -> str:
        if salt is None:
            salt_bytes = os.urandom(32)
        else:
            salt_bytes = salt.encode()
        hash_ = pyscrypt.hash(
            password.encode(),
            salt_bytes,
            self.n,
            self.r,
            self.p,
            self.derived_key_length
        )
        return "$".join(map(str, [self.n, self.r, self.p, b64encode(salt_bytes).decode(), hash_.hex()]))

    def check_password_hash(self, password: str, hash_: str) -> bool:
        n, r, p, salt_b64, hash_hex = hash_.split("$")
        password_hash = pyscrypt.hash(
            password.encode(),
            b64decode(salt_b64),
            int(n),
            int(r),
            int(p),
            int(len(hash_hex) / 2)
        )
        return password_hash.hex() == hash_hex


class LocalStorage:
    """
    Store files in file into your disk
    """
    def __init__(self, password_file_path="./app_users"):
        self.password_file_path = password_file_path

    def read_strings(self):
        try:
            with open(self.password_file_path, 'r') as password_file:
                for line in password_file:
                    yield line.strip()
        except FileNotFoundError:
            pass

    def append_string(self, string):
        with open(self.password_file_path, 'a+') as password_file:
            if password_file.tell() != 0:
                password_file.write('\n')
            password_file.write(string)

    def write_strings(self, strings):
        with open(self.password_file_path, 'w') as password_file:
            password_file.write('\n'.join(strings))


class User:
    """
    
    """
    def __init__(self, login, password_hash):
        self.login = login
        self.password_hash = password_hash

    @staticmethod
    def get_user_from_string(user_string: str):
        return User(*user_string.split(":"))

    def get_user_string(self) -> str:
        return ":".join([self.login, self.password_hash])


class UserManagerException(Exception):
    pass


class UserManager:
    user_model = User
    storage = LocalStorage()
    password_hasher = ScryptPasswordHasher()

    def __init__(self):
        self.__load_users_from_storage()

    def __load_users_from_storage(self):
        self.users = dict()
        for user_string in self.storage.read_strings():
            user = self.user_model.get_user_from_string(user_string)
            self.users[user.login] = user

    def __write_users_to_storage(self):
        self.storage.write_strings([user.get_user_string() for user in self.users.values()])

    def register(self, login: str, password: str):
        if login in self.users:
            raise UserManagerException(f"User with login `{login}` already exists")
        user = self.user_model(login, self.password_hasher.get_password_hash(password))
        self.users[user.login] = user
        self.storage.append_string(user.get_user_string())

    def check_user_exists(self, login: str):
        if login not in self.users:
            raise UserManagerException(f"User with login `{login}` not exists")

    def login(self, login: str, password: str) -> bool:
        self.check_user_exists(login)
        return self.password_hasher.check_password_hash(password, self.users[login].password_hash)

    def change_password(self, login: str, new_password: str):
        self.check_user_exists(login)
        self.users[login].password_hash = self.password_hasher.get_password_hash(new_password)


if __name__ == '__main__':
    um = UserManager()
    um.register('user1', 's3cr3t')
    print(um.login('user1', 's3cr3t'))
    um.change_password('user1', 's3cr3ts3cr3ts3cr3t')
    print(um.login('user1', 's3cr3ts3cr3ts3cr3t'))
