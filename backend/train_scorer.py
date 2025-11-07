"""
Model Training Script
Fine-tune RoBERTa/BERT models for interview answer scoring with calibration.
"""

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import RobertaTokenizer, RobertaForSequenceClassification, AdamW
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnswerDataset(Dataset):
    """Dataset for interview answer scoring."""
    
    def __init__(self, texts: List[str], scores: List[float], tokenizer, max_length=512):
        self.texts = texts
        self.scores = scores
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        score = self.scores[idx]
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'score': torch.tensor(score, dtype=torch.float)
        }


class RegressionHead(nn.Module):
    """Regression head for scoring (0-100)."""
    
    def __init__(self, hidden_size=768):
        super().__init__()
        self.regressor = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 1),
            nn.Sigmoid()  # Output 0-1, will scale to 0-100
        )
    
    def forward(self, pooled_output):
        return self.regressor(pooled_output) * 100  # Scale to 0-100


class ScoringModel(nn.Module):
    """RoBERTa-based scoring model."""
    
    def __init__(self, model_name='roberta-base'):
        super().__init__()
        self.roberta = RobertaForSequenceClassification.from_pretrained(
            model_name,
            num_labels=1
        )
        # Replace classification head with regression head
        self.roberta.classifier = RegressionHead()
    
    def forward(self, input_ids, attention_mask):
        outputs = self.roberta.roberta(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        pooled_output = outputs.pooler_output
        score = self.roberta.classifier(pooled_output)
        return score


def load_training_data(data_path: str) -> Tuple[List[str], Dict[str, List[float]]]:
    """
    Load training data from JSON or CSV.
    
    Expected format (JSON):
    [
        {
            "answer_text": "...",
            "clarity": 75,
            "correctness": 80,
            "relevance": 85
        },
        ...
    ]
    
    Or CSV with columns: answer_text, clarity, correctness, relevance
    """
    data_file = Path(data_path)
    
    if data_file.suffix == '.json':
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        texts = [item['answer_text'] for item in data]
        scores = {
            'clarity': [item['clarity'] for item in data],
            'correctness': [item['correctness'] for item in data],
            'relevance': [item['relevance'] for item in data]
        }
    
    elif data_file.suffix == '.csv':
        df = pd.read_csv(data_file)
        texts = df['answer_text'].tolist()
        scores = {
            'clarity': df['clarity'].tolist(),
            'correctness': df['correctness'].tolist(),
            'relevance': df['relevance'].tolist()
        }
    
    else:
        raise ValueError(f"Unsupported file format: {data_file.suffix}")
    
    logger.info(f"Loaded {len(texts)} training examples")
    return texts, scores


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int = 3,
    lr: float = 2e-5,
    device: str = 'cpu'
):
    """
    Train the scoring model.
    """
    model = model.to(device)
    optimizer = AdamW(model.parameters(), lr=lr)
    criterion = nn.MSELoss()
    
    best_val_loss = float('inf')
    
    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0
        for batch in train_loader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            scores = batch['score'].to(device)
            
            optimizer.zero_grad()
            predictions = model(input_ids, attention_mask).squeeze()
            loss = criterion(predictions, scores)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        avg_train_loss = train_loss / len(train_loader)
        
        # Validation
        model.eval()
        val_loss = 0
        predictions_list = []
        targets_list = []
        
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                scores = batch['score'].to(device)
                
                predictions = model(input_ids, attention_mask).squeeze()
                loss = criterion(predictions, scores)
                
                val_loss += loss.item()
                predictions_list.extend(predictions.cpu().numpy())
                targets_list.extend(scores.cpu().numpy())
        
        avg_val_loss = val_loss / len(val_loader)
        mae = mean_absolute_error(targets_list, predictions_list)
        
        logger.info(
            f"Epoch {epoch + 1}/{epochs} - "
            f"Train Loss: {avg_train_loss:.4f}, "
            f"Val Loss: {avg_val_loss:.4f}, "
            f"MAE: {mae:.2f}"
        )
        
        # Save best model
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), 'best_model.pt')
            logger.info(f"Saved best model with val_loss: {best_val_loss:.4f}")
    
    return model


def calibrate_scores(model: nn.Module, data_loader: DataLoader, device: str = 'cpu'):
    """
    Apply isotonic calibration to map model outputs to human-meaningful 0-100 range.
    """
    model.eval()
    predictions = []
    targets = []
    
    with torch.no_grad():
        for batch in data_loader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            scores = batch['score']
            
            preds = model(input_ids, attention_mask).squeeze()
            predictions.extend(preds.cpu().numpy())
            targets.extend(scores.numpy())
    
    predictions = np.array(predictions).reshape(-1, 1)
    targets = np.array(targets)
    
    # Fit isotonic regression
    from sklearn.isotonic import IsotonicRegression
    calibrator = IsotonicRegression(out_of_bounds='clip')
    calibrator.fit(predictions.flatten(), targets)
    
    # Save calibrator
    import joblib
    joblib.dump(calibrator, 'score_calibrator.pkl')
    logger.info("Saved calibrator")
    
    return calibrator


def main():
    """Main training pipeline."""
    
    # Configuration
    DATA_PATH = "training_data.json"  # Replace with your data path
    MODEL_NAME = "roberta-base"
    BATCH_SIZE = 16
    EPOCHS = 3
    LR = 2e-5
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    logger.info(f"Using device: {DEVICE}")
    
    # Load data
    try:
        texts, scores = load_training_data(DATA_PATH)
    except FileNotFoundError:
        logger.error(f"Training data not found at {DATA_PATH}")
        logger.info("Creating sample training data...")
        
        # Create sample data for demonstration
        sample_data = [
            {
                "answer_text": "I have extensive experience with Python and JavaScript. I've built several web applications.",
                "clarity": 85,
                "correctness": 80,
                "relevance": 90
            },
            {
                "answer_text": "Um, well, I think maybe I've done some programming, you know, like basic stuff.",
                "clarity": 45,
                "correctness": 50,
                "relevance": 55
            },
            # Add more examples...
        ]
        
        with open('sample_training_data.json', 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        logger.info("Created sample_training_data.json. Please add more examples and re-run.")
        return
    
    # Train three models (one for each component)
    components = ['clarity', 'correctness', 'relevance']
    
    for component in components:
        logger.info(f"\n{'='*50}")
        logger.info(f"Training {component} model")
        logger.info(f"{'='*50}\n")
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            texts, scores[component], test_size=0.2, random_state=42
        )
        
        # Create datasets
        tokenizer = RobertaTokenizer.from_pretrained(MODEL_NAME)
        train_dataset = AnswerDataset(X_train, y_train, tokenizer)
        val_dataset = AnswerDataset(X_val, y_val, tokenizer)
        
        train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)
        
        # Initialize model
        model = ScoringModel(MODEL_NAME)
        
        # Train
        trained_model = train_model(model, train_loader, val_loader, EPOCHS, LR, DEVICE)
        
        # Save model
        model_path = f"{component}_model.pt"
        torch.save(trained_model.state_dict(), model_path)
        logger.info(f"Saved {component} model to {model_path}")
        
        # Calibrate
        calibrator = calibrate_scores(trained_model, val_loader, DEVICE)
        logger.info(f"Completed training for {component}\n")
    
    logger.info("Training complete!")
    logger.info("\nTo use the trained models:")
    logger.info("1. Update scoring_config.json with model paths")
    logger.info("2. Load models in models/answer_scorer.py")
    logger.info("3. Apply calibration when making predictions")


if __name__ == "__main__":
    main()
