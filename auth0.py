from os import environ
from dotenv import load_dotenv, find_dotenv
from textwrap import dedent
import jwt

class verify_token():
    '''
    Verify the given Auth0 JWT
    '''
    def __init__(self, token):
        self.token = token

        if load_dotenv(find_dotenv()) == False:
            '''
            Raise a system exit on error reading environment variables
            with python-dotenv
            '''
            raise SystemExit('Problem locating the .env file')

        '''
        Read the environment variables for the parameters
        needed for Auth0 JWT authentication
        '''
        try:
            auth0_domain = environ['AUTH0_DOMAIN']
            auth0_issuer = environ['AUTH0_ISSUER']
            auth0_audience = environ['AUTH0_AUDIENCE']
            auth0_algorithms = environ['AUTH0_ALGORITHMS']
        except KeyError:
            # Raise a system exit on error reading the hostname
            raise SystemExit(dedent('''\
            One or more of the environment variables needed for
            Auth0 JWT authentication is missing
            ''').replace('\n', ' '))

        self.config = {
            'DOMAIN': auth0_domain,
            'ISSUER': auth0_issuer,
            'AUDIENCE': auth0_audience,
            'ALGORITHMS': auth0_algorithms
        }

        # Initiate the JSON Web Tokens (JWT) client given the Auth0 domain
        jwks_url = f'https://{self.config["DOMAIN"]}/.well-known/jwks.json'
        self.jwks_client = jwt.PyJWKClient(jwks_url)

    def verify(self):
        try:
            # Retrieve the signing keys given the token
            self.signing_key = self.jwks_client.get_signing_key_from_jwt(
                self.token
            ).key
        except jwt.exceptions.DecodeError as error:
            # Return the error message on failed validation
            return {'status': 'error', 'msg': error.__str__()}

        try:
            decoded = jwt.decode(
                self.token,
                self.signing_key,
                issuer = self.config['ISSUER'],
                algorithms = self.config['ALGORITHMS'],
                audience = self.config['AUDIENCE']
            )
        except Exception as e:
            # Return the error message on exception
            return {'status': 'error', 'msg': str(e)}

        return decoded
