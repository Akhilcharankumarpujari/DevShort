module.exports = {
  services: {
    web: {
      port: 5173,
      name: "web"
    },
    api: {
      port: 8080,
      name: "api"
    },
    aiService: {
      port: 8000,
      name: "ai-service"
    }
  },
  database: {
    postgres: {
      port: 5432
    },
    redis: {
      port: 6379
    }
  }
};
