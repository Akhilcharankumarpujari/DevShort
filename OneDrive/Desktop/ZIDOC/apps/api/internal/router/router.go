package router

import (
	"github.com/gin-gonic/gin"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
	_ "github.com/zidoc/api/docs" // Swagger generated docs
	"github.com/zidoc/api/internal/handlers"
	"github.com/zidoc/api/internal/middleware"
)

func SetupRouter() *gin.Engine {
	r := gin.New()

	// Apply global middlewares
	r.Use(middleware.RequestID())
	r.Use(middleware.CORS())
	r.Use(middleware.Logger())
	r.Use(middleware.Recovery())

	// Health handlers
	healthHandler := handlers.NewHealthHandler()
	r.GET("/health", healthHandler.HealthCheck)
	r.GET("/ready", healthHandler.ReadyCheck)
	r.GET("/live", healthHandler.LiveCheck)

	// API versioning group
	v1 := r.Group("/api/v1")
	{
		// Placeholder for future endpoints
		v1.GET("/ping", func(c *gin.Context) {
			c.JSON(200, gin.H{"message": "pong"})
		})
	}

	// Swagger documentation route
	r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

	return r
}
