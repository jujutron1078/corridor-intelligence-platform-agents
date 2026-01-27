@Library('shared-jenkins-library') _

dockerPipeline(
    // Required Configuration
    dockerImage: ' ms-grant-writer-agent',
    appPort: '8000',
    
    // Project & Technology
    project: 'bayes',
    technology: 'python',  // FastAPI / Python backend
    
    // Kubernetes Deployment
    deployTo: 'kubernetes',
    
    // Infisical Secrets
    infisicalPath: '/ms-grant-writer-agent/',
    
    // Override health check timeout (default is 5 minutes, reduce to 1 for faster feedback)
    healthCheckTimeout: 1
)


