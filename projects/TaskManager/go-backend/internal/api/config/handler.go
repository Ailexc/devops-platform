package config

import (
	"net/http"

	"cmdb-go/internal/service"

	"github.com/gin-gonic/gin"
)

// Handler holds config API handlers.
type Handler struct {
	configSvc *service.ConfigService
}

// NewHandler creates a new config handler.
func NewHandler(configSvc *service.ConfigService) *Handler {
	return &Handler{configSvc: configSvc}
}

// RegisterRoutes registers all config routes.
func (h *Handler) RegisterRoutes(rg *gin.RouterGroup) {
	cfg := rg.Group("/config")
	{
		cfg.GET("/regions/", h.RegionsGET)
		cfg.PUT("/regions/", h.RegionsPUT)
		cfg.GET("/accounts/", h.Accounts)
	}
}

// RegionsGET returns region configurations.
func (h *Handler) RegionsGET(c *gin.Context) {
	ctx := c.Request.Context()
	groups, err := h.configSvc.ListAccountRegions(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	var regions []gin.H
	for _, acct := range groups {
		for _, reg := range acct.Regions {
			regions = append(regions, gin.H{
				"account":     acct.Name,
				"region":      reg.Code,
				"cron":        reg.Cron,
				"concurrency": reg.Concurrency,
				"enabled":     reg.Enabled,
				"source":      reg.Source,
			})
		}
	}
	c.JSON(http.StatusOK, gin.H{"regions": regions})
}

// RegionConfigRequest is the request body for region config update.
type RegionConfigRequest struct {
	Account     string `json:"account" binding:"required"`
	Region      string `json:"region" binding:"required"`
	Cron        string `json:"cron"`
	Concurrency *int   `json:"concurrency"`
}

// RegionsPUT updates a region configuration.
func (h *Handler) RegionsPUT(c *gin.Context) {
	var req RegionConfigRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	ctx := c.Request.Context()
	var cronPtr *string
	if req.Cron != "" {
		cronPtr = &req.Cron
	}

	if err := h.configSvc.UpdateRegionConfig(ctx, req.Account, req.Region, cronPtr, req.Concurrency); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status":  "updated",
		"account": req.Account,
		"region":  req.Region,
	})
}

// Accounts returns the account list.
func (h *Handler) Accounts(c *gin.Context) {
	ctx := c.Request.Context()
	accounts, err := h.configSvc.ListAccounts(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"accounts": accounts})
}
