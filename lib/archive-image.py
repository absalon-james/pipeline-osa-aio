import argparse
import datetime

from swiftclient.service import SwiftService
from swiftclient.service import SwiftUploadObject


# Special swift header:  X-Container-Meta-Web-Index
# Special swift header: X-Container-Meta-Web-Listings: true"


def default_date():
    """Get default date in iso8601 string form.

    :returns: Today in utctime in is8601 format.
    :rtype: str
    """
    return datetime.datetime.utcnow().date().isoformat()


def check_format(f):
    """Check the output format.

    The format should have a __DATE__ placeholder which
    will be replaced with the default date or date provided
    via arguments.

    :param f: Format to check
    :type f: str
    """
    if '__DATE__' not in f:
        raise Exception(
            "Invalid format. Format must contain __DATE__ placeholder."
        )


def check_swift_error(resp):
    if resp.get('error'):
        raise resp.get('error')


def split_container_name(name):
    return name.split('/', 1)


def post_container(swift, container):
    """Ensure that the target container exists.

    :param swift: Instance of swift service.
    :type swift: swiftclient.service.SwiftService
    :param container: Name of the target container
    :type container: str
    """
    options = {"header": ["X-Container-Meta-Web-Listings: true"]}
    resp = swift.post(container=container, options=options)
    check_swift_error(resp)


def list_container(swift, container):
    """Get list of container contents.

    :param swift: Instance of swift service
    :type swift: swiftclient.service.SwiftService
    :param container: Name of the target container
    :type container: str
    :returns: List of dictionaries describing contents
    :rtype: list
    """
    root_container, prefix = split_container_name(container)
    objs = []
    pages = swift.list(container=root_container)
    for page in pages:
        check_swift_error(page)
        if page["success"]:
            for item in page["listing"]:
                if item['content_type'] == 'application/octet-stream' and \
                        item['name'].startswith(prefix):
                    objs.append(item)
    return objs


def trim_container(swift, container, remove_list):
    """Remove objects in remove_list from the container.

    :param swift: Instance of swift service
    :type swift: swiftclient.service.SwiftService
    :param container: Name of the target container
    :type container: str
    :param remove_list: List of objects to remove
    :type remove_list: list
    """
    root_container, _ = split_container_name(container)
    names = [i['name'] for i in remove_list]
    deletes = swift.delete(container=root_container, objects=names)
    for delete in deletes:
        check_swift_error(delete)


def upload_object(swift, args):
    """Upload an object to swift

    :param swift: Instance of swift service
    :type swift: swiftclient.service.SwiftService
    :param args: Parsed arguments object from argparse
    :type args: obj
    """
    o_name = args.format.replace('__DATE__', args.date)
    obj = SwiftUploadObject(args.object, object_name=o_name)
    resp = swift.upload(args.container, [obj])
    for r in resp:
        check_swift_error(r)


parser = argparse.ArgumentParser()
parser.add_argument('container', type=str, help="name of container")
parser.add_argument(
    'format',
    type=str,
    help="Archive format. Example xenial-heat-agents-__DATE__.qcow2"
)
parser.add_argument(
    'object',
    type=str,
    help="File to archive."
)
parser.add_argument(
    '--date',
    type=str,
    default=default_date(),
    help="Date to use"
)
parser.add_argument(
    '--limit',
    type=int,
    default=10,
    help="Keep only the most recent n items. Defaults to 10."
)
args = parser.parse_args()

check_format(args.format)

with SwiftService() as swift:

    print "Ensuring container {} exists.".format(args.container)

    # Make sure container exists:
    post_container(swift, args.container)

    print "Uploading file {} to container {}".format(
        args.object,
        args.container
    )

    # Upload the new object
    upload_object(swift, args)

    print "Listing contents of container {}".format(args.container)

    # Get list of files in container
    l = list_container(swift, args.container)

    for i in l:
        print i.get('name')

    l = list(reversed(sorted(l, key=lambda o: o['name'])))
    if len(l) > args.limit:
        remove_list = l[args.limit:]
    else:
        remove_list = []

    print "Need to delete: "
    for i in remove_list:
        print "Deleting ", i.get('name')

    if remove_list:
        trim_container(swift, args.container, remove_list)
