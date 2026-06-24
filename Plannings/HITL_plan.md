# FINNEXUS HUMAN-IN-THE-LOOP (HITL) SYSTEM
## Implementation Plan & Technical Specification

---

## 📋 TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Component Specifications](#component-specifications)
4. [Data Flow & Integration](#data-flow--integration)
5. [Implementation Roadmap](#implementation-roadmap)
6. [Technical Requirements](#technical-requirements)
7. [Success Metrics](#success-metrics)
8. [Risks & Mitigation](#risks--mitigation)
9. [Performance Benchmarks](#performance-benchmarks)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Plan](#deployment-plan)
12. [Maintenance & Evolution](#maintenance--evolution)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Overview
FINNEXUS HITL is an advanced trading intelligence system that combines machine learning predictions with human expertise through structured, adaptive questioning.

### 1.2 Core Objectives
- **Primary:** Improve prediction accuracy from 55-61% to 65-75%
- **Secondary:** Build a community of knowledgeable traders
- **Tertiary:** Create a continuous learning loop between humans and AI

### 1.3 Expected Outcomes
| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Prediction Accuracy | 55-61% | 65-75% | +10-14% |
| Sharpe Ratio | 0.8 | 1.5+ | +87% |
| User Retention | 20% | 60% | +200% |
| Paper Cash Engagement | N/A | ₹10,000+ avg | - |

---

## 2. SYSTEM ARCHITECTURE

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FINNEXUS HITL PLATFORM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   FRONTEND   │    │   BACKEND    │    │   DATABASE   │     │
│  │   (React)    │────│   (FastAPI)  │────│  (PostgreSQL)│     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│         │                    │                    │            │
│         ▼                    ▼                    ▼            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   LLM NODE   │    │   RAG NODE   │    │   ML NODE    │     │
│  │  (Question   │────│  (Context)   │────│  (Prediction)│     │
│  │   Generator) │    │              │    │              │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│         │                    │                    │            │
│         └────────────────────┼────────────────────┘            │
│                              ▼                                 │
│                    ┌──────────────────┐                        │
│                    │   ORCHESTRATOR  │                        │
│                    │   ("The Baby")  │                        │
│                    └──────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Interaction Diagram

```
    USER
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                             │
│                                                             │
│  1. Determine Level                                         │
│  2. Generate Questions (via LLM)                            │
│  3. Display Questions                                       │
│  4. Collect Answers                                         │
│  5. Evaluate (via RAG)                                      │
│  6. Calculate Score & Reward                                │
│  7. Update ML Model                                         │
│  8. Provide Feedback                                        │
└─────────────────────────────────────────────────────────────┘
      │                       │                  │
      ▼                       ▼                  ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  CONTEXT     │    │  RAG MODEL   │    │  ML MODEL    │
│  NODE        │◄───│              │───►│              │
│              │    │  • News      │    │  • Train     │
│  • Books     │    │  • Theory    │    │  • Predict   │
│  • Theory    │    │  • Data      │    │  • Improve   │
│  • History   │    │  • Context   │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 3. COMPONENT SPECIFICATIONS

### 3.1 LLM Question Generator

#### 3.1.1 Purpose
Generate dynamic, context-aware questions tailored to user level

#### 3.1.2 Specifications

| Parameter | Value |
|-----------|-------|
| Model | GPT-4 or Claude 3.5 |
| Input | Level, User Profile, Context |
| Output | 19 Questions (15 MCQ + 4 SAQ) |
| Generation Time | < 30 seconds |
| Cache Time | 24 hours per user level |

#### 3.1.3 Question Structure

```json
{
  "questions": [
    {
      "id": "q1",
      "type": "mcq_single",
      "question": "Based on current market conditions, which technical indicator would you prioritize?",
      "options": ["RSI (14)", "MACD", "Bollinger Bands", "Moving Averages", "Volume Profile"],
      "correct_answer": null,  // Not known initially
      "difficulty": 3,
      "topic": "Technical Analysis",
      "hint": "Consider the current volatility regime"
    },
    {
      "id": "q16",
      "type": "mcq_multiple",
      "question": "Which factors indicate a potential market reversal?",
      "options": ["Divergence", "Extreme sentiment", "Key resistance", "Volume surge", "Hammer pattern", "Overbought RSI"],
      "max_select": 3,
      "difficulty": 4,
      "topic": "Technical Analysis"
    },
    {
      "id": "q20",
      "type": "saq",
      "question": "Identify 5 global events affecting Indian markets and explain their impact.",
      "word_limit": 50,
      "difficulty": 5,
      "topic": "Global Events"
    }
  ]
}
```

#### 3.1.4 System Prompt

```markdown
# SYSTEM PROMPT FOR QUESTION GENERATION

You are an expert financial trading question generator for FINNEXUS HITL.

## MISSION
Create 19 personalized questions that will extract valuable trading insights from users.

## CRITERIA
1. Questions must be context-aware (use current market data)
2. Progressive difficulty (Level 1 → Easy, Level 5 → Expert)
3. 15 MCQ (10 single answer, 5 multiple answer)
4. 4 SAQ requiring analytical thinking
5. Each question should test real-world trading knowledge

## CONTEXT
{context_data}

## USER PROFILE
- Level: {level}
- Strengths: {strengths}
- Weaknesses: {weaknesses}
- Experience: {experience}

## FORMAT
Return JSON with proper structure and validation.
```

---

### 3.2 RAG Model (Context Node)

#### 3.2.1 Purpose
Retrieve and provide relevant context for question generation and answer evaluation

#### 3.2.2 Knowledge Sources

| Source | Type | Update Frequency |
|--------|------|------------------|
| Trading Books | Documents | Manual (Monthly) |
| Market Theories | Documents | Manual (Quarterly) |
| News Articles | API | Real-time |
| Market Data | API | Real-time |
| User History | Database | Real-time |
| Successful Strategies | Database | Weekly |

#### 3.2.3 Vector Database Schema

```python
class Document:
    id: UUID
    content: str
    metadata: {
        'source': str,      # 'book', 'article', 'theory', 'strategy'
        'topic': str,       # 'technical', 'fundamental', 'macro'
        'level': int,       # 1-5 difficulty
        'date': datetime,
        'relevance_score': float
    }
    embedding: List[float]  # 1536-dim for OpenAI
```

#### 3.2.4 Retrieval Pipeline

```python
def retrieve_context(query, top_k=5):
    # 1. Generate query embedding
    query_embedding = embed(query)
    
    # 2. Retrieve from vector DB
    results = vector_db.search(query_embedding, top_k)
    
    # 3. Rank by relevance
    ranked = rank_by_relevance(results, query)
    
    # 4. Add metadata
    enriched = enrich_with_metadata(ranked)
    
    return enriched
```

---

### 3.3 ML Model Node

#### 3.3.1 Purpose
Learn from user insights to improve predictions

#### 3.3.2 Model Architecture

```python
class HITLEnsemble:
    def __init__(self):
        self.models = {
            'xgboost': XGBClassifier(),
            'lightgbm': LGBMClassifier(),
            'randomforest': RandomForestClassifier(),
            'neural_net': NeuralNetwork()  # Added for HITL integration
        }
        self.user_insights = {}
    
    def train_with_hitl(self, user_data, market_data):
        # 1. Extract features from user answers
        user_features = self.extract_user_features(user_data)
        
        # 2. Combine with market features
        combined_features = self.combine_features(
            user_features, market_data
        )
        
        # 3. Train ensemble
        for model in self.models.values():
            model.fit(combined_features, market_outcomes)
        
        # 4. Optimize weights
        self.ensemble_weights = self.optimize_weights()
    
    def extract_user_features(self, user_data):
        """Convert user answers into ML features"""
        features = {}
        
        # Technical analysis understanding
        features['technical_proficiency'] = user_data.get('tech_score', 0)
        
        # Risk assessment ability
        features['risk_awareness'] = user_data.get('risk_score', 0)
        
        # Global awareness
        features['global_context'] = user_data.get('global_score', 0)
        
        # Trading strategy quality
        features['strategy_quality'] = user_data.get('strategy_score', 0)
        
        # Q20 exceptional analysis
        features['exceptional_insight'] = user_data.get('is_exceptional', 0)
        
        return features
```

---

### 3.4 Orchestrator ("The Baby")

#### 3.4.1 Purpose
Coordinate all components and manage user sessions

#### 3.4.2 Session Management

```python
class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.ttl = 3600  # 1 hour
    
    def create_session(self, user_id):
        session_id = f"session_{user_id}_{int(time.time())}"
        self.sessions[user_id] = {
            'session_id': session_id,
            'user_id': user_id,
            'level': None,
            'questions': [],
            'current_index': 0,
            'answers': {},
            'started_at': datetime.now(),
            'last_activity': datetime.now(),
            'status': 'active'
        }
        return self.sessions[user_id]
    
    def get_session(self, user_id):
        if user_id not in self.sessions:
            return None
        if (datetime.now() - self.sessions[user_id]['last_activity']).seconds > self.ttl:
            self.close_session(user_id)
            return None
        return self.sessions[user_id]
```

---

## 4. DATA FLOW & INTEGRATION

### 4.1 Question Generation Flow

```
┌────────────────────────────────────────────────────────────────┐
│                    QUESTION GENERATION FLOW                    │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  1. USER REQUEST                                               │
│     ↓                                                         │
│  2. FETCH USER PROFILE                                         │
│     - History                                                  │
│     - Scores                                                  │
│     - Level                                                   │
│     ↓                                                         │
│  3. CHECK CACHE                                                │
│     - Has user seen this level before?                        │
│     - Generate new if >24 hours old                          │
│     ↓                                                         │
│  4. RETRIEVE CONTEXT                                           │
│     - Level-specific content                                  │
│     - Current market data                                     │
│     - Recent news                                             │
│     ↓                                                         │
│  5. GENERATE QUESTIONS                                         │
│     - LLM system prompt                                       │
│     - 19 questions generated                                  │
│     ↓                                                         │
│  6. VALIDATE & STORE                                           │
│     - Validate JSON format                                    │
│     - Save to database                                        │
│     - Return to user                                          │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Answer Processing Flow

```
┌────────────────────────────────────────────────────────────────┐
│                    ANSWER PROCESSING FLOW                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  1. USER SUBMITS ANSWER                                        │
│     - MCQ: Selected options                                   │
│     - SAQ: Text input                                         │
│     ↓                                                         │
│  2. VALIDATE ANSWER                                            │
│     - Check format                                            │
│     - Word count (SAQ)                                        │
│     ↓                                                         │
│  3. EVALUATE ANSWER                                            │
│     - MCQ: Exact match / Partial match                        │
│     - SAQ: LLM-based scoring (0-1)                            │
│     - Using RAG context                                       │
│     ↓                                                         │
│  4. UPDATE SESSION                                             │
│     - Store answer                                            │
│     - Store score                                             │
│     - Update progress                                         │
│     ↓                                                         │
│  5. CHECK LEVEL COMPLETION                                     │
│     - 19 questions answered?                                  │
│     - Calculate average score                                 │
│     ↓                                                         │
│  6. IF COMPLETED                                               │
│     - Calculate reward                                        │
│     - Update ML model                                         │
│     - Next level unlock                                       │
│     - Generate Level 20 if applicable                         │
└────────────────────────────────────────────────────────────────┘
```

---

## 5. IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Weeks 1-3)

#### Week 1: Core Infrastructure
- [ ] Set up database schema
- [ ] Create API endpoints
- [ ] Implement authentication
- [ ] Basic frontend setup

#### Week 2: LLM Integration
- [ ] Integrate OpenAI/Claude API
- [ ] Implement system prompts
- [ ] Create question generation pipeline
- [ ] Cache mechanism

#### Week 3: RAG Setup
- [ ] Vector database setup (Pinecone/Weaviate)
- [ ] Document embedding pipeline
- [ ] Knowledge base ingestion
- [ ] News API integration

### Phase 2: HITL Core (Weeks 4-6)

#### Week 4: Question System
- [ ] MCQ generation (single & multiple)
- [ ] SAQ generation
- [ ] Answer validation
- [ ] Scoring mechanism

#### Week 5: User Management
- [ ] Level determination logic
- [ ] Progress tracking
- [ ] Reward calculation
- [ ] Level 20 questions

#### Week 6: Frontend Development
- [ ] Question UI components
- [ ] Answer submission forms
- [ ] Progress dashboard
- [ ] Paper cash display

### Phase 3: ML Integration (Weeks 7-9)

#### Week 7: Feature Engineering
- [ ] Extract features from user answers
- [ ] Combine with market data
- [ ] Feature pipeline creation

#### Week 8: Model Training
- [ ] Train ensemble models
- [ ] Optimize weights
- [ ] Cross-validation
- [ ] Performance tracking

#### Week 9: Integration
- [ ] Connect ML predictions to HITL
- [ ] Real-time prediction updates
- [ ] A/B testing framework

### Phase 4: Enhancement (Weeks 10-12)

#### Week 10: Advanced Features
- [ ] Exceptional answer detection
- [ ] Bonus reward system
- [ ] Leaderboard
- [ ] Badges & achievements

#### Week 11: Optimization
- [ ] Performance tuning
- [ ] Cost optimization (LLM tokens)
- [ ] Cache optimization
- [ ] Load testing

#### Week 12: Beta Launch
- [ ] User testing group
- [ ] Bug fixing
- [ ] Documentation
- [ ] Monitoring setup

---

## 6. TECHNICAL REQUIREMENTS

### 6.1 Hardware Requirements

| Component | Specification | Justification |
|-----------|---------------|---------------|
| Database | 8 vCPU, 32GB RAM, 1TB SSD | User data, history, RAG docs |
| API Server | 4 vCPU, 16GB RAM | Handling requests |
| ML Server | GPU (A100/V100), 64GB RAM | Model training & inference |
| Vector DB | 4 vCPU, 16GB RAM | RAG retrieval |
| Redis | 2 vCPU, 8GB RAM | Caching |
| Backup | 4TB HDD | Daily backups |

### 6.2 Software Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Backend | FastAPI | 0.104+ |
| Frontend | React + TypeScript | 18.0+ |
| Database | PostgreSQL | 15+ |
| Vector DB | Pinecone/Weaviate | Latest |
| Cache | Redis | 7.0+ |
| ML | Scikit-learn, XGBoost, PyTorch | Latest |
| LLM | OpenAI GPT-4 / Claude 3.5 | Latest |
| Queue | Celery | 5.0+ |
| Monitoring | Prometheus + Grafana | Latest |
| Logging | ELK Stack | Latest |

### 6.3 API Specifications

#### Question Generation API

```python
POST /api/v1/hitl/generate
Authorization: Bearer <token>
Body: {
    "user_id": 12345,
    "level": 3,
    "force_generate": false
}
Response: {
    "session_id": "session_12345_1700000000",
    "level": 3,
    "questions": [...],
    "total": 19,
    "time_limit": 3600
}
```

#### Answer Submission API

```python
POST /api/v1/hitl/submit
Authorization: Bearer <token>
Body: {
    "session_id": "session_12345_1700000000",
    "question_id": "q5",
    "answer": ["A", "C", "E"]
}
Response: {
    "status": "in_progress",
    "score": 0.85,
    "next_question": {...},
    "progress": "5/19"
}
```

#### Level Completion API

```python
GET /api/v1/hitl/level-complete
Authorization: Bearer <token>
Params: {
    "session_id": "session_12345_1700000000"
}
Response: {
    "status": "level_complete",
    "level": 3,
    "score": 0.82,
    "reward": 25,
    "next_level": 4,
    "total_cash": 185,
    "message": "Great job! You've unlocked Level 4!"
}
```

---

## 7. SUCCESS METRICS

### 7.1 Primary Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Prediction Accuracy | 55-61% | 65-75% | Monthly evaluation |
| Sharpe Ratio | 0.8 | 1.5+ | Monthly |
| User Retention | 20% | 60% | Weekly |
| Level Completion | - | 40% | Daily |
| Q20 Quality | - | 50% exceptional | Weekly |

### 7.2 Secondary Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Questions Generated | 10,000+/month | API usage |
| Average Time per Level | 15-25 minutes | Session tracking |
| ML Improvement Rate | 0.5% per week | Model evaluation |
| Paper Cash Engagement | ₹10,000+ avg | User balance tracking |
| Daily Active Users | 500+ | Daily tracking |
| LLM Cost Efficiency | $0.02 per question | Cost monitoring |

### 7.3 Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Question Diversity Score | >0.8 | Cosine similarity analysis |
| SAQ Word Count Compliance | >90% | Validation |
| MCQ Difficulty Distribution | Normal | Statistical analysis |
| RAG Relevance Score | >0.7 | User feedback |
| User Satisfaction | >4.5/5 | Survey |

---

## 8. RISKS & MITIGATION

### 8.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM Cost Explosion | Medium | High | Caching, cheaper models, request limits |
| RAG Outdated Context | High | Medium | Real-time API integration, update scheduler |
| ML Model Overfitting | Medium | High | Cross-validation, regularization |
| Vector DB Performance | Medium | Medium | Index optimization, sharding |
| API Rate Limiting | Medium | Medium | Distributed architecture, queue system |

### 8.2 User-Related Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| User Fatigue | High | Medium | 19 questions optimal, progress tracking |
| Bad Faith Answers | Medium | Medium | Validation, quality scoring, verification |
| Low Engagement | Medium | High | Gamification, rewards, community features |
| Skill Mismatch | Medium | Medium | Adaptive difficulty, level adjustments |

### 8.3 Market Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Regime Change | High | High | Regular model updates, ensemble approach |
| Black Swan Events | Low | High | Model cannot predict, focus on resilience |
| Data Quality | Medium | Medium | Multiple data sources, validation |
| API Downtime | Medium | Medium | Fallback mechanisms, manual input |

---

## 9. PERFORMANCE BENCHMARKS

### 9.1 Response Time Requirements

| Operation | Target (ms) | Warning (ms) | Critical (ms) |
|-----------|-------------|--------------|---------------|
| Question Generation | 10,000 | 20,000 | 30,000 |
| Answer Evaluation | 3,000 | 5,000 | 10,000 |
| Level Completion | 5,000 | 10,000 | 15,000 |
| Dashboard Load | 500 | 1,000 | 2,000 |
| ML Prediction | 1,000 | 2,000 | 5,000 |

### 9.2 Capacity Planning

| Metric | Current | Month 1 | Month 3 | Month 6 |
|--------|---------|---------|---------|---------|
| Users | - | 100 | 500 | 1,000 |
| Daily Active | - | 50 | 300 | 600 |
| Questions/Day | - | 1,000 | 9,500 | 19,000 |
| LLM Tokens/Day | - | 200K | 2M | 4M |
| API Calls/Day | - | 5,000 | 25,000 | 50,000 |

---

## 10. TESTING STRATEGY

### 10.1 Unit Testing

```python
# Test question generation
def test_question_generation():
    generator = QuestionGeneratorLLM()
    questions = generator.generate_questions(level=1, user_profile={})
    assert len(questions) == 19
    assert all(q['type'] in ['mcq_single', 'mcq_multiple', 'saq'] for q in questions)

# Test answer evaluation
def test_answer_evaluation():
    rag = RAGModel()
    score = rag.evaluate_answer(mcq_question, correct_answer)
    assert score == 1.0
    
# Test session management
def test_session_management():
    session_manager = SessionManager()
    session = session_manager.create_session(user_id=1)
    assert session['status'] == 'active'
    assert session['current_index'] == 0
```

### 10.2 Integration Testing

```python
# Test full flow
def test_full_hitl_flow():
    # 1. Generate questions
    questions = generator.generate_questions(user_id=1, level=1)
    
    # 2. Submit answers
    for i, q in enumerate(questions):
        answer = get_mock_answer(q)
        result = orchestrator.process_answer(user_id=1, q_id=q['id'], answer=answer)
        assert result['status'] in ['in_progress', 'level_complete']
    
    # 3. Verify completion
    final_result = orchestrator.get_session_status(user_id=1)
    assert final_result['level_complete'] == True
    assert final_result['reward'] > 0
```

### 10.3 A/B Testing Framework

```python
class ABTest:
    def __init__(self, test_name, variants):
        self.test_name = test_name
        self.variants = variants
        self.results = {v: {'count': 0, 'success': 0} for v in variants}
    
    def assign_variant(self, user_id):
        variant = hash(user_id) % len(self.variants)
        return self.variants[variant]
    
    def track_result(self, variant, success):
        self.results[variant]['count'] += 1
        if success:
            self.results[variant]['success'] += 1
    
    def get_winner(self):
        best_variant = max(self.results.items(), 
                          key=lambda x: x[1]['success'] / x[1]['count'])
        return best_variant[0]
```

---

## 11. DEPLOYMENT PLAN

### 11.1 Environment Setup

```yaml
# docker-compose.prod.yml
services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/finnexus
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=finnexus
    volumes:
      - pg_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
```

### 11.2 CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy FINNEXUS HITL

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          python -m pytest tests/
          npm test
    
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Production
        uses: appleboy/ssh-action@v0.1.10
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /var/www/finnexus
            git pull origin main
            docker-compose pull
            docker-compose up -d
```

---

## 12. MAINTENANCE & EVOLUTION

### 12.1 Monitoring Dashboard

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

# Question generation metrics
questions_generated = Counter('questions_generated_total', 'Total questions generated')
question_gen_time = Histogram('question_generation_seconds', 'Time to generate questions')

# Answer metrics
answers_submitted = Counter('answers_submitted_total', 'Total answers submitted')
answer_score = Gauge('answer_average_score', 'Average answer score')

# ML metrics
prediction_accuracy = Gauge('prediction_accuracy', 'Model prediction accuracy')
hitl_improvement = Gauge('hitl_improvement', 'HITL improvement over baseline')

# User metrics
active_users = Gauge('active_users', 'Number of active users')
level_completions = Counter('level_completions_total', 'Total level completions')
cash_distributed = Counter('paper_cash_distributed', 'Total paper cash distributed')
```

### 12.2 Scheduled Tasks

```python
# Celery scheduled tasks
@celery.task
def update_knowledge_base():
    """Update RAG documents daily"""
    fetch_market_news()
    update_vector_db()
    generate_summaries()

@celery.task
def retrain_ml_model():
    """Retrain ML model weekly"""
    fetch_new_data()
    engineer_features()
    train_ensemble()
    validate_performance()

@celery.task
def evaluate_hitl_performance():
    """Evaluate HITL performance monthly"""
    calculate_accuracy()
    analyze_user_insights()
    generate_performance_report()

@celery.task
def optimize_llm_prompts():
    """Optimize prompts monthly"""
    analyze_question_quality()
    test_variations()
    deploy_best_prompts()
```

### 12.3 Continuous Improvement

| Cycle | Activity | Frequency | Owner |
|-------|----------|-----------|-------|
| Weekly | Review model performance | Weekly | ML Team |
| Monthly | Update knowledge base | Monthly | Research Team |
| Monthly | Optimize LLM prompts | Monthly | AI Team |
| Quarterly | User feedback analysis | Quarterly | Product Team |
| Quarterly | Feature enhancement | Quarterly | Dev Team |

---

## 13. COST ESTIMATES

### 13.1 Monthly Infrastructure Costs

| Service | Cost (USD) | Cost (INR) | Justification |
|---------|------------|------------|---------------|
| OpenAI API | $500-1,000 | ₹41,500-83,000 | 2M tokens/day |
| Pinecone | $300-500 | ₹24,900-41,500 | Vector DB |
| AWS Server | $300-500 | ₹24,900-41,500 | ML + API |
| PostgreSQL | $100-200 | ₹8,300-16,600 | Database |
| Redis | $50-100 | ₹4,150-8,300 | Cache |
| **Total** | **$1,250-2,300** | **₹1,03,750-1,90,900** | - |

### 13.2 Development Costs

| Resource | Cost (INR) | Description |
|----------|------------|-------------|
| 1 Full-Stack Developer | ₹2,00,000/month | Frontend + Backend |
| 1 ML Engineer | ₹2,00,000/month | Model development |
| 1 AI Engineer | ₹1,80,000/month | LLM + RAG |
| 1 DevOps Engineer | ₹1,50,000/month | Infrastructure |
| **Total** | **₹7,30,000/month** | Team costs |

---

## 14. APPENDIX

### 14.1 Level Question Templates

#### Level 1 Template (MCQ Single)

```json
{
  "type": "mcq_single",
  "question": "When analyzing a stock's trend, which moving average combination is most commonly used to identify the overall direction?",
  "options": [
    "A. 20-day and 50-day",
    "B. 50-day and 200-day",
    "C. 10-day and 30-day",
    "D. 100-day and 300-day",
    "E. 5-day and 20-day"
  ],
  "difficulty": 1,
  "topic": "Technical Analysis",
  "hint": "Think about what institutional traders typically use for trend identification."
}
```

#### Level 3 Template (MCQ Multiple)

```json
{
  "type": "mcq_multiple",
  "question": "Which of the following are characteristics of a healthy bull market?",
  "options": [
    "A. Higher highs and higher lows",
    "B. Increasing volume on up days",
    "C. Overbought RSI (>70)",
    "D. Rising 50-day MA",
    "E. Expanding PE ratios",
    "F. Increasing short interest"
  ],
  "max_select": 3,
  "difficulty": 3,
  "topic": "Market Analysis"
}
```

### 14.2 SAQ Evaluation Rubric

```json
{
  "criteria": [
    {
      "dimension": "Relevance",
      "weight": 0.25,
      "description": "How directly does the answer address the question?"
    },
    {
      "dimension": "Accuracy",
      "weight": 0.25,
      "description": "Are the facts and data points correct?"
    },
    {
      "dimension": "Depth",
      "weight": 0.20,
      "description": "Does the answer demonstrate thorough understanding?"
    },
    {
      "dimension": "Application",
      "weight": 0.15,
      "description": "Does the answer show practical trading application?"
    },
    {
      "dimension": "Clarity",
      "weight": 0.15,
      "description": "Is the answer well-structured and clearly written?"
    }
  ]
}
```

---

## 15. CONCLUSION

### 15.1 Key Takeaways

1. **Target Accuracy:** 65-75% (up from 55-61%)
2. **Implementation Time:** 12 weeks
3. **Core Components:** LLM + RAG + ML + Orchestrator
4. **Success Factors:** User quality + System learning + Context awareness

### 15.2 Next Steps

1. ✅ Complete HITL Plan approval
2. ✅ Set up development environment
3. ✅ Begin Phase 1 implementation
4. ✅ Schedule weekly reviews
5. ✅ Prepare for Beta launch

---

## 16. CONTACT & SUPPORT

**Project Lead:** [Ashutosh_3021!]
**Technical Lead:** [Ashutosh_3021!]
**Documentation:** [Link to docs]

---

*Document Version: 1.0*
*Last Updated: June 2026*
*Next Review: Quarterly*