package handlers

import (
	"bytes"
	"context"
	"fmt"
	"io"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/tools/remotecommand"
	"kubesage/pkg/k8s"
)

type PodHandler struct {
	client *k8s.Client
}

func NewPodHandler(client *k8s.Client) *PodHandler {
	return &PodHandler{client: client}
}

func (h *PodHandler) GetLogs(ctx context.Context, namespace, podName string, tailLines *int64) (string, error) {
	if namespace == "" {
		namespace = "default"
	}

	req := h.client.Clientset.CoreV1().Pods(namespace).GetLogs(podName, &corev1.PodLogOptions{
		TailLines: tailLines,
	})
	
	podLogs, err := req.Stream(ctx)
	if err != nil {
		return "", fmt.Errorf("error in opening stream: %w", err)
	}
	defer podLogs.Close()

	buf := new(bytes.Buffer)
	_, err = io.Copy(buf, podLogs)
	if err != nil {
		return "", fmt.Errorf("error in copy information from podLogs to buf: %w", err)
	}

	return buf.String(), nil
}

func (h *PodHandler) ExecInPod(ctx context.Context, namespace, podName, container string, command []string) (string, error) {
	if namespace == "" {
		namespace = "default"
	}

	req := h.client.Clientset.CoreV1().RESTClient().Post().
		Resource("pods").
		Name(podName).
		Namespace(namespace).
		SubResource("exec").
		VersionedParams(&corev1.PodExecOptions{
			Container: container,
			Command:   command,
			Stdin:     false,
			Stdout:    true,
			Stderr:    true,
			TTY:       false,
		}, scheme.ParameterCodec)

	exec, err := remotecommand.NewSPDYExecutor(h.client.Config, "POST", req.URL())
	if err != nil {
		return "", fmt.Errorf("failed to create executor: %w", err)
	}

	var stdout, stderr bytes.Buffer
	err = exec.StreamWithContext(ctx, remotecommand.StreamOptions{
		Stdout: &stdout,
		Stderr: &stderr,
	})
	if err != nil {
		return "", fmt.Errorf("failed to execute command. Stderr: %s, Error: %w", stderr.String(), err)
	}

	return stdout.String(), nil
}
