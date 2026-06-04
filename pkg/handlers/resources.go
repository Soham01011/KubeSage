package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/discovery"
	"k8s.io/client-go/discovery/cached/memory"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/restmapper"
	"kubesage/pkg/k8s"
)

type ResourceHandler struct {
	client *k8s.Client
	mapper meta.RESTMapper
}

func NewResourceHandler(client *k8s.Client) (*ResourceHandler, error) {
	dc, err := discovery.NewDiscoveryClientForConfig(client.Config)
	if err != nil {
		return nil, err
	}
	mapper := restmapper.NewDeferredDiscoveryRESTMapper(memory.NewMemCacheClient(dc))
	return &ResourceHandler{
		client: client,
		mapper: mapper,
	}, nil
}

func (h *ResourceHandler) getGVR(resource string) (schema.GroupVersionResource, error) {
	gvr, err := h.mapper.ResourceFor(schema.GroupVersionResource{Resource: resource})
	if err != nil {
		// Fallback for case sensitivity or common aliases if needed
		return schema.GroupVersionResource{}, fmt.Errorf("failed to map resource '%s': %w", resource, err)
	}
	return gvr, nil
}

func (h *ResourceHandler) ListResources(ctx context.Context, resource, namespace string) (string, error) {
	gvr, err := h.getGVR(resource)
	if err != nil {
		return "", err
	}

	var res dynamic.ResourceInterface
	if namespace != "" {
		res = h.client.Dynamic.Resource(gvr).Namespace(namespace)
	} else {
		res = h.client.Dynamic.Resource(gvr)
	}

	list, err := res.List(ctx, metav1.ListOptions{})
	if err != nil {
		return "", err
	}

	// Just return simplified JSON or name list
	var items []map[string]interface{}
	for _, item := range list.Items {
		items = append(items, map[string]interface{}{
			"name":      item.GetName(),
			"namespace": item.GetNamespace(),
			"kind":      item.GetKind(),
		})
	}

	b, _ := json.MarshalIndent(items, "", "  ")
	return string(b), nil
}

func (h *ResourceHandler) GetResource(ctx context.Context, resource, namespace, name string) (string, error) {
	gvr, err := h.getGVR(resource)
	if err != nil {
		return "", err
	}

	var res dynamic.ResourceInterface
	if namespace != "" {
		res = h.client.Dynamic.Resource(gvr).Namespace(namespace)
	} else {
		res = h.client.Dynamic.Resource(gvr)
	}

	item, err := res.Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return "", err
	}

	b, _ := json.MarshalIndent(item.Object, "", "  ")
	return string(b), nil
}

func (h *ResourceHandler) DescribeResource(ctx context.Context, resource, namespace, name string) (string, error) {
	// A true "kubectl describe" is very complex. 
	// For an LLM, getting the full object plus events is usually sufficient.
	gvr, err := h.getGVR(resource)
	if err != nil {
		return "", err
	}

	var res dynamic.ResourceInterface
	if namespace != "" {
		res = h.client.Dynamic.Resource(gvr).Namespace(namespace)
	} else {
		res = h.client.Dynamic.Resource(gvr)
	}

	item, err := res.Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return "", err
	}

	// Just return full JSON for now. The LLM can interpret the spec, status, and metadata easily.
	b, _ := json.MarshalIndent(item.Object, "", "  ")
	return string(b), nil
}

func (h *ResourceHandler) DeleteResource(ctx context.Context, resource, namespace, name string) (string, error) {
	gvr, err := h.getGVR(resource)
	if err != nil {
		return "", err
	}

	var res dynamic.ResourceInterface
	if namespace != "" {
		res = h.client.Dynamic.Resource(gvr).Namespace(namespace)
	} else {
		res = h.client.Dynamic.Resource(gvr)
	}

	err = res.Delete(ctx, name, metav1.DeleteOptions{})
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Successfully deleted %s %s in namespace %s", resource, name, namespace), nil
}

func (h *ResourceHandler) ApplyYAML(ctx context.Context, yamlContent string) (string, error) {
	// For apply, we typically need to parse the YAML into an Unstructured object
	// and then use the dynamic client to Create or Update it.
	// For simplicity in this demo, let's just parse the JSON/YAML and apply it.
	// In a robust implementation, k8s.io/cli-runtime is used.
	
	// Convert yaml string to Unstructured map
	obj := &unstructured.Unstructured{}
	err := json.Unmarshal([]byte(yamlContent), &obj.Object) // expecting JSON format for now for simplicity
	if err != nil {
		return "", fmt.Errorf("failed to parse content (make sure it's valid JSON for now): %w", err)
	}
	
	gvk := obj.GroupVersionKind()
	mapping, err := h.mapper.RESTMapping(gvk.GroupKind(), gvk.Version)
	if err != nil {
		return "", err
	}
	
	namespace := obj.GetNamespace()
	if namespace == "" {
		namespace = "default"
	}
	
	var res dynamic.ResourceInterface
	if mapping.Scope.Name() == meta.RESTScopeNameNamespace {
		res = h.client.Dynamic.Resource(mapping.Resource).Namespace(namespace)
	} else {
		res = h.client.Dynamic.Resource(mapping.Resource)
	}
	
	// Try Create, if exists, fall back to Update (simplified Apply)
	created, err := res.Create(ctx, obj, metav1.CreateOptions{})
	if err != nil {
		if strings.Contains(err.Error(), "already exists") {
			// Update requires getting the resourceVersion first
			existing, getErr := res.Get(ctx, obj.GetName(), metav1.GetOptions{})
			if getErr != nil {
				return "", fmt.Errorf("resource exists but failed to get it: %w", getErr)
			}
			obj.SetResourceVersion(existing.GetResourceVersion())
			
			_, updateErr := res.Update(ctx, obj, metav1.UpdateOptions{})
			if updateErr != nil {
				return "", fmt.Errorf("failed to update resource: %w", updateErr)
			}
			return fmt.Sprintf("Successfully updated %s %s", gvk.Kind, obj.GetName()), nil
		}
		return "", fmt.Errorf("failed to create resource: %w", err)
	}
	
	return fmt.Sprintf("Successfully created %s %s", gvk.Kind, created.GetName()), nil
}
