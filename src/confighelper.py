import configparser
import boto3
from botocore.exceptions import ClientError
import logging
import os
import json

class ConfigHelper:
    
    @staticmethod
    def get_config_helper(default_env_name, aws_parameter_prefix):
        if not "ENVIRONMENT" in os.environ:
            logging.info("Did not find ENVIRONMENT environment variable, running in development mode and loading config from config files.")

            return ConfigHelperFile(environment=default_env_name, filename_list=["config/config.ini", "config/secrets.ini"])

        else:
            ENVIRONMENT = os.environ.get('ENVIRONMENT')

            logging.info(f"Found ENVIRONMENT environment variable containing '{ENVIRONMENT}': assuming we're running in AWS and getting our parameters from the AWS Parameter Store")

            return ConfigHelperParameterStore(environment=ENVIRONMENT, key_prefix=aws_parameter_prefix)

    @staticmethod
    def _log(param, value, is_secret, cache_type="none"):
        logging.info(f"Got parameter {param} with value {ConfigHelper._get_value_log_string(value, is_secret)}")

    @staticmethod
    def _get_value_log_string(value, is_secret):
        if is_secret:
            return "<secret>"
        else:
            return f"{value}" 

class ConfigHelperFile(ConfigHelper):
    
    '''
    Uses the ConfigParser library to read config items from a set of local files
    '''

    def __init__(self, environment, filename_list):
        self.environment    = environment
        self.config         = configparser.ConfigParser(interpolation=None) # We may need % signs in our encryption key, and don't want people to have to worry about escaping them

        for filename in filename_list:
            logging.info(f"Reading in config file '{filename}'")
            self.config.read(filename)

    def get_environment(self):
        return self.environment

    def get(self, key, is_secret=False):
        try:
            value = self.config.get(self.environment, key)
            ConfigHelper._log(key, value, is_secret)
            return value

        except configparser.NoOptionError as e:
            raise ParameterNotFoundException(message=f'Could not get parameter {key}') from e

    # This will throw a ValueError if the parameter doesn't contain an int
    def getInt(self, key, is_secret=False):
        try:
            value = self.config.getint(self.environment, key)
            ConfigHelper._log(key, value, is_secret)
            return value

        except configparser.NoOptionError as e:
            raise ParameterNotFoundException(message=f'Could not get parameter {key}') from e

    # This will throw a ValueError if the parameter doesn't contain a float
    def getFloat(self, key, is_secret=False):
        try:
            value = self.config.getfloat(self.environment, key)
            ConfigHelper._log(key, value, is_secret)
            return value

        except configparser.NoOptionError as e:
            raise ParameterNotFoundException(message=f'Could not get parameter {key}') from e

    # This will throw a ValueError if the parameter doesn't contain a JSON-formatted array
    def getArray(self, key, is_secret=False):
        try:
            value = json.loads(self.config.get(self.environment, key))
            ConfigHelper._log(key, value, is_secret)
            return value

        except configparser.NoOptionError as e:
            raise ParameterNotFoundException(message=f'Could not get parameter {key}') from e

class ConfigHelperParameterStore(ConfigHelper):

    '''
    Reads config items from the AWS Parameter Store
    '''

    def __init__(self, environment, key_prefix):
        self.environment    = environment
        self.key_prefix     = key_prefix
        self.ssm            = boto3.client('ssm') # Region is read from the AWS_DEFAULT_REGION env var

    def get_environment(self):
        return self.environment

    def get(self, key, is_secret=False):

        full_path = self._get_full_path(key)

        value = self._get_from_parameter_store(full_path, is_secret)

        return value

    def _get_from_parameter_store(self, full_path, is_secret=False):
        
        try:
            return self.ssm.get_parameter(Name=full_path, WithDecryption=is_secret)['Parameter']['Value']

        except ClientError as e:
            error_code = e.response['Error']['Code']

            if error_code == "ParameterNotFound":
                raise ParameterNotFoundException(message=f'Could not get parameter {full_path}: {error_code}') from e
            else:
                # Something else bad happened; better just let it through
                raise

    def _get_full_path(self, key):
        return f'/{self.environment}/{self.key_prefix}/{key}'

    # This will throw a ValueError if the parameter doesn't contain an int
    def getInt(self, key, is_secret=False):
        return int(self.get(key, is_secret))

    # This will throw a ValueError if the parameter doesn't contain an int
    def getFloat(self, key, is_secret=False):
        return float(self.get(key, is_secret))

    # This will throw a ValueError if the parameter doesn't contain a JSON-formatted array
    def getArray(self, key, is_secret=False):
        return json.loads(self.get(key, is_secret))

class ParameterNotFoundException(Exception):

    '''
    Raised when a particular parameter cannot be found
    '''

    def __init__(self, message):
        logging.warn(message) # The actual parameter value isn't logged in the stack trace, so if we want to see it we need to log it here
