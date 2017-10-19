import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument(
    'projects_file',
    type=str,
    help='File location of json formatted list of projects.'
)
parser.add_argument(
    'security_groups_file',
    type=str,
    help='File location of json formatted list of security groups.'
)

if __name__ == '__main__':
    args = parser.parse_args()

    project_id = None
    with open(args.projects_file, 'r') as f:
        projects = json.loads(f.read())
    for p in projects:
        if p['Name'] == 'admin':
            project_id = p['ID']
            break

    security_group_id = None
    with open(args.security_groups_file, 'r') as f:
        security_groups = json.loads(f.read())
    for sg in security_groups:
        if sg['Name'] == 'default' and sg['Project'] == project_id:
            security_group_id = sg['ID']

    if not security_group_id:
        raise Exception(
            "Unable to locate default security group for project admin."
        )
    print security_group_id
