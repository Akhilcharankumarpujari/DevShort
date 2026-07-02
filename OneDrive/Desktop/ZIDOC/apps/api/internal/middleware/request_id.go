package middleware

import (
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/zidoc/api/pkg/logger"
	"go.uber.org/zap"
)

const RequestIDHeader = "X-Request-ID"
const RequestIDKey = "requestID"

func RequestID() gin.HandlerFunc {
	return func(c *gin.Context) {
		requestID := c.GetHeader(RequestIDHeader)
		if requestID == "" {
			requestID = uuid.New().String()
		}

		c.Header(RequestIDHeader, requestID)
		c.Set(RequestIDKey, requestID)

		// Create a request-specific logger pre-populated with requestID
		reqLogger := logger.Log.With(zap.String("requestId", requestID))
		c.Request = c.Request.WithContext(logger.WithContext(c.Request.Context(), reqLogger))

		c.Next()
	}
}
