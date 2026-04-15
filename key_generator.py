from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Выведет что-то вроде: kX-8... (сохраните это)
