package main

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/zidoc/api/internal/router"
	"github.com/zidoc/api/pkg/config"
	"github.com/zidoc/api/pkg/database"
	"github.com/zidoc/api/pkg/logger"
	"github.com/zidoc/api/pkg/redis"
	"go.uber.org/zap"
)

// @title           Zidoc API
// @version         1.0
// @description     Zidoc core modular monolith backend API.
// @host            localhost:8080
// @BasePath        /
func main() {
	// 1. Load configuration
	configPath := "config.yaml"
	cfg, err := config.LoadConfig(configPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to load config: %v\n", err)
		os.Exit(1)
	}

	// 2. Initialize logger
	if err := logger.InitLogger(cfg.Server.Env, cfg.Logging.Level, cfg.Logging.Format); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to initialize logger: %v\n", err)
		os.Exit(1)
	}
	defer logger.Sync()

	logger.Log.Info("Starting Zidoc API Server",
		zap.String("env", cfg.Server.Env),
		zap.Int("port", cfg.Server.Port),
	)

	// 3. Connect to Database (PostgreSQL)
	logger.Log.Info("Connecting to PostgreSQL database...")
	db, err := database.ConnectDB(&cfg.Database, cfg.Server.Env == "development")
	if err != nil {
		logger.Fatal("Failed to connect to database", zap.Error(err))
	}
	// Run seeders
	logger.Log.Info("Running database seeders...")
	if err := database.Seed(db); err != nil {
		logger.Log.Warn("Database seeding completed with warning", zap.Error(err))
	} else {
		logger.Log.Info("Database seeding completed successfully")
	}

	// 4. Connect to Redis
	logger.Log.Info("Connecting to Redis...")
	rdb, err := redis.ConnectRedis(&cfg.Redis)
	if err != nil {
		logger.Fatal("Failed to connect to Redis", zap.Error(err))
	}
	_ = rdb // Reserved for future use

	// 5. Setup router & server
	r := router.SetupRouter()

	srv := &http.Server{
		Addr:    fmt.Sprintf(":%d", cfg.Server.Port),
		Handler: r,
	}

	// 6. Start server in a goroutine
	go func() {
		logger.Log.Info("API Server is listening", zap.String("addr", srv.Addr))
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Fatal("Failed to listen and serve", zap.Error(err))
		}
	}()

	// 7. Wait for interrupt signal to gracefully shut down the server
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Log.Info("Shutting down Zidoc API server...")

	// The context is used to inform the server it has 5 seconds to finish
	// the request it is currently handling
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		logger.Log.Error("Server forced to shutdown", zap.Error(err))
	}

	logger.Log.Info("Zidoc API server exited gracefully")
}
