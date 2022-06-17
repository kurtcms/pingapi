from fastapi import FastAPI, Query, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from typing import Optional
from pydantic import BaseModel
from io import StringIO
import asyncio
import subprocess
import numpy as np
import pandas as pd

from auth0 import verify_token

class ip_model(BaseModel):
    '''
    Pydantic model for POST request
    '''
    ip: str
    c: Optional[int] = Query(5, gt = 0, le = 60)

    class Config:
        schema_extra = {
            'example': {
                'ip': '1.1.1.1',
                'c': 5
            }
        }

class rtt_model(BaseModel):
    '''
    Pydantic model for GET or POST reply
    '''
    date_time: str
    ip_host: str
    rtt_mean: float
    rtt_min: float
    rtt_max: float
    jitter: float
    count_requested: int
    count_received: int
    packet_loss: float

class exception_model(Exception):
    '''
    Pydantic model for exception
    '''
    def __init__(self, msg: str):
        self.msg = msg

token_auth_scheme = HTTPBearer()

description = '''
    Return the round trip time (RTT), jitter and packet loss to the
    given IP address or hostname in the specified duration as
    measured by ping at one ICMP datagram per second.
    '''
app = FastAPI(
    title = 'PingAPI',
    description = description,
    version = '1.0',
    terms_of_service = 'https://kurtcms.org',
    contact = {
        'name': 'Kurt CM See',
        'url': 'https://kurtcms.org',
        'email': 'kurtcms@gmail.com'
    },
    license_info = {
        'name': 'GPL-2.0 License',
        'url': 'https://www.gnu.org/licenses/gpl-2.0.html'
    }
)

@app.get(
    '/pingapi/{ip}',
    response_model = rtt_model,
    response_description = 'The RTT, jitter and packet loss measured',
    summary = 'Return the round trip time (RTT), jitter and packet loss'
)
async def pingapi_get(
    ip: str,
    c: Optional[int] = Query(5, gt = 0, le = 60),
    token: str = Depends(token_auth_scheme)
):
    '''
    Returns a JSON with the following:
    - **date_time**: Date and time of the request
    - **ip_host**: The IP address or hostname provided
    - **rtt_mean**: The average RTT (ms) of the measurement
    - **rtt_min**: The minimum RTT (ms) of the measurement
    - **rtt_max**: The maxmimum RTT (ms) of the measurement
    - **jitter**: The jitter (ms) i.e. variation in the RTT measured
    - **count_requested**: The number of ICMP datagram requested for the measurement
    - **count_received**: The number of ICMP datagram received from the measurement
    - **packet_loss**: The number of packet loss (%) of the measurement
    '''
    auth = verify_token(token.credentials).verify()

    if auth.get('status') == 'error':
        raise exception_model(
            msg = auth.get('msg')
        )

    pingapi_json = await pingapi(ip, c)
    return pingapi_json

@app.post(
    '/pingapi/',
    response_model = rtt_model,
    response_description = 'The RTT, jitter and packet loss measured',
    summary = 'Return the round trip time (RTT), jitter and packet loss'
)
async def pingapi_post(
    ip_model: ip_model,
    token: str = Depends(token_auth_scheme)
):
    '''
    Returns a JSON with the following:
    - **date_time**: Date and time of the request
    - **ip_host**: The IP address or hostname provided
    - **rtt_mean**: The average RTT (ms) of the measurement
    - **rtt_min**: The minimum RTT (ms) of the measurement
    - **rtt_max**: The maxmimum RTT (ms) of the measurement
    - **jitter**: The jitter (ms) i.e. variation in the RTT measured
    - **count_requested**: The number of ICMP datagram requested for the measurement
    - **count_received**: The number of ICMP datagram received from the measurement
    - **packet_loss**: The number of packet loss (%) of the measurement
    '''
    auth = verify_token(token.credentials).verify()

    if auth.get('status') == 'error':
        raise exception_model(
            msg = auth.get('msg')
        )

    pingapi_json = await pingapi(ip_model.ip, ip_model.c)
    return pingapi_json

@app.exception_handler(exception_model)
async def exception_handler(request: Request, exception: exception_model):
    '''
    Return a HTTP 400 Bad Request status code with the error message in JSON
    '''
    return JSONResponse(
        status_code = 400,
        content = {'message': exception.msg}
    )

async def pingapi(ip: str, count: int):
    '''
    Return the round trip time (RTT), jitter and packet loss
    measured by ping given an IP address or hostname and
    the number of ICMP datagram for the measurement. A Bash
    script is employed to execute ping and converts the output
    at runtime to comma separated values (CSV) . The source code
    for which is available at https://github.com/kurtcms/pingc.
    '''
    proc = await asyncio.create_subprocess_shell(
        f'./pingc/pingc {ip} -c {count}',
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()

    if stderr:
        raise exception_model(
            msg = stderr.decode()
        )

    pingapi_stdout = stdout.decode()

    if pingapi_stdout == '\n':
        # Raise error if nil is returned
        raise exception_model(
            msg = 'IP or hostname does not reply to ICMP echo'
        )

    try:
        pingapi_df = pd.read_csv(StringIO(pingapi_stdout), delimiter=',',
                names=['date_time', 'date_time_epoch', 'ip_host', 'rtt'])
    except pd.errors.ParserError:
        # Raise error pandas throws error from parsing
        raise exception_model(
            msg = 'Error parsing the ICMP echo replies'
        )

    if len(pingapi_df) == 0:
        # Raise error if the dataframe has no row
        raise exception_model(
            msg = 'No ICMP echo reply received'
        )

    if (pingapi_df['ip_host'] == pingapi_df['ip_host']).all() == False:
        # Raise error if there is more that one ip_host returned
        raise exception_model(
            msg = 'More than one IP or hostname returned from the result'
        )

    count_received = pingapi_df['date_time_epoch'].count()
    rtt_std = pingapi_df['rtt'].std()
    return {
        'date_time': str(pingapi_df['date_time'][0]),
        'ip_host': str(pingapi_df['ip_host'][0]),
        'rtt_mean': round(pingapi_df['rtt'].mean(), 2),
        'rtt_min': round(pingapi_df['rtt'].min(), 2),
        'rtt_max': round(pingapi_df['rtt'].max(), 2),
        'jitter': 0.00 if pd.isna(rtt_std) else rtt_std,
        'count_requested': count,
        'count_received': count_received,
        'packet_loss': round((1 - count_received / count) * 100, 2)
    }
