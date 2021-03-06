#!groovy

def tryStep(String message, Closure block, Closure tearDown = null) {
    try {
        block()
    }
    catch (Throwable t) {
        slackSend message: "${env.JOB_NAME}: ${message} failure ${env.BUILD_URL}", channel: '#ci-channel', color: 'danger'

        throw t
    }
    finally {
        if (tearDown) {
            tearDown()
        }
    }
}


node {
    stage("Checkout") {
        checkout scm
    }

    stage("Test") {
        tryStep "test", {
            sh "docker-compose -p dcatd -f ./docker-compose.yml up -d database && " +
               "docker-compose -p dcatd -f ./docker-compose.yml build --no-cache --pull test && " +
               "docker-compose -p dcatd -f ./docker-compose.yml run --rm test make test"
        }, {
            sh "docker-compose -p dcatd -f ./docker-compose.yml down"
        }
    }

    stage("Build image") {
        tryStep "build", {
                docker.withRegistry("${DOCKER_REGISTRY_HOST}",'docker_registry_auth') {
                def image = docker.build("datapunt/dcatd:${env.BUILD_NUMBER}")
                image.push()
            }
        }
    }
}

String BRANCH = "${env.BRANCH_NAME}"

if (BRANCH == "master") {

	/*
	node {
	    stage("Update documentation") {
            sh "pip install Sphinx sphinx_rtd_theme sphinx_autodoc_typehints && " +
               "make -C sphinx gh-pages"
	    }
	}
	*/

    node {
        stage('Push acceptance image') {
            tryStep "image tagging", {
                docker.withRegistry("${DOCKER_REGISTRY_HOST}",'docker_registry_auth') {
                def image = docker.image("datapunt/dcatd:${env.BUILD_NUMBER}")
                image.pull()
                image.push("acceptance")
                }
            }
        }
    }

    node {
        stage("Deploy to ACC") {
        tryStep "deployment", {
            build job: 'Subtask_Openstack_Playbook',
            parameters: [
                    [$class: 'StringParameterValue', name: 'INVENTORY', value: 'acceptance'],
                    [$class: 'StringParameterValue', name: 'PLAYBOOK', value: 'deploy.yml'],
                    [$class: 'StringParameterValue', name: 'PLAYBOOKPARAMS', value: "-e cmdb_id=app_dcatd"]
                ]
            }
        }
    }

    stage('Waiting for approval') {
        slackSend channel: '#ci-channel', color: 'warning', message: 'dcatd service is waiting for Production Release - please confirm'
        input "Deploy to Production?"
    }

    node {
        stage('Push production image') {
        tryStep "image tagging", {
                docker.withRegistry("${DOCKER_REGISTRY_HOST}",'docker_registry_auth') {
                    def image = docker.image("datapunt/dcatd:${env.BUILD_NUMBER}")
                    image.pull()
                    image.push("production")
                    image.push("latest")
                }
            }
        }
    }

    node {
        stage("Deploy") {
            tryStep "deployment", {
                build job: 'Subtask_Openstack_Playbook',
                parameters: [
                    [$class: 'StringParameterValue', name: 'INVENTORY', value: 'production'],
                    [$class: 'StringParameterValue', name: 'PLAYBOOK', value: 'deploy.yml'],
                    [$class: 'StringParameterValue', name: 'PLAYBOOKPARAMS', value: "-e cmdb_id=app_dcatd"]
                ]
            }
        }
    }
}
