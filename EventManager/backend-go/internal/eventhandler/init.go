package eventhandler

import (
	"log"

	"event-flow/internal/eventhandler/types"

	awsHandlers "event-flow/internal/eventhandler/aws"
	internalHandlers "event-flow/internal/eventhandler/internal"
	webhookHandlers "event-flow/internal/eventhandler/webhook"
)

// Init registers all handlers with the global default registry
func Init() {
	RegisterAllHandlers(DefaultRegistry)
	log.Println("Event handler registry initialized")
}

// RegisterAllHandlers registers every handler factory and its metadata on the given registry
func RegisterAllHandlers(r *types.Registry) {
	// ── Handler factories (order matters for first-match) ──────────
	r.Register("aws.ec2.*", awsHandlers.NewEC2Handler)
	r.Register("aws.rds.*", awsHandlers.NewRDSHandler)
	r.Register("aws.s3.*", awsHandlers.NewS3Handler)
	r.Register("webhook.github.*", webhookHandlers.NewGitHubHandler)
	r.Register("internal.health", internalHandlers.NewHealthCheckHandler)
	r.Register("echo.*", internalHandlers.NewEchoHandler)
	r.Register("*", internalHandlers.NewEchoHandler) // fallback — matches anything
}
