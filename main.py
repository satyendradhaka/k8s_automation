import argparse

from deployment_status import getDeploymentHealthStatus, getDeploymentDetails
from setup_cluster import connectToKubernetesCluster, installHelm, installKEDA, summarizeClusterSetup, \
    installMetricServer
from create_deployment import createHelmCommand, createDeployment


def main():
    parser = argparse.ArgumentParser(description="Kubernetes Cluster Setup and Deployment")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Subparser for the connect command
    connect_parser = subparsers.add_parser('connect', help='Connect to Kubernetes cluster')
    connect_parser.add_argument('--config', type=str, default="~/.kube/config", help='Path to the kubeconfig file')

    # Subparser for the create_deployment command
    deploy_parser = subparsers.add_parser('create_deployment', help='Create a deployment in the Kubernetes cluster')
    deploy_parser.add_argument('--namespace', required=True, help='The Kubernetes namespace')
    deploy_parser.add_argument('--release_name', required=True, help='The name of the Helm release')
    deploy_parser.add_argument('--set', action='append', help='Helm set parameters')
    deploy_parser.add_argument('--values_file', type=str, help='Path to the values file')

    # Subparser for the get_deployment_status command
    status_parser = subparsers.add_parser('get_deployment_status', help='Get deployment health status')
    status_parser.add_argument('--release_name', required=True, help='The name of the Helm release')
    status_parser.add_argument('--namespace', required=True, help='The Kubernetes namespace')

    args = parser.parse_args()

    if args.command == 'connect':
        configFilePath = args.config
        if connectToKubernetesCluster(configFilePath):
            installHelm()
            installKEDA()
            installMetricServer()
            summarizeClusterSetup()

    elif args.command == 'create_deployment':
        helm_args = {
            'namespace': args.namespace,
            'release_name': args.release_name
        }

        if args.values_file:
            helm_args['values_file'] = args.values_file

        if args.set:
            for set_arg in args.set:
                key, value = set_arg.split('=')
                helm_args[key] = value

        helm_command = createHelmCommand(**helm_args)
        if createDeployment(helm_command, args.release_name, "automation-chart"):
            getDeploymentDetails(args.release_name, args.namespace)

    elif args.command == 'get_deployment_status':
        release_name = args.release_name
        namespace = args.namespace
        getDeploymentHealthStatus(release_name, namespace)


if __name__ == '__main__':
    main()
