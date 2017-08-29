import java.text.SimpleDateFormat

def today = new SimpleDateFormat('yyyy-MM-dd').format(new Date())
def key_name = "james-jenkins"
def server_ip = ''
def server_id = ''
def server_status = ''
def admin_password = 'jenkinstesting'



pipeline {
    agent any

    stages {

        stage('Cleanup') {
            steps {
                deleteDir()
            }
        }

        stage('Provision OSA VM') {
            steps {
                sh """
                    set +x
                    . ~/openrc
                    set -x

                    python ~/lib/provision-aio.py \
                        --flavor-id ${server_flavor} \
                        --image-id ${server_image} \
                        --key-name ${key_name} \
                        ${server_name}
                """
                script {
                    server_ip = readFile('server-ip')
                    server_id = readFile('server-id')
                    server_status = readFile('server-status')
                }
            }
        }

        stage('Bootstrapping Ansible') {
            steps {
                sh """
                    |ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${server_ip} <<-'ENDSSH'
                    |    set -e
                    |    apt-get update
                    |    git clone https://git.openstack.org/openstack/openstack-ansible /opt/openstack-ansible
                    |    cd /opt/openstack-ansible
                    |    git checkout ${osa_branch}
                    |    ./scripts/bootstrap-ansible.sh
                    |ENDSSH
                """.stripMargin()
            }
        }

        stage('Bootstrapping AIO') {
            steps {
                sh """
                    |ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${server_ip} <<-'ENDSSH'
                    |    set -e
                    |    cd /opt/openstack-ansible
                    |    ./scripts/bootstrap-aio.sh
                    |ENDSSH
                """.stripMargin()
            }
        }

        stage ('Running Playbooks') {
            steps {
                sh """
                    |ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${server_ip} <<-'ENDSSH'
                    |    set -e
                    |    # Change admin password
                    |    sed -i 's/^keystone_auth_admin_password.*/keystone_auth_admin_password: ${admin_password}/' /etc/openstack_deploy/user_secrets.yml
                    |ENDSSH
                """.stripMargin()

                sh """
                    |ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${server_ip} <<-'ENDSSH'
                    |    set -e
                    |    cd /opt/openstack-ansible
                    |    ./scripts/run-playbooks.sh
                    |ENDSSH

                    |ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${server_ip} <<-'ENDSSH'
                    |set -e
                    |    cd /opt/openstack-ansible/playbooks
                    |    openstack-ansible os-tempest-install.yml
                    |ENDSSH
                """.stripMargin()
            }
        }

        stage('Setup Environment') {
            steps {
                sh """
                    export OS_USERNAME=admin
                    export OS_INTERFACE=publicURL
                    export OS_PASSWORD=${admin_password}
                    export OS_PROJECT_NAME=admin
                    export OS_TENANT_NAME=admin
                    export OS_PROJECT_DOMAIN_NAME=Default
                    export OS_USER_DOMAIN_NAME=Default
                    export OS_AUTH_URL=https://${server_ip}:5000/v3
                    export OS_IDENTITY_API_VERSION=3
                    export OS_AUTH_VERSION=3

                    openstack --insecure security group list -f json > security-groups.json
                    openstack --insecure project list -f json > projects.json
                    SECURITY_GROUP_ID=\$(python ~/lib/get-security-group.py projects.json security-groups.json)

                    echo "Security group id is \${SECURITY_GROUP_ID}"
                    openstack --insecure security group rule list \${SECURITY_GROUP_ID}
                    # Update security group to include ssh
                    openstack --insecure security group rule create \${SECURITY_GROUP_ID} --protocol tcp --dst-port 22
                """
            } // Steps
        } // Stage
    } // Stages

    post {
        always {
            echo "Server name: ${server_name}"
            echo "AIO server IP: ${server_ip}"
            echo "Admin password: ${admin_password}"
            echo "Osa branch: ${osa_branch}"
        }
    }
}
