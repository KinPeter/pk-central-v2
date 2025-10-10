import boto3
import requests
import base64
import jwt

from app.common.environment import PkCentralEnv
from app.common.responses import UnauthorizedException
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


class CognitoClientHelper:
    def __init__(self, env: PkCentralEnv):
        self.client = boto3.client(
            "cognito-idp",
            aws_access_key_id=env.AWS_ACCESS_KEY,
            aws_secret_access_key=env.AWS_SECRET_ACCESS_KEY,
            region_name=env.AWS_REGION,
        )
        self.region = env.AWS_REGION
        self.user_pool_id = env.AWS_COGNITO_USER_POOL_ID
        self.app_client_id = env.AWS_COGNITO_APP_CLIENT_ID
        self.jwks_url = f"https://cognito-idp.{env.AWS_REGION}.amazonaws.com/{env.AWS_COGNITO_USER_POOL_ID}/.well-known/jwks.json"

    def verify_id_token(self, email_request: str, id_token: str):
        """Verify the ID token against the user pool."""
        try:
            jwks = requests.get(self.jwks_url).json()
            headers = jwt.get_unverified_header(id_token)
            key = next(k for k in jwks["keys"] if k["kid"] == headers["kid"])
            pem_key = self.jwk_to_pem(key)

            claims = jwt.decode(
                id_token,
                pem_key,
                algorithms=["RS256"],
                audience=self.app_client_id,
                issuer=f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}",
            )

            cognito_sub = claims.get("sub")
            email_claim = claims.get("email")

            user = self.get_user(cognito_sub)
            if not user:
                raise UnauthorizedException("User does not exist")

            user_attributes = user.get("UserAttributes", [])
            user_email = next(
                (attr["Value"] for attr in user_attributes if attr["Name"] == "email"),
                None,
            )

            if not (email_claim == email_request == user_email):
                raise UnauthorizedException("Email does not match")

            return user_email

        except requests.exceptions.RequestException as e:
            raise UnauthorizedException(f"Failed to fetch JWKS: {str(e)}")
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("ID token has expired")
        except jwt.InvalidTokenError as e:
            print("JWT InvalidTokenError:", str(e))
            raise UnauthorizedException(f"Invalid ID token: {str(e)}")

    def get_user(self, username: str):
        return self.client.admin_get_user(
            UserPoolId=self.user_pool_id,
            Username=username,
        )

    def jwk_to_pem(self, jwk):
        n = int.from_bytes(base64.urlsafe_b64decode(jwk["n"] + "=="), "big")
        e = int.from_bytes(base64.urlsafe_b64decode(jwk["e"] + "=="), "big")
        public_numbers = rsa.RSAPublicNumbers(e, n)
        public_key = public_numbers.public_key()
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem
