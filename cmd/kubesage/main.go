package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	"kubesage/pkg/k8s"
	mcpserver "kubesage/pkg/mcp"
)

func main() {
	// Setup file logging for MCP server debugging
	logFile, err := os.OpenFile("mcp-server.log", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err == nil {
		log.SetOutput(logFile)
	} else {
		log.Printf("Failed to open log file, falling back to stderr: %v", err)
	}

	// Initialize K8s client
	k8sClient, err := k8s.NewClient()
	if err != nil {
		log.Fatalf("Failed to initialize Kubernetes client: %v", err)
	}

	// Create KubeSage MCP Server
	server, err := mcpserver.NewServer(k8sClient)
	if err != nil {
		log.Fatalf("Failed to initialize MCP Server: %v", err)
	}

	// Setup context for graceful shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle signals for graceful shutdown
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigCh
		log.Println("Received termination signal, shutting down...")
		cancel()
	}()

	// We use the standard stdio transport for the MCP server
	transport := &mcp.StdioTransport{}

	if err := server.Start(ctx, transport); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}
