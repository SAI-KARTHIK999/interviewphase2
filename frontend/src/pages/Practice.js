import React, { useState, useEffect } from 'react';
import DSACompiler from '../components/DSACompiler';
import { questions } from '../data/dsaQuestions';
import './Practice.css';

const Practice = () => {
  const [view, setView] = useState('categories'); // 'categories', 'problems', 'question', 'compiler'
  const [selectedDifficulty, setSelectedDifficulty] = useState(null);
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [randomQuestion, setRandomQuestion] = useState(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleCategorySelect = (difficulty) => {
    setSelectedDifficulty(difficulty);
    setView('problems');
  };

  const handleProblemSelect = (question) => {
    setSelectedQuestion(question);
    setView('compiler');
  };

  const handleRandomQuestion = () => {
    const allQuestions = [...questions.Easy, ...questions.Medium, ...questions.Hard];
    const random = allQuestions[Math.floor(Math.random() * allQuestions.length)];
    setRandomQuestion(random);
    setView('question');
  };

  const handleCodeItFromQuestion = () => {
    setSelectedQuestion(randomQuestion);
    setView('compiler');
  };

  const handleBack = () => {
    if (view === 'compiler') {
      setView('problems');
      setSelectedQuestion(null);
    } else if (view === 'problems') {
      setView('categories');
      setSelectedDifficulty(null);
    } else if (view === 'question') {
      setView('categories');
      setRandomQuestion(null);
    }
  };

  // Category Selection View
  if (view === 'categories') {
    return (
      <div className={`practice-container ${isVisible ? 'fade-in' : ''}`}>
        <div className="practice-header">
          <div className="header-content">
            <h1>Practice Coding Problems</h1>
            <p>Choose a difficulty level to start practicing</p>
          </div>
        </div>

        <div className="categories-grid">
          <div 
            className="category-card easy"
            onClick={() => handleCategorySelect('Easy')}
          >
            <div className="category-icon">🟢</div>
            <h2>Easy</h2>
            <p>{questions.Easy.length} problems available</p>
            <div className="category-arrow">→</div>
          </div>

          <div 
            className="category-card medium"
            onClick={() => handleCategorySelect('Medium')}
          >
            <div className="category-icon">🟡</div>
            <h2>Medium</h2>
            <p>{questions.Medium.length} problems available</p>
            <div className="category-arrow">→</div>
          </div>

          <div 
            className="category-card hard"
            onClick={() => handleCategorySelect('Hard')}
          >
            <div className="category-icon">🔴</div>
            <h2>Hard</h2>
            <p>{questions.Hard.length} problems available</p>
            <div className="category-arrow">→</div>
          </div>
        </div>

        <div className="random-question-section">
          <button className="random-question-btn" onClick={handleRandomQuestion}>
            <span className="random-icon">🎲</span>
            <span>Try a Random Question</span>
          </button>
        </div>
      </div>
    );
  }

  // Problem List View
  if (view === 'problems') {
    const problemList = questions[selectedDifficulty] || [];
    
    return (
      <div className={`practice-container ${isVisible ? 'fade-in' : ''}`}>
        <div className="practice-header">
          <div className="header-content">
            <button className="back-button" onClick={handleBack}>
              ← Back
            </button>
            <h1>{selectedDifficulty} Problems</h1>
            <p>Select a problem to start coding</p>
          </div>
        </div>

        <div className="problems-list">
          {problemList.map((problem) => (
            <div key={problem.id} className="problem-item">
              <div className="problem-info">
                <h3>{problem.title}</h3>
                <p className="problem-description-preview">{problem.description.substring(0, 100)}...</p>
              </div>
              <button 
                className="code-it-button"
                onClick={() => handleProblemSelect(problem)}
              >
                Code It
              </button>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Full-Page Question View (for random question)
  if (view === 'question') {
    return (
      <div className={`practice-container question-view ${isVisible ? 'fade-in' : ''}`}>
        <div className="question-full-page">
          <div className="question-header-full">
            <button className="back-button" onClick={handleBack}>
              ← Back
            </button>
            <div className="question-title-section">
              <h1>{randomQuestion.title}</h1>
              <span className={`difficulty-badge-full ${
                questions.Easy.some(q => q.id === randomQuestion.id) ? 'easy' :
                questions.Medium.some(q => q.id === randomQuestion.id) ? 'medium' : 'hard'
              }`}>
                {questions.Easy.some(q => q.id === randomQuestion.id) ? 'Easy' :
                 questions.Medium.some(q => q.id === randomQuestion.id) ? 'Medium' : 'Hard'}
              </span>
            </div>
          </div>

          <div className="question-content-full">
            <div className="question-description-full">
              <h3>Description</h3>
              <p>{randomQuestion.description}</p>
            </div>

            <div className="question-example-full">
              <h3>Example</h3>
              <pre>{randomQuestion.example}</pre>
            </div>

            {randomQuestion.testCases && randomQuestion.testCases.length > 0 && (
              <div className="question-testcases-full">
                <h3>Test Cases</h3>
                <ul>
                  {randomQuestion.testCases.map((testCase, idx) => (
                    <li key={idx}>
                      <strong>Input:</strong> {testCase.input} → <strong>Expected:</strong> {testCase.expected}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="question-actions-full">
            <button className="code-it-button-large" onClick={handleCodeItFromQuestion}>
              Code It
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Compiler View
  if (view === 'compiler') {
    return (
      <div className={`practice-container ${isVisible ? 'fade-in' : ''}`}>
        <div className="compiler-header-section">
          <button className="back-button" onClick={handleBack}>
            ← Back to Problems
          </button>
          <h2>Code Editor</h2>
        </div>
        <div className="compiler-section">
          <DSACompiler initialQuestion={selectedQuestion} />
        </div>
      </div>
    );
  }

  return null;
};

export default Practice;
