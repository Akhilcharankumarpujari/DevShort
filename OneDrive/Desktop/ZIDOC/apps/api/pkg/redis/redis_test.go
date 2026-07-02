package redis_test

import (
	"testing"

	"github.com/zidoc/api/pkg/config"
	"github.com/zidoc/api/pkg/redis"
)

func TestConnectRedis_Failure(t *testing.T) {
	// Provide invalid configuration to verify connection failure behavior
	cfg := &config.RedisConfig{
		Host:     "invalid_host",
		Port:     9999,
		Password: "",
		DB:       0,
		PoolSize: 2,
	}

	_, err := redis.ConnectRedis(cfg)
	if err == nil {
		t.Error("expected Redis connection to fail, but it succeeded")
	}
}

func TestPingRedis_Nil(t *testing.T) {
	// Set RedisClient reference to nil to verify PingRedis handles nil clients
	redis.RedisClient = nil
	err := redis.PingRedis()
	if err == nil {
		t.Error("expected PingRedis to fail when connection is nil, but it succeeded")
	}
}
