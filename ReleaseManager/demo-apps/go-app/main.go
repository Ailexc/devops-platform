package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"runtime"
)

var (
	appVersion = getEnv("APP_VERSION", "1.0.0")
	appName    = getEnv("APP_NAME", "go-demo")
	env        = getEnv("ENV", "dev")
)

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func rootHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"app":      appName,
		"version":  appVersion,
		"env":      env,
		"language": "Go",
		"host":     getHostname(),
	})
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "ok",
		"app":     appName,
		"version": appVersion,
	})
}

func infoHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"app":        appName,
		"version":    appVersion,
		"env":        env,
		"go_version": runtime.Version(),
		"platform":   runtime.GOOS + "/" + runtime.GOARCH,
	})
}

func getHostname() string {
	host, _ := os.Hostname()
	return host
}

func main() {
	http.HandleFunc("/", rootHandler)
	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/info", infoHandler)

	port := getEnv("PORT", "8080")
	fmt.Printf("Go demo app starting on :%s\n", port)
	http.ListenAndServe(":"+port, nil)
}