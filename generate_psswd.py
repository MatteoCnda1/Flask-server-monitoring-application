#!/bin/env python3
from werkzeug.security import generate_password_hash
# The purpose of this program is to allow you to modify the default admin's password. 

passwords = {
    'admin': 'Your password HERE',
}

for name, pwd in passwords.items():
    hashed = generate_password_hash(pwd, method='pbkdf2:sha256')
    print(f"{name}: {hashed}\n")
