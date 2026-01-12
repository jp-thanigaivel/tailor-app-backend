import logging
import secrets
import subprocess

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette import status

from app.config.app_secret import app_secret
from app.common.models import TokenData
from app.utils.admin_constant import KEY_STDERR, KEY_STDOUT, KEY_RETURN_CODE, ALLOWED_COMMANDS
from app.utils.app_constant import STATUS_TYPE_ERROR, STATUS_DESC_AUTH_NOT_AUTHORIZED_FOR_ACTION, DTO_KEY_RESPONSE_DATA
from app.core.exceptions import AuthorizeException

logger = logging.getLogger(__name__)

security = HTTPBasic()


def validate_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    # encode the credentials to compare
    input_user_name = credentials.username.encode("utf-8")
    input_password = credentials.password.encode("utf-8")

    # DO NOT STORE passwords in plain text.
    # This is just for internal purpose to add extra security layer for internal api.
    stored_username = app_secret.internal_api_credential.user_name.encode("utf-8")
    stored_password = app_secret.internal_api_credential.password.encode("utf-8")

    is_username = secrets.compare_digest(input_user_name, stored_username)
    is_password = secrets.compare_digest(input_password, stored_password)

    if is_username and is_password:
        return {"auth message": "authentication successful"}

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid credentials",
                        headers={"WWW-Authenticate": "Basic"})


def execute_script(script_name, token_data: TokenData):
    logger.info("In execute_script for {}".format(str(script_name)))
    if script_name not in ALLOWED_COMMANDS:
        logger.error("scriptName is not configured")
        raise AuthorizeException(status.HTTP_401_UNAUTHORIZED, STATUS_TYPE_ERROR,
                                 STATUS_DESC_AUTH_NOT_AUTHORIZED_FOR_ACTION + " script not configured")
    logger.info("Executing Shell Process for {}".format(str(script_name)))
    process_output = subprocess.run(
        script_name,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return_code = process_output.returncode
    standard_output = process_output.stdout
    standard_error = process_output.stderr
    logger.info("Executed Shell Process with return_code {} for {}".format(str(return_code), str(script_name)))
    response = {KEY_RETURN_CODE: return_code, KEY_STDOUT: standard_output, KEY_STDERR: standard_error}
    logger.info("out execute_script for {}".format(str(script_name)))
    return {DTO_KEY_RESPONSE_DATA: response}
