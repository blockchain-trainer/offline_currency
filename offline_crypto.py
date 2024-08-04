import hashlib
import secrets
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
