import argparse
import os
import time
from keystoneauth1 import loading
from keystoneauth1 import session
from novaclient import client as novaclient


def get_session():
    auth_kwargs = {
        'auth_url': os.environ.get('OS_AUTH_URL'),
        'username': os.environ.get('OS_USERNAME'),
        'password': os.environ.get('OS_PASSWORD'),
        'project_id': os.environ.get('OS_PROJECT_ID'),
    }
    loader = loading.get_plugin_loader('password')
    auth = loader.load_from_options(**auth_kwargs)
    return session.Session(auth=auth)


def get_nova(version="2.1"):
    region_name = os.environ.get('OS_REGION_NAME', 'dfw')
    return novaclient.Client(
        version,
        session=get_session(),
        region_name=region_name
    )


def create(nova, name, flavor_id, image_id, key_name):
    return nova.servers.create(name, image_id, flavor_id, key_name=key_name)


def save(server):
    with open('server-ip', 'w') as f:
        f.write(server.accessIPv4)
    with open('server-id', 'w') as f:
        f.write(server.id)
    with open('server-status', 'w') as f:
        f.write(server.status)


def wait_for_active(nova, server, timeout=600):
    start = time.time()
    now = start

    while now - start < timeout:
        print "Waiting for status for server {}".format(server.name)
        server = nova.servers.get(server)
        print "\tGot {}".format(server.status)
        save(server)
        if server.status == 'ACTIVE':
            return True
        time.sleep(15)
    raise Exception(
        "Server creation exceeded timeout of {} seconds."
        .format(timeout)
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Provision a public cloud vm for osa aio.'
    )
    parser.add_argument('server_name', type=str, help='Name of the new vm.')
    parser.add_argument('--flavor-id', type=str, help='Id of the flavor.')
    parser.add_argument('--image-id', type=str, help='Id of the image.')
    parser.add_argument('--key-name', type=str, help='Name of the keypair.')
    parser.add_argument(
        '--timeout',
        type=int,
        help='Length of time in seconds to wait for vm to go to ACTIVE status'
    )
    args = parser.parse_args()

    SERVER_NAME = os.environ.get('SERVER_NAME', 'james-osa-heat-testing')
    # 15GB Standard Instance = 7
    LAVOR_ID = os.environ.get('FLAVOR_ID', '7')
    IMAGE_ID = os.environ.get(
        'IMAGE_ID',
        'f5046581-62ab-4078-8d4d-ce09e5de1e93'
    )
    KEY_NAME = os.environ.get('KEY_NAME', 'james-key-xps')
    TIMEOUT = int(os.environ.get('TIMEOUT', '600'))
    nova = get_nova()
    server = create(
        nova,
        args.server_name,
        args.flavor_id,
        args.image_id,
        args.key_name
    )
    wait_for_active(nova, server)
