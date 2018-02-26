import os

with open('secret_key.txt', 'wb') as f:
    f.write(os.urandom(24))
