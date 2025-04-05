import argparse
from setup_cluster import connectToKubernetesCluster, installHelm, installKEDA, summarizeClusterSetup
from create_deployment import createHelmCommand, createDeployment, getDeploymentDetails


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

    args = parser.parse_args()

    if args.command == 'connect':
        configFilePath = args.config
        if connectToKubernetesCluster(configFilePath):
            installHelm()
            installKEDA()
            summarizeClusterSetup()

    elif args.command == 'create_deployment':
        helm_args = {
            'namespace': args.namespace,
            'release_name': args.release_name
        }
        if args.set:
            for set_arg in args.set:
                key, value = set_arg.split('=')
                helm_args[key] = value

        helm_command = createHelmCommand(**helm_args)
        if createDeployment(helm_command, args.release_name, "automation-chart"):
            deploymentDetails = getDeploymentDetails(args.release_name, args.namespace)
            print(deploymentDetails)


if __name__ == '__main__':
    main()
