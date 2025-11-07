# Interview Answer Evaluation Service

## Overview

A comprehensive NLP-powered evaluation service that analyzes interview answers and provides detailed quality scoring based on multiple components:

- **Clarity** (30% weight): How clearly the answer is communicated
- **Relevance** (30% weight): How well the answer addresses the question
- **Correctness** (25% weight): Factual accuracy and completeness
- **Tone** (10% weight): Speaking confidence and engagement
- **STT Confidence** (5% weight): Transcription quality

**Quality Score Formula:**
```
quality_score = 0.30×clarity + 0.30×relevance + 0.25×correctness + 0.10×tone + 0.05×stt_confidence
```

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────┐
│   Evaluation Service (Port 8001)                 │
├──────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌─────────┐│
│  │ Answer      │  │ Tone         │  │ Scoring ││
│  │ Scorer      │  │ Analyzer     │  │ Engine  ││
│  │ (RoBERTa)   │  │ (Sentiment)  │  │         ││
│  └─────────────┘  └──────────────┘  └─────────┘│
├──────────────────────────────────────────────────┤
│           Consent Enforcement Layer              │
│     (validates allow_storage from session)       │
├──────────────────────────────────────────────────┤
│               MongoDB (interview_db)             │
│  ┌──────────┐  ┌─────────┐  ┌─────────────────┐│
│  │ sessions │  │ answers │  │ processing_audit││
│  └──────────┘  └─────────┘  └─────────────────┘│
└──────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
backend/
├── evaluation_service.py          # FastAPI main service
├── scoring_engine.py               # Weighted scoring calculator
├── scoring_config.json             # Configurable weights
├── train_scorer.py                 # Model training script
├── requirements_evaluation.txt     # Dependencies
└── models/
    ├── answer_scorer.py            # NLP scoring models
    └── tone_analyzer.py            # Tone/emotion analysis

frontend/src/components/
├── AnswerScores.jsx                # Score visualization component
└── AnswerScores.css                # Styling
```

## 🚀 Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements_evaluation.txt
```

### 2. Download Required Models

The service will auto-download models on first run:
- `sentence-transformers/all-mpnet-base-v2` (384-dim embeddings)
- `distilbert-base-uncased-finetuned-sst-2-english` (sentiment/tone)

Optional: Install librosa for audio prosody analysis:
```bash
pip install librosa soundfile
```

### 3. Start MongoDB

```bash
# Windows
net start MongoDB

# Linux/Mac
sudo systemctl start mongod
```

### 4. Start Evaluation Service

```bash
cd backend
python evaluation_service.py
```

Service runs on http://localhost:8001

API documentation available at http://localhost:8001/docs

## 📡 API Endpoints

### POST /api/answers/{answer_id}/analyze

Analyze an interview answer and compute quality scores.

**Request:**
```http
POST /api/answers/507f1f77bcf86cd799439011/analyze
Content-Type: application/json

{
  "question_text": "Describe your experience with Python",
  "ground_truth": "Expected answer mentioning frameworks and projects",
  "audio_path": "/path/to/audio.wav"
}
```

**Response:**
```json
{
  "answer_id": "507f1f77bcf86cd799439011",
  "quality_score": 76.4,
  "clarity": 78.0,
  "correctness": 70.0,
  "relevance": 82.0,
  "tone_score": 64.0,
  "stt_confidence": 0.92,
  "components": {
    "clarity_explanation": "Uses concise sentences, minimal hedging",
    "correctness_explanation": "Contains one factual error re: API semantics",
    "relevance_explanation": "Mostly on-topic with slight digression",
    "tone_label": "calm"
  },
  "model_version": "v1.0",
  "created_at": "2025-11-06T18:00:00Z"
}
```

**Status Codes:**
- `200`: Analysis completed successfully
- `400`: Invalid answer_id or missing data
- `403`: Session expired or consent denied
- `404`: Answer or session not found
- `429`: Rate limit exceeded (10 analyses/minute/session)
- `500`: Internal processing error

### GET /api/score/config

Get current scoring configuration.

**Response:**
```json
{
  "weights": {
    "clarity": 0.30,
    "relevance": 0.30,
    "correctness": 0.25,
    "tone": 0.10,
    "stt_confidence": 0.05
  },
  "models": {
    "embedding_model": "sentence-transformers/all-mpnet-base-v2",
    "model_version": "v1.0"
  },
  "thresholds": {
    "async_processing_threshold_seconds": 120,
    "target_latency_ms": 2000
  }
}
```

### PUT /api/score/config

Update scoring configuration (admin endpoint).

**Request:**
```json
{
  "weights": {
    "clarity": 0.35,
    "relevance": 0.30,
    "correctness": 0.25,
    "tone": 0.05,
    "stt_confidence": 0.05
  }
}
```

**Note:** In production, protect this endpoint with authentication.

## 🎯 Scoring Components Explained

### 1. Clarity (0-100)

**What it measures:**
- Sentence structure and conciseness
- Hedge words (maybe, perhaps, possibly)
- Filler words (um, uh, like, you know)
- Average sentence length

**Scoring rules:**
- Base score: 80
- Penalty: -3 points per hedge word (max -20)
- Penalty: -2 points per filler word (max -15)
- Penalty: -10 points for overly long sentences (>30 words)

**Example:**
```
Good:   "I have 5 years of Python experience building web apps."
        → Clarity: 85 (concise, no hedging)

Poor:   "Um, well, maybe I've done some, you know, programming stuff, like basic things."
        → Clarity: 45 (many fillers and hedge words)
```

### 2. Correctness (0-100)

**What it measures:**
- Semantic similarity to ground truth answer (if provided)
- Factual indicators (cites evidence, research)
- ML classifier confidence

**Scoring rules:**
- If ground truth provided: 50% semantic similarity + 50% ML score
- Otherwise: ML classifier only
- Bonus: +5 points for citing evidence

**Example:**
```
Ground Truth: "Python is a high-level interpreted language with dynamic typing."
Good Answer:  "Python uses dynamic typing and is interpreted at runtime."
             → Similarity: 0.78 → Score: 85

Wrong Answer: "Python is a compiled language like C++."
             → Similarity: 0.32 → Score: 40
```

### 3. Relevance (0-100)

**What it measures:**
- Semantic similarity between answer and question
- On-topic vs. digression
- Direct addressing of question

**Scoring rules:**
- Semantic similarity to question × 110 (boosted slightly)
- Threshold: >0.6 = highly relevant, 0.3-0.6 = moderate, <0.3 = low

**Example:**
```
Question: "What is your experience with databases?"
Relevant: "I've worked with PostgreSQL and MongoDB for 3 years..."
          → Relevance: 88

Off-topic: "I really enjoy programming and started coding in college..."
           → Relevance: 35
```

### 4. Tone (0-100)

**What it measures:**
- Text sentiment (positive/neutral/negative)
- Optional: Audio prosody (pitch, speaking rate, energy)

**Tone labels:**
- Enthusiastic (>80): High confidence and energy
- Engaged (60-80): Positive and confident
- Calm (40-60): Neutral and steady
- Reserved (25-40): Low confidence
- Hesitant (<25): Anxious or uncertain

**Example:**
```
Enthusiastic: "I'm really excited about this opportunity and confident in my skills!"
              → Tone: 85 (enthusiastic)

Hesitant: "I'm not sure if I'm qualified, but I'll try my best..."
          → Tone: 32 (hesitant)
```

### 5. STT Confidence (0-1)

**What it measures:**
- Whisper transcription confidence per segment
- Automatically provided by speech-to-text service
- Weighted least (5%) in final score

## ⚙️ Configuration

### Adjusting Scoring Weights

Edit `scoring_config.json`:

```json
{
  "weights": {
    "clarity": 0.30,      // Increase for communication focus
    "relevance": 0.30,    // Increase for on-topic emphasis
    "correctness": 0.25,  // Increase for technical accuracy
    "tone": 0.10,         // Increase for confidence assessment
    "stt_confidence": 0.05
  }
}
```

**Example weight configurations:**

**Technical Interview (emphasize correctness):**
```json
{
  "clarity": 0.25,
  "relevance": 0.25,
  "correctness": 0.40,  // Higher
  "tone": 0.05,
  "stt_confidence": 0.05
}
```

**Communication Skills (emphasize clarity/tone):**
```json
{
  "clarity": 0.40,      // Higher
  "relevance": 0.25,
  "correctness": 0.15,
  "tone": 0.15,         // Higher
  "stt_confidence": 0.05
}
```

### Testing Weight Changes

```bash
# Before change
curl http://localhost:8001/api/score/config

# Update weights
curl -X PUT http://localhost:8001/api/score/config \
  -H "Content-Type: application/json" \
  -d '{"weights": {"clarity": 0.35, "relevance": 0.30, "correctness": 0.25, "tone": 0.05, "stt_confidence": 0.05}}'

# Verify change
curl http://localhost:8001/api/score/config
```

## 🔐 Consent Enforcement

The service enforces consent at every step:

```python
# Pseudocode workflow
1. Fetch answer from database
2. Fetch session and check allow_storage flag
3. Analyze answer (always allowed)
4. IF allow_storage == true:
     Store scores in database
   ELSE:
     Return scores to caller only
5. Log audit entry (always, regardless of storage)
```

**Storage behavior:**

| allow_storage | Analysis Performed | Scores Stored in DB | Audit Logged |
|---------------|-------------------|---------------------|--------------|
| true          | ✅                | ✅                  | ✅           |
| false         | ✅                | ❌                  | ✅           |

## 🧪 Testing

### Run Unit Tests

```bash
cd backend
pytest tests/test_evaluation_service.py -v
```

### Manual Testing

1. **Create a test answer in MongoDB:**
```javascript
use interview_db
db.answers.insertOne({
  session_id: "test_session",
  user_id: "test_user",
  consent_id: "test_consent",
  original_text: "I have 5 years of Python experience building web applications with Django and Flask.",
  stt_confidence: 0.95
})
```

2. **Create a test session:**
```javascript
db.sessions.insertOne({
  session_id: "test_session",
  user_id: "test_user",
  consent_id: "test_consent",
  allow_storage: true,
  allow_audio: true,
  allow_video: true,
  created_at: new Date(),
  expires_at: new Date(Date.now() + 24*60*60*1000),
  status: "active"
})
```

3. **Analyze the answer:**
```bash
curl -X POST http://localhost:8001/api/answers/YOUR_ANSWER_ID/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "What is your Python experience?",
    "ground_truth": "Candidate should mention years of experience and frameworks used"
  }'
```

4. **Verify scores were stored:**
```javascript
db.answers.findOne({_id: ObjectId("YOUR_ANSWER_ID")})
// Should now include quality_score, clarity, correctness, etc.
```

## 🎓 Model Training

### Preparing Training Data

Create `training_data.json`:
```json
[
  {
    "answer_text": "I have extensive experience with Python...",
    "clarity": 85,
    "correctness": 80,
    "relevance": 90
  },
  {
    "answer_text": "Um, well, maybe I've done some programming...",
    "clarity": 45,
    "correctness": 50,
    "relevance": 55
  }
]
```

Minimum 100-200 examples recommended per component.

### Training Models

```bash
cd backend
python train_scorer.py
```

This will:
1. Load training data
2. Fine-tune RoBERTa models for each component
3. Apply isotonic calibration
4. Save models and calibrators

**Output files:**
- `clarity_model.pt`
- `correctness_model.pt`
- `relevance_model.pt`
- `score_calibrator.pkl` (for each)

### Using Fine-tuned Models

Update `models/answer_scorer.py` to load your trained models:
```python
# Load fine-tuned model
self.clarity_model = ScoringModel()
self.clarity_model.load_state_dict(torch.load('clarity_model.pt'))
```

## 📊 Monitoring & Metrics

### Key Metrics to Track

1. **Processing Time**
   - Target: <2s per answer
   - Alert if >5s consistently

2. **Error Rate**
   - Target: <1% failures
   - Alert if >5%

3. **Score Distribution**
   - Monitor avg quality_score over time
   - Alert on sudden shifts (may indicate model drift)

4. **Rate Limit Hits**
   - Track 429 responses
   - May need to increase limits

### Prometheus Integration (Optional)

```python
from prometheus_client import Counter, Histogram

# Add to evaluation_service.py
analysis_duration = Histogram('answer_analysis_duration_seconds', 'Time to analyze answer')
analysis_total = Counter('answer_analysis_total', 'Total analyses performed')
analysis_errors = Counter('answer_analysis_errors', 'Total analysis errors')
```

## 🗑️ Data Retention

**Automatic deletion:** 
- Scores are stored in the `answers` collection with TTL index (30 days)
- Audit logs are permanent for compliance

**Manual cleanup:**
```javascript
// Delete old analysis data
db.answers.deleteMany({
  "analysis_meta.analyzed_at": {
    $lt: new Date(Date.now() - 30*24*60*60*1000)
  }
})
```

## 🔧 Troubleshooting

### Service won't start

**Issue:** `ModuleNotFoundError: No module named 'sentence_transformers'`
**Solution:**
```bash
pip install sentence-transformers transformers torch
```

### Models downloading slowly

**Issue:** First startup takes 5-10 minutes
**Solution:** Models are cached after first download. Use smaller models in `scoring_config.json`:
```json
"embedding_model": "sentence-transformers/all-MiniLM-L6-v2"  // Faster, 384→128 dims
```

### Analysis returns low scores for good answers

**Issue:** Default models not calibrated for your domain
**Solution:** 
1. Collect labeled data (100+ examples)
2. Run `train_scorer.py` to fine-tune
3. Replace default models with trained ones

### High memory usage

**Issue:** Multiple transformer models loaded
**Solution:** Use ONNX-optimized models:
```bash
pip install optimum
# Convert models to ONNX for faster inference
```

## 📖 Frontend Integration

### Using the AnswerScores Component

```jsx
import AnswerScores from './components/AnswerScores';

function InterviewResults() {
  const [analysisData, setAnalysisData] = useState(null);

  useEffect(() => {
    // Fetch analysis from backend
    fetch(`http://localhost:8001/api/answers/${answerId}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question_text: "What is your Python experience?",
        ground_truth: null
      })
    })
      .then(res => res.json())
      .then(data => setAnalysisData(data));
  }, [answerId]);

  return (
    <div>
      <h1>Interview Results</h1>
      <AnswerScores analysisData={analysisData} />
    </div>
  );
}
```

## 🎯 Best Practices

1. **Always provide question_text** for better relevance scoring
2. **Use ground_truth** when available for technical questions
3. **Calibrate models** with domain-specific training data
4. **Monitor score distributions** to detect drift
5. **Test weight changes** with A/B testing before deploying
6. **Rate limit per user** not just per session
7. **Cache model outputs** for identical texts

## 📚 Additional Resources

- [Sentence Transformers Documentation](https://www.sbert.net/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Model Calibration Guide](https://scikit-learn.org/stable/modules/calibration.html)

## 🤝 Support

For issues or questions:
1. Check logs: service outputs detailed INFO/DEBUG messages
2. Test with curl examples above
3. Verify MongoDB connection and data
4. Check model downloads completed

## 📝 License

This evaluation service is part of the AI Interview Bot project.
