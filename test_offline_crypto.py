import unittest
import json
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
import secrets
import uuid
import hashlib
import json

class ChameleonHash:
    def __init__(self, trapdoor=None):
        self.trapdoor = trapdoor if trapdoor else secrets.token_bytes(32)

    def hash(self, message, r=None):
        r = r if r else secrets.token_bytes(32)
        h = hashlib.sha256(message.encode() + r + self.trapdoor).digest()
        return h, r

    def modify(self, original_message, original_r, new_message):
        new_r = hashlib.sha256(original_message.encode() + original_r + self.trapdoor).digest()
        new_r = bytes(a ^ b for a, b in zip(new_r, new_message.encode()))
        return new_r

class CommitmentScheme:
    def __init__(self):
        pass

    def commit(self, value):
        r = secrets.token_bytes(32)
        commitment = hashlib.sha256(value.encode() + r).digest()
        return commitment, r

    def verify(self, value, r, commitment):
        return commitment == hashlib.sha256(value.encode() + r).digest()

class SecureWallet:
    def __init__(self, owner):
        self.owner = owner
        self.balance = 0
        self.tokens = {}

    def create_token(self, value):
        token_id = str(uuid.uuid4())
        token = {
            "id": token_id,
            "value": value,
            "owner": self.owner
        }
        self.tokens[token_id] = token
        self.balance += value
        return token

    def sign_token(self, private_key, token):
        token_data = json.dumps(token).encode('utf-8')
        signature = private_key.sign(
            token_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature

    def verify_token(self, public_key, token, signature):
        token_data = json.dumps(token).encode('utf-8')
        try:
            public_key.verify(
                signature,
                token_data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except:
            return False

    def transfer_token(self, recipient, token_id, private_key):
        if token_id not in self.tokens:
            return "Token does not exist"

        token = self.tokens[token_id]
        if token['owner'] != self.owner:
            return "Not the owner of the token"

        signature = self.sign_token(private_key, token)
        recipient.receive_token(token, signature)
        del self.tokens[token_id]
        self.balance -= token['value']

    def receive_token(self, token, signature):
        self.tokens[token['id']] = token
        self.balance += token['value']

class TestCryptoSystem(unittest.TestCase):
    def setUp(self):
        # Generate keys for testing
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self.public_key = self.private_key.public_key()
        self.public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.ch = ChameleonHash()
        self.cs = CommitmentScheme()

    def test_create_token(self):
        wallet = SecureWallet("test_owner")
        token = wallet.create_token(100)
        self.assertEqual(wallet.balance, 100)
        self.assertEqual(token['value'], 100)
        self.assertEqual(token['owner'], "test_owner")

    def test_sign_and_verify_token(self):
        wallet = SecureWallet("test_owner")
        token = wallet.create_token(100)
        signature = wallet.sign_token(self.private_key, token)
        self.assertTrue(wallet.verify_token(self.public_key, token, signature))

    def test_transfer_token(self):
        sender_wallet = SecureWallet("sender")
        recipient_wallet = SecureWallet("recipient")
        token = sender_wallet.create_token(100)
        signature = sender_wallet.sign_token(self.private_key, token)
        sender_wallet.transfer_token(recipient_wallet, token['id'], self.private_key)
        self.assertEqual(sender_wallet.balance, 0)
        self.assertEqual(recipient_wallet.balance, 100)
        self.assertTrue(recipient_wallet.verify_token(self.public_key, token, signature))

  
    def test_commitment_scheme(self):
        value = "test_value"
        commitment, r = self.cs.commit(value)
        self.assertTrue(self.cs.verify(value, r, commitment))

if __name__ == '__main__':
    unittest.main()
