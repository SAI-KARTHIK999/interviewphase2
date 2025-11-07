import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import DSACompiler from '../components/DSACompiler';
import './Practice.css';

const Practice = () => {
  const [activeTab, setActiveTab] = useState('behavioral');
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const interviewCategories = {
    behavioral: {
      title: 'Behavioral Questions',
      icon: '🧠',
      description: 'Questions about past experiences and how you handled situations',
      questions: [
        {
          question: "Tell me about a time when you had to work with a difficult team member.",
          tips: "Focus on your communication skills, problem-solving approach, and positive outcome. Use the STAR method.",
          sample: "In my previous role, I worked with a colleague who consistently missed deadlines, affecting our team's performance..."
        },
        {
          question: "Describe a situation where you had to learn something new quickly.",
          tips: "Highlight your adaptability, learning methods, and how you applied the new knowledge successfully.",
          sample: "When our company adopted a new CRM system, I had only two weeks to become proficient..."
        },
        {
          question: "Tell me about a time you failed and how you handled it.",
          tips: "Show self-awareness, what you learned, and how you improved. End on a positive note.",
          sample: "Early in my career, I underestimated the time needed for a project and missed a critical deadline..."
        },
        {
          question: "Describe a time when you had to persuade someone to see things your way.",
          tips: "Demonstrate your communication skills, empathy, and ability to find common ground.",
          sample: "I needed to convince my manager to invest in new software that would improve our team's efficiency..."
        }
      ]
    },
    technical: {
      title: 'Technical Questions',
      icon: '💻',
      description: 'Role-specific technical knowledge and problem-solving skills',
      questions: [
        {
          question: "Walk me through how you would approach debugging a complex issue.",
          tips: "Show systematic thinking, use of tools, and collaboration with team members.",
          sample: "I start by reproducing the issue, then use logging and debugging tools to isolate the problem..."
        },
        {
          question: "How do you stay updated with the latest technologies in your field?",
          tips: "Mention specific resources, communities, and how you apply new learning.",
          sample: "I regularly follow industry blogs, attend webinars, and participate in online communities..."
        },
        {
          question: "Describe your experience with [specific technology/tool].",
          tips: "Be specific about projects, challenges overcome, and results achieved.",
          sample: "I've worked with React for 3 years, building several large-scale applications..."
        }
      ]
    },
    situational: {
      title: 'Situational Questions',
      icon: '🎯',
      description: 'Hypothetical scenarios to assess your judgment and decision-making',
      questions: [
        {
          question: "What would you do if you disagreed with your manager's decision?",
          tips: "Show respect for hierarchy while demonstrating critical thinking and communication skills.",
          sample: "I would first seek to understand their reasoning, then respectfully present my perspective with supporting data..."
        },
        {
          question: "How would you handle a situation where you have multiple urgent deadlines?",
          tips: "Demonstrate prioritization skills, time management, and communication with stakeholders.",
          sample: "I would assess the impact and urgency of each task, communicate with stakeholders about realistic timelines..."
        },
        {
          question: "What would you do if you realized you made a mistake that could affect the project?",
          tips: "Show accountability, problem-solving, and proactive communication.",
          sample: "I would immediately assess the impact, develop a solution plan, and communicate transparently with my team..."
        }
      ]
    },
    general: {
      title: 'General Questions',
      icon: '❓',
      description: 'Common questions about yourself, motivations, and career goals',
      questions: [
        {
          question: "Tell me about yourself.",
          tips: "Create a compelling 2-minute story connecting your background to the role. Focus on relevant experiences.",
          sample: "I'm a software developer with 5 years of experience building scalable web applications..."
        },
        {
          question: "Why do you want to work here?",
          tips: "Research the company thoroughly. Connect your values and goals with the company's mission.",
          sample: "I'm excited about your company's commitment to innovation and how you're transforming the industry..."
        },
        {
          question: "What is your greatest weakness?",
          tips: "Choose a real weakness that won't disqualify you, and explain how you're actively working to improve it.",
          sample: "I sometimes focus too much on perfecting details, which can slow down my initial progress..."
        },
        {
          question: "Where do you see yourself in 5 years?",
          tips: "Show ambition while aligning with potential career paths at the company.",
          sample: "I see myself having grown both technically and as a leader, potentially mentoring junior developers..."
        }
      ]
    }
  };

  const interviewTips = [
    {
      title: "Research the Company",
      description: "Know your potential employer",
      icon: "🔍",
      details: [
        "Company mission and values",
        "Recent news and achievements",
        "Team structure and culture",
        "Products and services"
      ]
    },
    {
      title: "Prepare Questions",
      description: "Show your genuine interest",
      icon: "❓",
      details: [
        "About the role and expectations",
        "Team dynamics and collaboration",
        "Company culture and growth",
        "Challenges and opportunities"
      ]
    },
    {
      title: "Body Language",
      description: "Non-verbal communication matters",
      icon: "👤",
      details: [
        "Maintain eye contact",
        "Sit up straight and lean forward",
        "Use gestures naturally",
        "Smile and show enthusiasm"
      ]
    }
  ];

  return (
    <div className={`practice-container ${isVisible ? 'fade-in' : ''}`}>
      {/* Header Section */}
      <div className="practice-header">
        <div className="header-content">
          <div className="header-badge">
            <span className="badge-icon">📚</span>
            <span>Interview Preparation</span>
          </div>
          <h1>Master Your Interview Skills</h1>
          <p>Comprehensive resources and practice materials to help you succeed in any interview</p>
        </div>
        <div className="header-actions">
        </div>
      </div>

      {/* DSA Compiler Section */}
      <div className="compiler-section">
        <DSACompiler />
      </div>

      {/* Quick Tips Section */}
      <div className="tips-section">
        <h2>Essential Interview Tips</h2>
        <div className="tips-grid">
          {interviewTips.map((tip, index) => (
            <div key={index} className="tip-card">
              <div className="tip-icon">{tip.icon}</div>
              <h3>{tip.title}</h3>
              <p>{tip.description}</p>
              <ul className="tip-details">
                {tip.details.map((detail, i) => (
                  <li key={i}>{detail}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Question Categories */}
      <div className="questions-section">
        <h2>Practice Questions by Category</h2>
        
        {/* Category Tabs */}
        <div className="category-tabs">
          {Object.entries(interviewCategories).map(([key, category]) => (
            <button
              key={key}
              className={`tab-button ${activeTab === key ? 'active' : ''}`}
              onClick={() => setActiveTab(key)}
            >
              <span className="tab-icon">{category.icon}</span>
              <span>{category.title}</span>
            </button>
          ))}
        </div>

        {/* Active Category Content */}
        <div className="category-content">
          <div className="category-header">
            <h3>{interviewCategories[activeTab].title}</h3>
            <p>{interviewCategories[activeTab].description}</p>
          </div>
          
          <div className="questions-grid">
            {interviewCategories[activeTab].questions.map((item, index) => (
              <div key={index} className="question-card">
                <div className="question-header">
                  <span className="question-number">{index + 1}</span>
                  <h4 className="question-text">{item.question}</h4>
                </div>
                <div className="question-content">
                  <div className="question-tips">
                    <h5>💡 Tips:</h5>
                    <p>{item.tips}</p>
                  </div>
                  <div className="question-sample">
                    <h5>📝 Sample Start:</h5>
                    <p className="sample-text">{item.sample}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Call to Action */}
      <div className="practice-cta">
        <div className="cta-content">
          <h2>Ready to Practice?</h2>
          <p>Continue exploring interview questions and tips to improve your skills</p>
          <div className="cta-actions">
            <Link to="/" className="cta-button secondary large">
              Back to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Practice;
