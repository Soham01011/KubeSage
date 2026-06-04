package handlers

import (
	"context"
	"encoding/json"
	"fmt"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"kubesage/pkg/k8s"
)

type EventHandler struct {
	client *k8s.Client
}

func NewEventHandler(client *k8s.Client) *EventHandler {
	return &EventHandler{client: client}
}

func (h *EventHandler) GetEvents(ctx context.Context, namespace, involvedObjectName string) (string, error) {
	if namespace == "" {
		namespace = "default"
	}

	opts := metav1.ListOptions{}
	if involvedObjectName != "" {
		// FieldSelector to filter events by involved object name
		opts.FieldSelector = fmt.Sprintf("involvedObject.name=%s", involvedObjectName)
	}

	events, err := h.client.Clientset.CoreV1().Events(namespace).List(ctx, opts)
	if err != nil {
		return "", err
	}

	var formattedEvents []string
	for _, e := range events.Items {
		formattedEvents = append(formattedEvents, fmt.Sprintf("[%s] %s/%s %s: %s", 
			e.LastTimestamp.String(), 
			e.InvolvedObject.Kind, 
			e.InvolvedObject.Name, 
			e.Reason, 
			e.Message))
	}

	if len(formattedEvents) == 0 {
		return "No events found.", nil
	}

	// Just return simplified JSON or name list
	b, _ := json.MarshalIndent(formattedEvents, "", "  ")
	return string(b), nil
}
