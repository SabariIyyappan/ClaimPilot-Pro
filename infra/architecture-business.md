# ClaimPilot Pro AWS Architecture (Business View)

```mermaid
flowchart LR
    U[Patients, Staff, Partners] --> DNS[Route 53 + TLS]
    DNS --> EDGE[CloudFront + AWS WAF]
    EDGE --> ALB[Application Load Balancer]
    ALB --> APP[Auto Scaling EC2 API Layer]
    APP --> DB[(Amazon RDS PostgreSQL Multi-AZ)]
    APP --> CACHE[(ElastiCache Redis)]
    APP --> S3[(Amazon S3 - Private Documents)]
    APP --> Q[SQS Async Processing Queue]
    Q --> WORKERS[Background Workers]
    WORKERS --> OCR[OCR/Claim Processing Services]
    OCR --> S3
    APP --> OBS[CloudWatch Logs + Metrics]
    OBS --> ALERTS[SNS Alerts]
```

## Value Story

- Scalable under peak claim volume via Auto Scaling.
- Secure document handling with private encrypted S3.
- Highly available app and database across Availability Zones.
- Fast user experience with edge caching and low-latency app tier.
- Operable at enterprise level using centralized monitoring and alerts.
