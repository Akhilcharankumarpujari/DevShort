"use client";

import React, { useState, useEffect } from "react";

interface ServiceNode {
  id: string;
  name: string;
  url: string;
  localUrl: string;
  dbUrl?: string;
  desc: string;
  port: number;
  endpoints: string[];
}

export default function Home() {
  const [selectedService, setSelectedService] = useState<string>("api-gateway");
  const [healthStatus, setHealthStatus] = useState<Record<string, "checking" | "online" | "offline">>({
    "api-gateway": "checking",
    "user-service": "checking",
    "product-service": "checking",
    "order-service": "checking",
    "inventory-service": "checking",
    "payment-service": "checking",
  });

  const services: Record<string, ServiceNode> = {
    "api-gateway": {
      id: "api-gateway",
      name: "API Gateway",
      url: "http://api-gateway:8000",
      localUrl: "http://localhost:8000",
      desc: "Single entry point for client requests. Dynamically proxies traffic to down-stream microservices, handles routing, and aggregates documentation.",
      port: 8000,
      endpoints: ["/api/v1/health", "/api/v1/openapi.json", "/api/v1/users/*", "/api/v1/products/*", "/api/v1/orders/*", "/api/v1/inventory/*", "/api/v1/payments/*"],
    },
    "user-service": {
      id: "user-service",
      name: "User Service",
      url: "http://user-service:8000",
      localUrl: "http://localhost:8001",
      dbUrl: "postgresql://postgres:postgres@db:5432/techhub_users",
      desc: "Manages customer accounts, user profiles, credentials, permissions, and addresses.",
      port: 8001,
      endpoints: ["/api/v1/health", "/api/v1/users/", "/api/v1/users/{user_id}"],
    },
    "product-service": {
      id: "product-service",
      name: "Product Service",
      url: "http://product-service:8000",
      localUrl: "http://localhost:8002",
      dbUrl: "postgresql://postgres:postgres@db:5432/techhub_products",
      desc: "Catalogs items, details, computer and electronics specifications, brands, filters, and prices.",
      port: 8002,
      endpoints: ["/api/v1/health", "/api/v1/products/", "/api/v1/products/{product_id}"],
    },
    "order-service": {
      id: "order-service",
      name: "Order Service",
      url: "http://order-service:8000",
      localUrl: "http://localhost:8003",
      dbUrl: "postgresql://postgres:postgres@db:5432/techhub_orders",
      desc: "Handles transaction workflows, cart items, checkout flows, orders creation, and status tracking.",
      port: 8003,
      endpoints: ["/api/v1/health", "/api/v1/orders/", "/api/v1/orders/{order_id}"],
    },
    "inventory-service": {
      id: "inventory-service",
      name: "Inventory Service",
      url: "http://inventory-service:8000",
      localUrl: "http://localhost:8004",
      dbUrl: "postgresql://postgres:postgres@db:5432/techhub_inventory",
      desc: "Tracks product stock quantities, warehouse locations, reorder notifications, and stock allocation.",
      port: 8004,
      endpoints: ["/api/v1/health", "/api/v1/inventory/", "/api/v1/inventory/{product_id}"],
    },
    "payment-service": {
      id: "payment-service",
      name: "Payment Service",
      url: "http://payment-service:8000",
      localUrl: "http://localhost:8005",
      dbUrl: "postgresql://postgres:postgres@db:5432/techhub_payments",
      desc: "Integrates with stripe/dummy payment providers, records transactions, tracks authorization/captured statuses.",
      port: 8005,
      endpoints: ["/api/v1/health", "/api/v1/payments/", "/api/v1/payments/{transaction_id}"],
    },
  };

  // Simulate health checking for architectural demo purposes
  useEffect(() => {
    const timer = setTimeout(() => {
      setHealthStatus({
        "api-gateway": "online",
        "user-service": "online",
        "product-service": "online",
        "order-service": "online",
        "inventory-service": "online",
        "payment-service": "online",
      });
    }, 1200);
    return () => clearTimeout(timer);
  }, []);

  const activeService = services[selectedService];

  return (
    <div style={styles.container}>
      {/* Background Gradients */}
      <div style={styles.glowBgLeft}></div>
      <div style={styles.glowBgRight}></div>

      {/* Header */}
      <header style={styles.header} className="glass-panel">
        <div style={styles.headerLogo}>
          <span style={styles.logoIcon}>⚡</span>
          <h1 style={styles.logoText}>TechHub</h1>
          <span style={styles.logoBadge}>Phase 1 - Infra</span>
        </div>
        <nav style={styles.nav}>
          <a href="#architecture" style={styles.navLink}>Architecture</a>
          <a href="#services" style={styles.navLink}>Services</a>
          <a href="#docs" style={styles.navLink}>Docs</a>
        </nav>
      </header>

      {/* Main Content */}
      <main style={styles.mainContent}>
        {/* Hero Section */}
        <section style={styles.heroSection}>
          <h2 style={styles.heroTitle}>
            Cloud-Native <span style={styles.gradientText}>Electronics Store</span>
          </h2>
          <p style={styles.heroSubtitle}>
            A production-ready monorepo microservice architecture built with Next.js 15, FastAPI, Docker, and Kubernetes.
          </p>
          <div style={styles.heroActions}>
            <a href="#architecture" style={styles.btnPrimary}>Explore Architecture</a>
            <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" style={styles.btnSecondary}>
              Interactive OpenAPI Docs ↗
            </a>
          </div>
        </section>

        {/* Live Grid & Explorer */}
        <section id="architecture" style={styles.archExplorerSection} className="animate-fade-in">
          <div style={styles.sectionHeader}>
            <h3 style={styles.sectionTitle}>Interactive Architecture Map</h3>
            <p style={styles.sectionSubtitle}>Click components below to inspect their environment configuration, endpoints, and OpenAPI endpoints.</p>
          </div>

          <div style={styles.archGrid}>
            {/* Visual Architecture Map */}
            <div style={styles.archCanvas} className="glass-panel">
              {/* Client tier */}
              <div style={styles.tierRow}>
                <div style={styles.clientNode}>
                  <div style={styles.nodeHeader}>
                    <span style={{ fontSize: "1.2rem" }}>🌐</span>
                    <span style={styles.nodeLabel}>User Browser</span>
                  </div>
                </div>
              </div>

              {/* Connector line */}
              <div style={styles.lineDown}></div>

              {/* Frontend tier */}
              <div style={styles.tierRow}>
                <div style={styles.frontendNode}>
                  <div style={styles.nodeHeader}>
                    <span style={{ fontSize: "1.2rem" }}>⚛️</span>
                    <span style={styles.nodeLabel}>Next.js 15 App</span>
                  </div>
                  <span style={styles.nodePort}>Port 3000</span>
                </div>
              </div>

              {/* Connector line */}
              <div style={styles.lineDown}></div>

              {/* API Gateway */}
              <div style={styles.tierRow}>
                <div 
                  onClick={() => setSelectedService("api-gateway")}
                  style={{
                    ...styles.serviceNode,
                    borderColor: selectedService === "api-gateway" ? "var(--primary)" : "var(--border-color)",
                    boxShadow: selectedService === "api-gateway" ? "var(--shadow-glow)" : "none",
                  }}
                >
                  <div style={styles.nodeHeader}>
                    <span style={{ color: "var(--accent)", fontSize: "1.2rem" }}>🛡️</span>
                    <span style={styles.nodeLabel}>API Gateway</span>
                    <span style={{
                      ...styles.statusDot,
                      backgroundColor: healthStatus["api-gateway"] === "online" ? "var(--success)" : "var(--warning)"
                    }}></span>
                  </div>
                  <span style={styles.nodePort}>Port 8000</span>
                </div>
              </div>

              {/* Connector split lines */}
              <div style={styles.connectorContainer}>
                <div style={styles.horizontalLine}></div>
                <div style={styles.verticalSplitLines}>
                  <div style={styles.verticalLine}></div>
                  <div style={styles.verticalLine}></div>
                  <div style={styles.verticalLine}></div>
                  <div style={styles.verticalLine}></div>
                  <div style={styles.verticalLine}></div>
                </div>
              </div>

              {/* Microservices tier */}
              <div style={styles.microservicesRow}>
                {Object.values(services).filter(s => s.id !== "api-gateway").map((svc) => (
                  <div 
                    key={svc.id}
                    onClick={() => setSelectedService(svc.id)}
                    style={{
                      ...styles.miniNode,
                      borderColor: selectedService === svc.id ? "var(--primary)" : "var(--border-color)",
                      boxShadow: selectedService === svc.id ? "var(--shadow-glow)" : "none",
                    }}
                  >
                    <div style={{ ...styles.statusDot, ...styles.miniDot, backgroundColor: healthStatus[svc.id] === "online" ? "var(--success)" : "var(--warning)" }}></div>
                    <span style={styles.miniNodeIcon}>⚙️</span>
                    <span style={styles.miniNodeLabel}>{svc.name.replace(" Service", "")}</span>
                    <span style={styles.miniNodePort}>:{svc.port}</span>
                  </div>
                ))}
              </div>

              {/* Database Layer connector */}
              <div style={styles.dbConnectorContainer}>
                <div style={styles.verticalSplitLines}>
                  <div style={styles.verticalLine}></div>
                  <div style={styles.verticalLine}></div>
                  <div style={styles.verticalLine}></div>
                  <div style={styles.verticalLine}></div>
                  <div style={styles.verticalLine}></div>
                </div>
                <div style={styles.horizontalLine}></div>
                <div style={styles.lineDown}></div>
              </div>

              {/* Shared Database */}
              <div style={styles.tierRow}>
                <div style={styles.dbNode}>
                  <div style={styles.nodeHeader}>
                    <span style={{ fontSize: "1.2rem" }}>🗄️</span>
                    <span style={styles.nodeLabel}>PostgreSQL</span>
                  </div>
                  <span style={styles.nodePort}>Port 5432 (5 Service DBs)</span>
                </div>
              </div>

            </div>

            {/* Sidebar Details Panel */}
            <div style={styles.detailsPanel} className="glass-panel">
              <div style={styles.panelTitleRow}>
                <h4 style={styles.panelTitle}>{activeService.name}</h4>
                <span style={{
                  ...styles.statusBadge,
                  backgroundColor: healthStatus[activeService.id] === "online" ? "var(--success-glow)" : "rgba(255, 165, 0, 0.1)",
                  color: healthStatus[activeService.id] === "online" ? "var(--success)" : "var(--warning)",
                }}>
                  {healthStatus[activeService.id].toUpperCase()}
                </span>
              </div>
              <p style={styles.panelDesc}>{activeService.desc}</p>
              
              <div style={styles.metaDivider}></div>

              <div style={styles.metaRow}>
                <span style={styles.metaLabel}>Internal Cluster URL:</span>
                <code style={styles.metaValue}>{activeService.url}</code>
              </div>

              <div style={styles.metaRow}>
                <span style={styles.metaLabel}>Local Developer URL:</span>
                <code style={styles.metaValue}>{activeService.localUrl}</code>
              </div>

              {activeService.dbUrl && (
                <div style={styles.metaRow}>
                  <span style={styles.metaLabel}>Database Source URL:</span>
                  <code style={styles.metaValue}>{activeService.dbUrl}</code>
                </div>
              )}

              <div style={styles.metaDivider}></div>

              <h5 style={styles.endpointsTitle}>Registered API Endpoints:</h5>
              <div style={styles.endpointList}>
                {activeService.endpoints.map((ep, idx) => (
                  <div key={idx} style={styles.endpointItem}>
                    <span style={styles.getBadge}>GET</span>
                    <code style={styles.endpointCode}>{ep}</code>
                  </div>
                ))}
              </div>

              <div style={styles.panelActions}>
                <a 
                  href={`${activeService.localUrl}/api/v1/docs`} 
                  target="_blank" 
                  rel="noreferrer" 
                  style={styles.panelBtnPrimary}
                >
                  Open Swagger Docs ↗
                </a>
                <a 
                  href={`${activeService.localUrl}/api/v1/health`} 
                  target="_blank" 
                  rel="noreferrer" 
                  style={styles.panelBtnSecondary}
                >
                  Verify Health Check Endpoint
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* Infrastructure Highlights */}
        <section id="services" style={styles.featuresSection}>
          <div style={styles.sectionHeader}>
            <h3 style={styles.sectionTitle}>Infrastructure Architecture Highlights</h3>
            <p style={styles.sectionSubtitle}>Standard production engineering configurations included in Phase 1.</p>
          </div>

          <div style={styles.featuresGrid}>
            <div style={styles.featureCard} className="glass-panel glass-panel-hover">
              <span style={styles.featureIcon}>🛡️</span>
              <h4 style={styles.featureTitle}>FastAPI Gateway</h4>
              <p style={styles.featureText}>Dynamically routes requests to downstream services via asynchronous `httpx` reverse proxies. Restricts internal cluster visibility.</p>
            </div>

            <div style={styles.featureCard} className="glass-panel glass-panel-hover">
              <span style={styles.featureIcon}>🐳</span>
              <h4 style={styles.featureTitle}>Multi-Stage Docker</h4>
              <p style={styles.featureText}>Lightweight multi-stage `Dockerfile` templates. Reduces final image footprint by removing compilers and source caches.</p>
            </div>

            <div style={styles.featureCard} className="glass-panel glass-panel-hover">
              <span style={styles.featureIcon}>🚀</span>
              <h4 style={styles.featureTitle}>Kubernetes Manifests</h4>
              <p style={styles.featureText}>Configured Deployments, cluster IP services, environment ConfigMaps, Secrets, and Nginx Ingress routes for production rollout.</p>
            </div>

            <div style={styles.featureCard} className="glass-panel glass-panel-hover">
              <span style={styles.featureIcon}>📈</span>
              <h4 style={styles.featureTitle}>Prometheus Monitoring</h4>
              <p style={styles.featureText}>Ready-to-use metrics scraping endpoint definitions and dashboard configs to evaluate system load, health, and latency.</p>
            </div>

            <div style={styles.featureCard} className="glass-panel glass-panel-hover">
              <span style={styles.featureIcon}>⚙️</span>
              <h4 style={styles.featureTitle}>Environment Configs</h4>
              <p style={styles.featureText}>Zero-configuration local runtime environments with isolated `.env` templates managed natively using Python `pydantic-settings`.</p>
            </div>

            <div style={styles.featureCard} className="glass-panel glass-panel-hover">
              <span style={styles.featureIcon}>💾</span>
              <h4 style={styles.featureTitle}>PostgreSQL Schema</h4>
              <p style={styles.featureText}>Pre-configured PostgreSQL container script that initializes isolated databases for all 5 microservices on startup.</p>
            </div>
          </div>
        </section>

        {/* Documentation Quick Links */}
        <section id="docs" style={styles.docsSection}>
          <div style={styles.docsCard} className="glass-panel">
            <h3 style={styles.docsTitle}>Get Started with Local Development</h3>
            <p style={styles.docsSubtitle}>Run the entire cloud-native computer store stack with one terminal command.</p>
            <div style={styles.codeSnippetBox}>
              <code style={styles.codeSnippet}>docker compose up --build</code>
            </div>
            <p style={styles.docsHelpText}>
              This orchestrates Next.js (port 3000), the API Gateway (port 8000), five independent FastAPI servers, and the database automatically with health checks.
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer style={styles.footer}>
        <p>© 2026 TechHub Inc. Cloud-Native Architecture. All Rights Reserved.</p>
        <p style={{ marginTop: "0.25rem", opacity: 0.5, fontSize: "0.85rem" }}>Phase 1 Infrastructure Boilerplate</p>
      </footer>
    </div>
  );
}

// Inline CSS Styles for rich responsive design
const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    minHeight: "100vh",
    width: "100%",
    position: "relative",
    overflowX: "hidden",
  },
  glowBgLeft: {
    position: "absolute",
    width: "600px",
    height: "600px",
    top: "-200px",
    left: "-200px",
    background: "radial-gradient(circle, var(--primary-glow) 0%, transparent 70%)",
    zIndex: -1,
  },
  glowBgRight: {
    position: "absolute",
    width: "800px",
    height: "800px",
    bottom: "10%",
    right: "-300px",
    background: "radial-gradient(circle, var(--secondary-glow) 0%, transparent 70%)",
    zIndex: -1,
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "1rem 2rem",
    position: "sticky",
    top: "1.5rem",
    zIndex: 100,
    margin: "1.5rem 2rem 0 2rem",
    borderRadius: "var(--radius-md)",
  },
  headerLogo: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
  },
  logoIcon: {
    fontSize: "1.5rem",
    lineHeight: 1,
  },
  logoText: {
    fontSize: "1.4rem",
    fontWeight: 800,
    letterSpacing: "-0.03em",
  },
  logoBadge: {
    fontSize: "0.75rem",
    padding: "0.15rem 0.5rem",
    borderRadius: "var(--radius-full)",
    backgroundColor: "var(--border-color)",
    color: "var(--text-secondary)",
    fontWeight: 500,
  },
  nav: {
    display: "flex",
    gap: "1.5rem",
  },
  navLink: {
    color: "var(--text-secondary)",
    fontWeight: 500,
    fontSize: "0.95rem",
  },
  mainContent: {
    flex: 1,
    padding: "0 2rem",
    maxWidth: "1280px",
    margin: "0 auto",
    width: "100%",
  },
  heroSection: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    textAlign: "center",
    padding: "6rem 1rem 4rem 1rem",
    maxWidth: "800px",
    margin: "0 auto",
  },
  heroTitle: {
    fontSize: "3.5rem",
    fontWeight: 800,
    lineHeight: 1.15,
    marginBottom: "1.5rem",
  },
  gradientText: {
    background: "linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
  },
  heroSubtitle: {
    fontSize: "1.2rem",
    color: "var(--text-secondary)",
    marginBottom: "2.5rem",
    lineHeight: 1.6,
  },
  heroActions: {
    display: "flex",
    gap: "1rem",
    flexWrap: "wrap",
    justifyContent: "center",
  },
  btnPrimary: {
    display: "inline-block",
    padding: "0.8rem 1.6rem",
    backgroundColor: "var(--primary)",
    color: "var(--text-on-primary)",
    borderRadius: "var(--radius-md)",
    fontWeight: 600,
    boxShadow: "var(--shadow-glow)",
    transition: "background-color 0.2s, transform 0.2s",
  },
  btnSecondary: {
    display: "inline-block",
    padding: "0.8rem 1.6rem",
    backgroundColor: "var(--bg-surface)",
    border: "1px solid var(--border-color)",
    color: "var(--text-primary)",
    borderRadius: "var(--radius-md)",
    fontWeight: 600,
    transition: "border-color 0.2s, background-color 0.2s",
  },
  archExplorerSection: {
    padding: "4rem 0",
  },
  sectionHeader: {
    textAlign: "center",
    marginBottom: "3rem",
  },
  sectionTitle: {
    fontSize: "2rem",
    fontWeight: 800,
    marginBottom: "0.5rem",
  },
  sectionSubtitle: {
    color: "var(--text-secondary)",
    fontSize: "1rem",
  },
  archGrid: {
    display: "grid",
    gridTemplateColumns: "2fr 1fr",
    gap: "2rem",
    alignItems: "stretch",
  },
  archCanvas: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: "2.5rem",
    borderRadius: "var(--radius-lg)",
    cursor: "default",
  },
  tierRow: {
    width: "100%",
    display: "flex",
    justifyContent: "center",
  },
  clientNode: {
    backgroundColor: "var(--bg-surface)",
    border: "1px solid var(--border-color)",
    padding: "0.75rem 1.5rem",
    borderRadius: "var(--radius-md)",
    boxShadow: "var(--shadow-sm)",
  },
  frontendNode: {
    backgroundColor: "var(--bg-surface)",
    border: "1px solid var(--border-color)",
    padding: "0.75rem 1.5rem",
    borderRadius: "var(--radius-md)",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    boxShadow: "var(--shadow-sm)",
  },
  serviceNode: {
    backgroundColor: "var(--bg-surface)",
    border: "2px solid var(--border-color)",
    padding: "0.85rem 2rem",
    borderRadius: "var(--radius-md)",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    cursor: "pointer",
    position: "relative",
    transition: "border-color 0.2s, box-shadow 0.2s",
  },
  dbNode: {
    backgroundColor: "var(--bg-surface-hover)",
    border: "1px solid var(--border-color)",
    padding: "0.85rem 2rem",
    borderRadius: "var(--radius-md)",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    boxShadow: "var(--shadow-sm)",
  },
  nodeHeader: {
    display: "flex",
    alignItems: "center",
    gap: "0.6rem",
  },
  nodeLabel: {
    fontWeight: 700,
    fontSize: "0.95rem",
  },
  nodePort: {
    fontSize: "0.75rem",
    color: "var(--text-muted)",
    marginTop: "0.15rem",
    fontFamily: "var(--font-mono)",
  },
  statusDot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
  },
  lineDown: {
    width: "2px",
    height: "24px",
    backgroundColor: "var(--border-color)",
  },
  connectorContainer: {
    width: "85%",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
  dbConnectorContainer: {
    width: "85%",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
  horizontalLine: {
    width: "100%",
    height: "2px",
    backgroundColor: "var(--border-color)",
  },
  verticalSplitLines: {
    width: "100%",
    display: "flex",
    justifyContent: "space-between",
  },
  verticalLine: {
    width: "2px",
    height: "20px",
    backgroundColor: "var(--border-color)",
  },
  microservicesRow: {
    width: "100%",
    display: "flex",
    justifyContent: "space-between",
    gap: "0.75rem",
  },
  miniNode: {
    flex: 1,
    backgroundColor: "var(--bg-surface)",
    border: "2px solid var(--border-color)",
    borderRadius: "var(--radius-md)",
    padding: "0.75rem 0.5rem",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    cursor: "pointer",
    position: "relative",
    transition: "border-color 0.2s, box-shadow 0.2s",
  },
  miniDot: {
    position: "absolute",
    top: "8px",
    right: "8px",
  },
  miniNodeIcon: {
    fontSize: "1.2rem",
    marginBottom: "0.25rem",
  },
  miniNodeLabel: {
    fontWeight: 700,
    fontSize: "0.8rem",
    textAlign: "center",
  },
  miniNodePort: {
    fontSize: "0.7rem",
    color: "var(--text-muted)",
    marginTop: "0.15rem",
    fontFamily: "var(--font-mono)",
  },
  detailsPanel: {
    padding: "2rem",
    borderRadius: "var(--radius-lg)",
    display: "flex",
    flexDirection: "column",
  },
  panelTitleRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "0.75rem",
  },
  panelTitle: {
    fontSize: "1.4rem",
    fontWeight: 800,
  },
  statusBadge: {
    fontSize: "0.75rem",
    padding: "0.25rem 0.6rem",
    borderRadius: "var(--radius-full)",
    fontWeight: 700,
    letterSpacing: "0.05em",
  },
  panelDesc: {
    color: "var(--text-secondary)",
    fontSize: "0.95rem",
    marginBottom: "1.5rem",
  },
  metaDivider: {
    height: "1px",
    backgroundColor: "var(--border-color)",
    margin: "1rem 0",
  },
  metaRow: {
    display: "flex",
    flexDirection: "column",
    gap: "0.25rem",
    marginBottom: "0.75rem",
  },
  metaLabel: {
    fontSize: "0.8rem",
    color: "var(--text-muted)",
    fontWeight: 600,
  },
  metaValue: {
    fontFamily: "var(--font-mono)",
    fontSize: "0.8rem",
    backgroundColor: "var(--bg-surface-hover)",
    padding: "0.35rem 0.6rem",
    borderRadius: "var(--radius-sm)",
    color: "var(--primary)",
    wordBreak: "break-all",
  },
  endpointsTitle: {
    fontSize: "0.85rem",
    color: "var(--text-primary)",
    fontWeight: 700,
    marginBottom: "0.5rem",
  },
  endpointList: {
    display: "flex",
    flexDirection: "column",
    gap: "0.5rem",
    marginBottom: "1.5rem",
    maxHeight: "150px",
    overflowY: "auto",
    paddingRight: "0.5rem",
  },
  endpointItem: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
  },
  getBadge: {
    fontSize: "0.65rem",
    padding: "0.15rem 0.35rem",
    backgroundColor: "var(--success-glow)",
    color: "var(--success)",
    fontWeight: 700,
    borderRadius: "3px",
  },
  endpointCode: {
    fontFamily: "var(--font-mono)",
    fontSize: "0.75rem",
    color: "var(--text-secondary)",
  },
  panelActions: {
    display: "flex",
    flexDirection: "column",
    gap: "0.75rem",
    marginTop: "auto",
  },
  panelBtnPrimary: {
    display: "block",
    textAlign: "center" as const,
    padding: "0.75rem 1rem",
    backgroundColor: "var(--primary)",
    color: "var(--text-on-primary)",
    borderRadius: "var(--radius-md)",
    fontWeight: 600,
    boxShadow: "var(--shadow-glow)",
    fontSize: "0.9rem",
  },
  panelBtnSecondary: {
    display: "block",
    textAlign: "center" as const,
    padding: "0.75rem 1rem",
    backgroundColor: "transparent",
    border: "1px solid var(--border-color)",
    color: "var(--text-secondary)",
    borderRadius: "var(--radius-md)",
    fontWeight: 600,
    fontSize: "0.9rem",
  },
  featuresSection: {
    padding: "4rem 0",
  },
  featuresGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
    gap: "1.5rem",
  },
  featureCard: {
    padding: "2rem",
    borderRadius: "var(--radius-md)",
  },
  featureIcon: {
    fontSize: "2rem",
    display: "block",
    marginBottom: "1rem",
  },
  featureTitle: {
    fontSize: "1.2rem",
    fontWeight: 700,
    marginBottom: "0.5rem",
  },
  featureText: {
    color: "var(--text-secondary)",
    fontSize: "0.9rem",
    lineHeight: 1.5,
  },
  docsSection: {
    padding: "4rem 0 6rem 0",
  },
  docsCard: {
    padding: "3rem",
    borderRadius: "var(--radius-lg)",
    textAlign: "center" as const,
    maxWidth: "800px",
    margin: "0 auto",
  },
  docsTitle: {
    fontSize: "1.8rem",
    fontWeight: 800,
    marginBottom: "0.5rem",
  },
  docsSubtitle: {
    color: "var(--text-secondary)",
    marginBottom: "2rem",
  },
  codeSnippetBox: {
    backgroundColor: "var(--bg-base)",
    padding: "1rem 2rem",
    borderRadius: "var(--radius-md)",
    border: "1px solid var(--border-color)",
    display: "inline-block",
    marginBottom: "1.5rem",
  },
  codeSnippet: {
    fontFamily: "var(--font-mono)",
    fontSize: "1.1rem",
    color: "var(--accent)",
    fontWeight: 700,
  },
  docsHelpText: {
    fontSize: "0.9rem",
    color: "var(--text-muted)",
  },
  footer: {
    textAlign: "center" as const,
    padding: "2.5rem 0",
    borderTop: "1px solid var(--border-color)",
    backgroundColor: "var(--bg-surface)",
    color: "var(--text-secondary)",
    fontSize: "0.9rem",
  },
};
