package middleware

import (
	"time"

	"github.com/gin-gonic/gin"
	"github.com/zidoc/api/pkg/logger"
	"go.uber.org/zap"
)

func Logger() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		query := c.Request.URL.RawQuery

		// Process request
		c.Next()

		// Get request-scoped logger
		reqLogger := logger.GetLogger(c.Request.Context())

		latency := time.Since(start)
		status := c.Writer.Status()
		method := c.Request.Method
		clientIP := c.ClientIP()
		userAgent := c.Request.UserAgent()

		fields := []zap.Field{
			zap.Int("status", status),
			zap.String("method", method),
			zap.String("path", path),
			zap.String("query", query),
			zap.String("ip", clientIP),
			zap.String("userAgent", userAgent),
			zap.Duration("latency", latency),
		}

		if len(c.Errors) > 0 {
			for _, err := range c.Errors {
				reqLogger.Error("Request error", zap.Error(err.Err))
			}
		} else {
			if status >= 500 {
				reqLogger.Error("Server error response", fields...)
			} else if status >= 400 {
				reqLogger.Warn("Client error response", fields...)
			} else {
				reqLogger.Info("Request completed successfully", fields...)
			}
		}
	}
}
