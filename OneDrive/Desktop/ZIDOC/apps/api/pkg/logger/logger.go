package logger

import (
	"context"
	"fmt"
	"os"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

var Log *zap.Logger

type contextKey string

const LoggerKey contextKey = "logger"

func InitLogger(env string, level string, format string) error {
	var config zap.Config

	// Determine log level
	var zapLevel zapcore.Level
	if err := zapLevel.UnmarshalText([]byte(level)); err != nil {
		zapLevel = zap.InfoLevel
	}

	if env == "production" || format == "json" {
		config = zap.NewProductionConfig()
	} else {
		config = zap.NewDevelopmentConfig()
		config.EncoderConfig.EncodeLevel = zapcore.CapitalColorLevelEncoder
	}

	config.Level = zap.NewAtomicLevelAt(zapLevel)
	config.OutputPaths = []string{"stdout"}
	config.ErrorOutputPaths = []string{"stderr"}

	// Build the logger
	builtLogger, err := config.Build()
	if err != nil {
		return fmt.Errorf("failed to build zap logger: %w", err)
	}

	Log = builtLogger
	zap.ReplaceGlobals(Log)

	return nil
}

// GetLogger returns the global logger or the request-scoped logger if present in context
func GetLogger(ctx context.Context) *zap.Logger {
	if ctx != nil {
		if loggerVal, ok := ctx.Value(LoggerKey).(*zap.Logger); ok {
			return loggerVal
		}
	}
	if Log == nil {
		// Fallback logger if not initialized
		fallback, _ := zap.NewDevelopment()
		return fallback
	}
	return Log
}

// WithContext returns a new context with the provided logger injected
func WithContext(ctx context.Context, logger *zap.Logger) context.Context {
	return context.WithValue(ctx, LoggerKey, logger)
}

// Sync flushes any buffered log entries
func Sync() {
	if Log != nil {
		_ = Log.Sync()
	}
}

// Fatal logs a fatal message and exits
func Fatal(msg string, fields ...zap.Field) {
	if Log != nil {
		Log.Fatal(msg, fields...)
	} else {
		fmt.Fprintf(os.Stderr, "FATAL: %s\n", msg)
		os.Exit(1)
	}
}
