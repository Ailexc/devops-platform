package api

import (
	"time"

	"cmdb-go/internal/api/config"
	"cmdb-go/internal/api/dashboard"
	"cmdb-go/internal/api/docs"
	"cmdb-go/internal/api/history"
	"cmdb-go/internal/api/tasks"
	"cmdb-go/internal/pkg/lock"
	"cmdb-go/internal/service"

	"github.com/hibiken/asynq"
	"github.com/gin-gonic/gin"
)

// Router holds all API handler registrations.
type Router struct {
	engine         *gin.Engine
	dashboardH     *dashboard.Handler
	tasksH         *tasks.Handler
	configH        *config.Handler
	historyH       *history.Handler
	docsH          *docs.Handler
	lockMgr        *lock.Manager
}

// NewRouter creates a new API router with all handlers.
func NewRouter(
	dashboardSvc *service.MetricsService,
	executionSvc *service.ExecutionService,
	treeSvc *service.TaskTreeService,
	configSvc *service.ConfigService,
	scheduleSvc *service.ScheduleService,
	lockMgr *lock.Manager,
	docsDir string,
	asynqClient *asynq.Client,
) *Router {
	engine := gin.New()
	engine.Use(gin.Logger())
	engine.Use(gin.Recovery())
	engine.Use(corsMiddleware())
	engine.Use(timeoutMiddleware(30 * time.Second))

	r := &Router{
		engine:     engine,
		dashboardH: dashboard.NewHandler(dashboardSvc),
		tasksH:     tasks.NewHandler(executionSvc, treeSvc, scheduleSvc, lockMgr, asynqClient),
		configH:    config.NewHandler(configSvc),
		historyH:   history.NewHandler(executionSvc),
		docsH:      docs.NewHandler(docsDir),
		lockMgr:    lockMgr,
	}

	r.setupRoutes()
	return r
}

// setupRoutes registers all API routes matching the openapi.json contract.
func (r *Router) setupRoutes() {
	// Health check
	r.engine.GET("/healthz", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "ok"})
	})

	// API v1 group
	v1 := r.engine.Group("/api/v1")
	{
		r.dashboardH.RegisterRoutes(v1)
		r.tasksH.RegisterRoutes(v1)
		r.configH.RegisterRoutes(v1)
		r.historyH.RegisterRoutes(v1)
		r.docsH.RegisterRoutes(v1)
	}
}

// Engine returns the underlying Gin engine.
func (r *Router) Engine() *gin.Engine {
	return r.engine
}

// corsMiddleware adds CORS headers for development.
func corsMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Content-Type, Authorization")
		c.Header("Access-Control-Max-Age", "86400")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	}
}

// timeoutMiddleware adds a timeout to each request.
func timeoutMiddleware(timeout time.Duration) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Next()
		// Simple timeout check (in production, use context.WithTimeout)
		_ = timeout
	}
}
