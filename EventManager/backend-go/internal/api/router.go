package api

import (
	"github.com/gin-gonic/gin"
	"github.com/hibiken/asynq"
	"gorm.io/gorm"

	"event-flow/internal/api/handler"
	"event-flow/internal/api/middleware"
	"event-flow/internal/repository"
	"event-flow/internal/tasklab"
	"event-flow/internal/worker"
)

// SetupRouter creates the Gin engine and registers all routes.
func SetupRouter(
	db *gorm.DB,
	eventRepo *repository.EventRepo,
	logRepo *repository.EventLogRepo,
	dispatcher worker.Dispatcher,
	inspector *asynq.Inspector,
	client *asynq.Client,
	docsDir string,
	outputDir string,
	statusStore *tasklab.StatusStore,
) *gin.Engine {
	r := gin.New()
	r.Use(middleware.Recovery(), middleware.Logger(), middleware.CORS())

	// ── Create handlers ─────────────────────────────────────────
	eventsH := handler.NewEventsHandler(eventRepo, logRepo, dispatcher)
	statsH := handler.NewStatsHandler(eventRepo, inspector)
	handlersH := handler.NewHandlersHandler(eventRepo, db)
	testLabH := handler.NewTestLabHandler(client, inspector, eventRepo, db, outputDir, statusStore)
	docsH := handler.NewDocsHandler(docsDir)

	v1 := r.Group("/api/v1")

	// ── /api/v1/events ──────────────────────────────────────────
	// IMPORTANT: specific routes BEFORE :event_id parameterised routes
	events := v1.Group("/events")
	{
		// Batch + DLQ replay (register before :event_id!)
		events.POST("/batch", eventsH.BatchCreateEvents)
		events.POST("/dlq/replay", eventsH.ReplayDLQ)

		// CRUD
		events.POST("", eventsH.CreateEvent)
		events.GET("", eventsH.ListEvents)

		// Parameterised routes
		events.GET("/:event_id", eventsH.GetEvent)
		events.GET("/:event_id/logs", eventsH.GetEventLogs)
		events.POST("/:event_id/retry", eventsH.RetryEvent)
	}

	// ── /api/v1/stats ───────────────────────────────────────────
	stats := v1.Group("/stats")
	{
		stats.GET("", statsH.GetStats)
		stats.GET("/queues", statsH.QueueStats)
		stats.GET("/workers", statsH.WorkerStats)
		stats.GET("/throughput", statsH.ThroughputStats)
		stats.GET("/recent-failures", statsH.RecentFailures)
	}

	// ── /api/v1/handlers ────────────────────────────────────────
	handlers := v1.Group("/handlers")
	{
		handlers.GET("", handlersH.ListHandlers)
		handlers.GET("/event-types", handlersH.ListEventTypes)
	}

	// ── /api/v1/test-lab ────────────────────────────────────────
	testLab := v1.Group("/test-lab")
	{
		testLab.GET("/tasks", testLabH.ListTasks)
		testLab.POST("/trigger", testLabH.TriggerTask)
		testLab.GET("/status/:celery_task_id", testLabH.GetTaskStatus)
		testLab.GET("/preview", testLabH.PreviewFile)
	}

	// ── /api/v1/docs ────────────────────────────────────────────
	docs := v1.Group("/docs")
	{
		docs.GET("", docsH.ListDocs)
		docs.GET("/:filename", docsH.GetDoc)
	}

	return r
}
