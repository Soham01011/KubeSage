package mcp

import (
	"context"
	"fmt"
	"log"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	"kubesage/pkg/handlers"
	"kubesage/pkg/k8s"
)

type Server struct {
	mcpServer       *mcp.Server
	resourceHandler *handlers.ResourceHandler
	podHandler      *handlers.PodHandler
	eventHandler    *handlers.EventHandler
}

func NewServer(k8sClient *k8s.Client) (*Server, error) {
	rh, err := handlers.NewResourceHandler(k8sClient)
	if err != nil {
		return nil, fmt.Errorf("failed to create resource handler: %w", err)
	}
	ph := handlers.NewPodHandler(k8sClient)
	eh := handlers.NewEventHandler(k8sClient)

	// Create MCP server
	s := mcp.NewServer(&mcp.Implementation{
		Name:    "KubeSage",
		Version: "1.0.0",
	}, nil)

	srv := &Server{
		mcpServer:       s,
		resourceHandler: rh,
		podHandler:      ph,
		eventHandler:    eh,
	}

	srv.registerTools()

	return srv, nil
}

func (s *Server) Start(ctx context.Context, transport mcp.Transport) error {
	log.Println("Starting KubeSage MCP Server...")
	return s.mcpServer.Run(ctx, transport)
}

type ResourceArgs struct {
	Resource  string `json:"resource" description:"The Kubernetes resource type (e.g. deployments, services)"`
	Namespace string `json:"namespace,omitempty" description:"The namespace. Defaults to 'default' if not provided"`
}

type ResourceNameArgs struct {
	Resource  string `json:"resource" description:"The Kubernetes resource type"`
	Namespace string `json:"namespace,omitempty" description:"The namespace. Defaults to 'default'"`
	Name      string `json:"name" description:"The name of the resource"`
}

type ApplyArgs struct {
	YAML string `json:"yaml" description:"The YAML or JSON manifest to apply"`
}

type PodLogsArgs struct {
	Namespace string `json:"namespace,omitempty" description:"The namespace. Defaults to 'default'"`
	PodName   string `json:"podName" description:"The name of the pod"`
	TailLines *int64 `json:"tailLines,omitempty" description:"Lines of recent log file to display"`
}

type ExecArgs struct {
	Namespace string   `json:"namespace,omitempty"`
	PodName   string   `json:"podName"`
	Container string   `json:"container,omitempty"`
	Command   []string `json:"command"`
}

type EventArgs struct {
	Namespace          string `json:"namespace,omitempty"`
	InvolvedObjectName string `json:"involvedObjectName,omitempty" description:"Optional. Filter events by the involved object name"`
}

func (s *Server) registerTools() {
	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "list_resources",
		Description: "List resources of a specific type in a namespace",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ResourceArgs) (*mcp.CallToolResult, any, error) {
		res, err := s.resourceHandler.ListResources(ctx, args.Resource, args.Namespace)
		return nil, res, err
	})

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "get_resource",
		Description: "Get details of a specific Kubernetes resource",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ResourceNameArgs) (*mcp.CallToolResult, any, error) {
		res, err := s.resourceHandler.GetResource(ctx, args.Resource, args.Namespace, args.Name)
		return nil, res, err
	})

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "describe_resource",
		Description: "Describe a specific Kubernetes resource",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ResourceNameArgs) (*mcp.CallToolResult, any, error) {
		res, err := s.resourceHandler.DescribeResource(ctx, args.Resource, args.Namespace, args.Name)
		return nil, res, err
	})

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "delete_resource",
		Description: "Delete a specific Kubernetes resource",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ResourceNameArgs) (*mcp.CallToolResult, any, error) {
		res, err := s.resourceHandler.DeleteResource(ctx, args.Resource, args.Namespace, args.Name)
		return nil, res, err
	})

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "apply_yaml",
		Description: "Apply a JSON/YAML manifest to the cluster",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ApplyArgs) (*mcp.CallToolResult, any, error) {
		res, err := s.resourceHandler.ApplyYAML(ctx, args.YAML)
		return nil, res, err
	})

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "get_logs",
		Description: "Get logs from a specific pod",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args PodLogsArgs) (*mcp.CallToolResult, any, error) {
		res, err := s.podHandler.GetLogs(ctx, args.Namespace, args.PodName, args.TailLines)
		return nil, res, err
	})

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "exec_in_pod",
		Description: "Execute a command inside a pod",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ExecArgs) (*mcp.CallToolResult, any, error) {
		res, err := s.podHandler.ExecInPod(ctx, args.Namespace, args.PodName, args.Container, args.Command)
		return nil, res, err
	})

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "get_events",
		Description: "Get cluster events optionally filtered by namespace or involved object name",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args EventArgs) (*mcp.CallToolResult, any, error) {
		res, err := s.eventHandler.GetEvents(ctx, args.Namespace, args.InvolvedObjectName)
		return nil, res, err
	})
}
