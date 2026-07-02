package database_test

import (
	"testing"
	"time"

	"github.com/zidoc/api/pkg/config"
	"github.com/zidoc/api/pkg/database"
)

func TestConnectDB_Failure(t *testing.T) {
	// Provide invalid configuration to verify connection failure behavior
	cfg := &config.DatabaseConfig{
		Host:            "invalid_host",
		Port:            9999,
		User:            "postgres",
		Password:        "wrong_password",
		DBName:          "invalid_db",
		SSLMode:         "disable",
		MaxOpenConns:    2,
		MaxIdleConns:    2,
		ConnMaxLifetime: 1 * time.Second,
	}

	_, err := database.ConnectDB(cfg, false)
	if err == nil {
		t.Error("expected database connection to fail, but it succeeded")
	}
}

func TestPingDB_Nil(t *testing.T) {
	// Set DB reference to nil to verify PingDB handles nil connections
	database.DB = nil
	err := database.PingDB()
	if err == nil {
		t.Error("expected PingDB to fail when connection is nil, but it succeeded")
	}
}
