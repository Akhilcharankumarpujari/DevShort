package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/zidoc/api/pkg/database"
	"github.com/zidoc/api/pkg/redis"
)

type HealthHandler struct{}

func NewHealthHandler() *HealthHandler {
	return &HealthHandler{}
}

// HealthCheck godoc
// @Summary      Liveness/General Health check
// @Description  Get general status of the API service
// @Tags         health
// @Produce      json
// @Success      200  {object}  map[string]string
// @Router       /health [get]
func (h *HealthHandler) HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "healthy",
	})
}

// LiveCheck godoc
// @Summary      Liveness check
// @Description  Check if the application is running
// @Tags         health
// @Produce      json
// @Success      200  {object}  map[string]string
// @Router       /live [get]
func (h *HealthHandler) LiveCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "alive",
	})
}

// ReadyCheck godoc
// @Summary      Readiness check
// @Description  Check if database and redis connections are healthy
// @Tags         health
// @Produce      json
// @Success      200  {object}  map[string]interface{}
// @Failure      503  {object}  map[string]interface{}
// @Router       /ready [get]
func (h *HealthHandler) ReadyCheck(c *gin.Context) {
	var dbStatus = "up"
	var redisStatus = "up"
	var hasError bool

	if err := database.PingDB(); err != nil {
		dbStatus = "down: " + err.Error()
		hasError = true
	}

	if err := redis.PingRedis(); err != nil {
		redisStatus = "down: " + err.Error()
		hasError = true
	}

	response := gin.H{
		"status": "ready",
		"checks": gin.H{
			"database": dbStatus,
			"redis":    redisStatus,
		},
	}

	if hasError {
		response["status"] = "unready"
		c.JSON(http.StatusServiceUnavailable, response)
		return
	}

	c.JSON(http.StatusOK, response)
}
