package middleware

import (
	"log/slog"
	"net/http"
	"runtime/debug"

	"github.com/gin-gonic/gin"
)

func Recovery() gin.HandlerFunc {
	return func(c *gin.Context) {
		defer func() {
			if err := recover(); err != nil {
				// Log the stack trace
				slog.Error("panic recovered",
					"error", err,
					"stack", string(debug.Stack()),
				)

				// Return JSON error response
				c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{
					"error":  "Internal Server Error",
					"detail": "An unexpected error occurred",
				})
			}
		}()
		c.Next()
	}
}
