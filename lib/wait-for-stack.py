import argparse
import os
import time

from keystoneauth1 import loading
from keystoneauth1 import session
from heatclient import client

_TERMINAL = [
    'CREATE_FAILED',
    'CREATE_COMPLETE',
    'UPDATE_FAILED',
    'UPDATE_COMPLETE'
]
_INTERVAL = 20


def get_session():
    """Get a keystone session

    :returns: Keystone session
    :rtype: session.Session
    """
    loader = loading.get_plugin_loader('password')
    auth = loader.load_from_options(
        auth_url=os.environ.get('OS_AUTH_URL'),
        username=os.environ.get('OS_USERNAME'),
        password=os.environ.get('OS_PASSWORD'),
        project_name=os.environ.get('OS_PROJECT_NAME'),
        project_domain_name=os.environ.get('OS_PROJECT_DOMAIN_NAME'),
        user_domain_name=os.environ.get('OS_USER_DOMAIN_NAME')
    )
    return session.Session(auth=auth, verify=False)


def get_heat():
    """Get instance of heat client.

    :returns: Heat client instance.
    :rtype: heatclient.client.Client
    """
    return client.Client('1', session=get_session())


parser = argparse.ArgumentParser()
parser.add_argument('stack', type=str, help='Name or ID of stack')
parser.add_argument(
    'timeout',
    type=int,
    help='How many seconds to wait for Create Complete Status.'
)
args = parser.parse_args()
heat = get_heat()

start = time.time()

while time.time() - start < args.timeout:
    stack = heat.stacks.get(args.stack)
    status = stack.stack_status
    print "Status of {} is {}".format(args.stack, stack.stack_status)
    if status in _TERMINAL:
        if status == 'CREATE_COMPLETE':
            exit()
        else:
            raise Exception(
                "Unexpected terminal status {} for stack {}."
                .format(status, args.stack)
            )
    else:
        time.sleep(_INTERVAL)

raise Exception("Ran out of time waiting for stack {}.".format(args.stack))
