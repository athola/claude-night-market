---
name: deployment-procedures
description: detailed deployment workflow including CI/CD pipelines, environment setup, monitoring, and production release management
version: 1.0.0
created_by: abstract-examples
tags: [deployment, ci-cd, production, monitoring, devops]
category: development
type: module
estimated_tokens: 120
dependencies: []
companion_skills: []
modules: []
tools:
  - deployment-validator
  - environment-checker
  - rollback-manager
---

# Deployment Procedures

detailed deployment framework that validates reliable, automated, and monitored releases with proper rollback procedures and environment management.

## Overview

Master deployment practices with this detailed framework:

** Quick Start**: Get your deployments working reliably in 20 minutes
- Set up basic CI/CD pipeline with automated testing
- Configure staging and production environments
- Implement deployment monitoring and alerting

**Progressive Learning**: Build deployment expertise gradually
1. **Foundation** → Basic deployment + environment setup + monitoring
2. **CI/CD Pipeline** → Automated testing + release management + rollback
3. **Production Ready** → Performance monitoring + scaling + disaster recovery

** Use Case-Based**: Jump directly to what you need right now
- First deployment? → Focus on environment setup + basic pipeline + monitoring
- Production issues? → Apply rollback procedures + health checks + debugging
- Scaling challenges? → Implement auto-scaling + load balancing + performance optimization
- Compliance needs? → Add audit trails + access controls + security scans

## Environment Management

### Environment Types
```yaml
# Development Environment
development:
  database: local_postgres
  cache: redis_local
  logging: debug_level
  monitoring: basic_metrics

# Staging Environment
staging:
  database: postgres_staging
  cache: redis_staging
  logging: info_level
  monitoring: production_like
  data: test_dataset

# Production Environment
production:
  database: postgres_cluster
  cache: redis_cluster
  logging: warn_level
  monitoring: full_observability
  data: production_data
```

### Environment Configuration
- Separate configurations for each environment
- Environment-specific secrets management
- Consistent infrastructure across environments
- Automated environment provisioning

## CI/CD Pipeline

### Pipeline Stages
```yaml
# .github/workflows/deploy.yml
name: Deploy Application

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm test
      - name: Run integration tests
        run: npm run test:integration

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build application
        run: npm run build
      - name: Build Docker image
        run: docker build -t app:${{ github.sha }} .
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push app:${{ github.sha }}

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    steps:
      - name: Deploy to staging
        run: |
          kubectl set image deployment/app app=app:${{ github.sha }}
          kubectl rollout status deployment/app

  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          kubectl set image deployment/app app=app:${{ github.sha }}
          kubectl rollout status deployment/app
```

### Pipeline Best Practices
- Automated testing at each stage
- Parallel execution where possible
- Fast feedback on failures
- Manual approval for production deployments
- Rollback automation for failed deployments

## Deployment Strategies

### Blue-Green Deployment
```bash
# Blue-Green Deployment Script
#!/bin/bash

CURRENT_ENV=$(kubectl get service app -o jsonpath='{.spec.selector.env}')
NEW_ENV="green"

if [ "$CURRENT_ENV" = "green" ]; then
    NEW_ENV="blue"
fi

echo "Deploying to $NEW_ENV environment"

# Deploy new version
kubectl apply -f deployment-${NEW_ENV}.yaml
kubectl rollout status deployment/app-${NEW_ENV}

# Health check
kubectl exec -it deployment/app-${NEW_ENV} -- curl -f http://localhost:3000/health
if [ $? -ne 0 ]; then
    echo "Health check failed, rolling back"
    kubectl delete deployment app-${NEW_ENV}
    exit 1
fi

# Switch traffic
kubectl patch service app -p '{"spec":{"selector":{"env":"'$NEW_ENV'"}}}'

echo "Deployment completed successfully"
```

### Rolling Deployment
```yaml
# Rolling Deployment Configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: app:latest
        ports:
        - containerPort: 3000
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### Canary Deployment
```bash
# Canary Deployment Script
#!/bin/bash

VERSION=$1
CANARY_PERCENTAGE=10

echo "Starting canary deployment of version $VERSION"

# Deploy canary version with 10% traffic
kubectl apply -f deployment-canary.yaml
kubectl patch service app -p '{"spec":{"selector":{"version":"canary"}}}'

# Monitor metrics for 10 minutes
for i in {1..60}; do
    ERROR_RATE=$(curl -s "http://monitoring/api/error-rate")
    RESPONSE_TIME=$(curl -s "http://monitoring/api/response-time")

    echo "Error rate: $ERROR_RATE%, Response time: ${RESPONSE_TIME}ms"

    if (( $(echo "$ERROR_RATE > 5" | bc -l) )); then
        echo "Error rate too high, rolling back"
        kubectl patch service app -p '{"spec":{"selector":{"version":"stable"}}}'
        kubectl delete deployment app-canary
        exit 1
    fi

    sleep 10
done

# Full deployment if canary is successful
echo "Canary deployment successful, proceeding with full deployment"
kubectl apply -f deployment-stable.yaml
kubectl delete deployment app-canary
```

## Monitoring and Health Checks

### Health Endpoints
```javascript
// Health check implementation
app.get('/health', async (req, res) => {
  try {
    // Check database connection
    await db.query('SELECT 1');

    // Check cache connection
    await cache.ping();

    // Check external services
    await externalService.healthCheck();

    res.status(200).json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        database: 'healthy',
        cache: 'healthy',
        external_service: 'healthy'
      }
    });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

// Readiness endpoint
app.get('/ready', (req, res) => {
  const isReady = app.locals.isReady &&
                  !app.locals.isShuttingDown;

  res.status(isReady ? 200 : 503).json({
    ready: isReady,
    timestamp: new Date().toISOString()
  });
});
```

### Monitoring Metrics
```yaml
# Prometheus configuration
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'application'
    static_configs:
      - targets: ['app:3000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'database'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'cache'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Alerting Rules
```yaml
# Alertmanager rules
groups:
  - name: application.rules
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds"
```

## Rollback Procedures

### Automated Rollback
```bash
# Rollback script
#!/bin/bash

DEPLOYMENT_NAME=$1
TARGET_REVISION=$2

echo "Rolling back $DEPLOYMENT_NAME to revision $TARGET_REVISION"

# Check current deployment status
kubectl rollout status deployment/$DEPLOYMENT_NAME --timeout=30s
if [ $? -ne 0 ]; then
    echo "Current deployment is not healthy, proceeding with rollback"
fi

# Rollback to target revision
kubectl rollout undo deployment/$DEPLOYMENT_NAME --to-revision=$TARGET_REVISION

# Wait for rollback to complete
kubectl rollout status deployment/$DEPLOYMENT_NAME --timeout=120s

if [ $? -eq 0 ]; then
    echo "Rollback completed successfully"
else
    echo "Rollback failed, manual intervention required"
    exit 1
fi
```

### Rollback Triggers
- Health check failures
- High error rates
- Performance degradation
- User feedback about issues
- Manual rollback request

## Security and Compliance

### Security Scans
```yaml
# Security scan in pipeline
- name: Security Scan
  run: |
    # Container security scan
    trivy image app:${{ github.sha }}

    # Dependency vulnerability scan
    npm audit --audit-level high

    # Infrastructure as code security scan
    checkov -d k8s/
```

### Access Controls
- Role-based access control (RBAC) for deployments
- Separate credentials for each environment
- Audit logs for all deployment activities
- Multi-factor authentication for production deployments

## Troubleshooting

### Common Issues
1. **Deployment Timeouts**
   - Check resource limits and quotas
   - Verify image size and pull times
   - Review health check configuration

2. **Health Check Failures**
   - Verify application startup time
   - Check database and service connections
   - Review health check endpoint implementation

3. **Performance Issues**
   - Monitor resource usage during deployment
   - Check database migration performance
   - Analyze response time trends

### Debugging Tools
- `kubectl logs` for application logs
- `kubectl describe` for resource status
- `kubectl exec` for debugging inside containers
- Application performance monitoring (APM) tools

This deployment framework provides detailed guidance for reliable, automated deployments with proper monitoring, rollback procedures, and security controls to validate smooth production releases.
