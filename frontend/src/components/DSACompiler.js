import React, { useState, useEffect } from 'react';
import './DSACompiler.css';
import { questions } from '../data/dsaQuestions';

const DSACompiler = ({ initialQuestion = null }) => {
  const [difficulty, setDifficulty] = useState('Easy');
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [code, setCode] = useState('');
  const [input, setInput] = useState('');
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [testResults, setTestResults] = useState([]);
  const [customOutput, setCustomOutput] = useState('');

  // Set initial question if provided
  useEffect(() => {
    if (initialQuestion) {
      setCurrentQuestion(initialQuestion);
      setCode(initialQuestion.template);
      // Determine difficulty based on which array contains the question
      if (questions.Easy.some(q => q.id === initialQuestion.id)) {
        setDifficulty('Easy');
      } else if (questions.Medium.some(q => q.id === initialQuestion.id)) {
        setDifficulty('Medium');
      } else {
        setDifficulty('Hard');
      }
      setInput('');
      setOutput('');
      setCustomOutput('');
      setError('');
      setTestResults([]);
    }
  }, [initialQuestion]);

  // Generate random question when difficulty changes (only if no initial question)
  useEffect(() => {
    if (!initialQuestion) {
      generateQuestion();
    }
  }, [difficulty]);

  const generateQuestion = () => {
    const difficultyQuestions = questions[difficulty];
    const randomIndex = Math.floor(Math.random() * difficultyQuestions.length);
    const question = difficultyQuestions[randomIndex];
    setCurrentQuestion(question);
    setCode(question.template);
    setInput('');
    setOutput('');
    setCustomOutput('');
    setError('');
    setTestResults([]);
  };

  const handleReset = () => {
    if (currentQuestion) {
      setCode(currentQuestion.template);
      setInput('');
      setOutput('');
      setCustomOutput('');
      setError('');
      setTestResults([]);
    }
  };

  // Helper function to parse test case input
  const parseTestCaseInput = (inputStr, functionName) => {
    try {
      // Try to parse as JSON first
      try {
        return JSON.parse(inputStr);
      } catch (e) {
        // If not JSON, try to parse based on function type
        if (functionName === 'twoSum' || functionName === 'threeSum' || functionName === 'maxSubArray' || functionName === 'containsDuplicate') {
          // Array inputs
          const match = inputStr.match(/\[.*?\]/);
          if (match) {
            const arr = JSON.parse(match[0]);
            if (inputStr.includes(',')) {
              const parts = inputStr.split(',').map(s => s.trim());
              if (parts.length === 2 && parts[1].match(/^\d+$/)) {
                return [arr, parseInt(parts[1])];
              }
            }
            return arr;
          }
        } else if (functionName === 'isPalindrome' || functionName === 'lengthOfLongestSubstring' || functionName === 'longestPalindrome' || functionName === 'isValid') {
          // String or number inputs
          if (inputStr.startsWith('"') && inputStr.endsWith('"')) {
            return inputStr.slice(1, -1);
          } else if (!isNaN(inputStr)) {
            return parseInt(inputStr);
          }
          return inputStr;
        } else if (functionName === 'reverseString') {
          // Array of characters
          try {
            return JSON.parse(inputStr);
          } catch (e) {
            return inputStr.split('').filter(c => c !== '[' && c !== ']' && c !== '"' && c !== ',');
          }
        } else if (functionName === 'maxArea' || functionName === 'trap') {
          // Array input
          try {
            return JSON.parse(inputStr);
          } catch (e) {
            return [];
          }
        } else if (functionName === 'findMedianSortedArrays') {
          // Two arrays
          const arrays = inputStr.match(/\[.*?\]/g);
          if (arrays && arrays.length === 2) {
            return [JSON.parse(arrays[0]), JSON.parse(arrays[1])];
          }
        } else if (functionName === 'minDistance' || functionName === 'solveNQueens') {
          // Two strings or number
          if (inputStr.includes(',')) {
            const parts = inputStr.split(',').map(s => s.trim());
            if (parts.length === 2) {
              return [parts[0].replace(/"/g, ''), parts[1].replace(/"/g, '')];
            }
          } else if (!isNaN(inputStr)) {
            return parseInt(inputStr);
          }
        }
        return inputStr;
      }
    } catch (e) {
      return inputStr;
    }
  };

  // Helper function to compare results
  const compareResults = (actual, expected) => {
    try {
      // Parse expected value
      let expectedParsed;
      try {
        expectedParsed = JSON.parse(expected);
      } catch (e) {
        expectedParsed = expected;
      }

      // Deep comparison for arrays and objects
      if (Array.isArray(actual) && Array.isArray(expectedParsed)) {
        if (actual.length !== expectedParsed.length) return false;
        return actual.every((val, idx) => {
          if (Array.isArray(val) && Array.isArray(expectedParsed[idx])) {
            return JSON.stringify(val.sort()) === JSON.stringify(expectedParsed[idx].sort());
          }
          return JSON.stringify(val) === JSON.stringify(expectedParsed[idx]);
        });
      }

      // For arrays with "or" in expected (like "bab" or "aba")
      if (typeof expectedParsed === 'string' && expectedParsed.includes(' or ')) {
        const options = expectedParsed.split(' or ').map(s => s.trim().replace(/"/g, ''));
        return options.some(opt => {
          try {
            const optParsed = JSON.parse(opt);
            return JSON.stringify(actual) === JSON.stringify(optParsed);
          } catch (e) {
            return String(actual) === opt;
          }
        });
      }

      // String comparison
      if (typeof actual === 'string' && typeof expectedParsed === 'string') {
        return actual === expectedParsed;
      }

      // Number comparison
      if (typeof actual === 'number' && typeof expectedParsed === 'number') {
        return Math.abs(actual - expectedParsed) < 0.0001;
      }

      // JSON comparison
      return JSON.stringify(actual) === JSON.stringify(expectedParsed);
    } catch (e) {
      return String(actual) === String(expected);
    }
  };

  // Function to execute code with a specific input
  const executeWithInput = (userCode, testInput, functionName) => {
    try {
      const wrappedCode = `
        try {
          ${userCode}
          
          // Parse input
          let parsedInput = ${JSON.stringify(testInput)};
          
          // Execute the function based on detected name when possible
          let result;
          const fnName = "${functionName || ''}";

          if (fnName && typeof eval(fnName) === 'function') {
            const fn = eval(fnName);
            // If the parsedInput is an array, spread it as arguments; otherwise pass as single arg
            result = Array.isArray(parsedInput) ? fn(...parsedInput) : fn(parsedInput);
          } else if (typeof twoSum === 'function') {
            const [nums, target] = Array.isArray(parsedInput) && parsedInput.length === 2 ? parsedInput : [parsedInput[0], parsedInput[1]];
            result = twoSum(nums, target);
          } else if (typeof isPalindrome === 'function') {
            result = isPalindrome(parsedInput);
          } else if (typeof reverseString === 'function') {
            const arr = Array.isArray(parsedInput) ? [...parsedInput] : parsedInput;
            reverseString(arr);
            result = arr;
          } else if (typeof isValid === 'function') {
            result = isValid(parsedInput);
          } else if (typeof maxSubArray === 'function') {
            result = maxSubArray(parsedInput);
          } else if (typeof longestPalindrome === 'function') {
            result = longestPalindrome(parsedInput);
          } else if (typeof maxArea === 'function') {
            result = maxArea(parsedInput);
          } else if (typeof threeSum === 'function') {
            result = threeSum(parsedInput);
          } else if (typeof lengthOfLongestSubstring === 'function') {
            result = lengthOfLongestSubstring(parsedInput);
          } else if (typeof addTwoNumbers === 'function') {
            result = "Linked list solution - check manually";
          } else if (typeof findMedianSortedArrays === 'function') {
            const [nums1, nums2] = Array.isArray(parsedInput) && parsedInput.length === 2 ? parsedInput : [parsedInput[0], parsedInput[1]];
            result = findMedianSortedArrays(nums1, nums2);
          } else if (typeof mergeKLists === 'function') {
            result = "Linked list solution - check manually";
          } else if (typeof trap === 'function') {
            result = trap(parsedInput);
          } else if (typeof solveNQueens === 'function') {
            result = solveNQueens(parsedInput);
          } else if (typeof minDistance === 'function') {
            const [word1, word2] = Array.isArray(parsedInput) && parsedInput.length === 2 ? parsedInput : [parsedInput[0], parsedInput[1]];
            result = minDistance(word1, word2);
          } else {
            result = "Function not recognized. Please use the provided template.";
          }
          
          return result;
        } catch (err) {
          throw err;
        }
      `;

      const func = new Function('', wrappedCode);
      return func();
    } catch (err) {
      throw err;
    }
  };

  // Function to detect function name from code
  const detectFunctionName = (code) => {
    const functionNames = [
      'twoSum', 'isPalindrome', 'reverseString', 'isValid', 'maxSubArray',
      'longestPalindrome', 'maxArea', 'threeSum', 'lengthOfLongestSubstring',
      'addTwoNumbers', 'findMedianSortedArrays', 'mergeKLists', 'trap',
      'solveNQueens', 'minDistance', 'containsDuplicate'
    ];

    // First, try to match known function names
    for (const name of functionNames) {
      if (code.includes(`function ${name}`) || code.includes(`${name} =`) || code.includes(`const ${name}`)) {
        return name;
      }
    }

    // If no known name is found, try to detect any function declaration as a fallback
    const fnDeclMatch = code.match(/function\s+([a-zA-Z0-9_]+)/);
    if (fnDeclMatch && fnDeclMatch[1]) {
      return fnDeclMatch[1];
    }

    // Arrow function or const assignment like: const solution = (...) => { }
    const constFnMatch = code.match(/const\s+([a-zA-Z0-9_]+)\s*=\s*\(/);
    if (constFnMatch && constFnMatch[1]) {
      return constFnMatch[1];
    }

    return null;
  };

  // Updated executeCode to run test cases
  const executeCode = () => {
    setIsRunning(true);
    setError('');
    setOutput('');
    setCustomOutput('');
    setTestResults([]);

    try {
      const userCode = code;
      const userInput = input.trim();
      const functionName = detectFunctionName(userCode);

      // If user provided custom input, run with that
      if (userInput) {
        try {
          let parsedInput = null;
          try {
            parsedInput = JSON.parse(userInput);
          } catch (e) {
            parsedInput = userInput;
          }

          const wrappedCode = `
            try {
              ${userCode}
              
              let parsedInput = ${JSON.stringify(parsedInput)};
              let result;
              const fnName = "${functionName || ''}";

              if (fnName && typeof eval(fnName) === 'function') {
                const fn = eval(fnName);
                result = Array.isArray(parsedInput) ? fn(...parsedInput) : fn(parsedInput);
              } else if (typeof twoSum === 'function') {
                const [nums, target] = Array.isArray(parsedInput) && parsedInput.length === 2 ? parsedInput : [parsedInput[0], parsedInput[1]];
                result = twoSum(nums, target);
              } else if (typeof isPalindrome === 'function') {
                result = isPalindrome(parsedInput);
              } else if (typeof reverseString === 'function') {
                const arr = Array.isArray(parsedInput) ? [...parsedInput] : parsedInput;
                reverseString(arr);
                result = arr;
              } else if (typeof isValid === 'function') {
                result = isValid(parsedInput);
              } else if (typeof maxSubArray === 'function') {
                result = maxSubArray(parsedInput);
              } else if (typeof longestPalindrome === 'function') {
                result = longestPalindrome(parsedInput);
              } else if (typeof maxArea === 'function') {
                result = maxArea(parsedInput);
              } else if (typeof threeSum === 'function') {
                result = threeSum(parsedInput);
              } else if (typeof lengthOfLongestSubstring === 'function') {
                result = lengthOfLongestSubstring(parsedInput);
              } else if (typeof findMedianSortedArrays === 'function') {
                const [nums1, nums2] = Array.isArray(parsedInput) && parsedInput.length === 2 ? parsedInput : [parsedInput[0], parsedInput[1]];
                result = findMedianSortedArrays(nums1, nums2);
              } else if (typeof trap === 'function') {
                result = trap(parsedInput);
              } else if (typeof solveNQueens === 'function') {
                result = solveNQueens(parsedInput);
              } else if (typeof minDistance === 'function') {
                const [word1, word2] = Array.isArray(parsedInput) && parsedInput.length === 2 ? parsedInput : [parsedInput[0], parsedInput[1]];
                result = minDistance(word1, word2);
              } else {
                result = "Function not recognized. Please use the provided template.";
              }
              
              return JSON.stringify(result, null, 2);
            } catch (err) {
              throw err;
            }
          `;

          const func = new Function('', wrappedCode);
          const result = func();
          setCustomOutput(result);
        } catch (err) {
          setError(`${err.name}: ${err.message}\n${err.stack || ''}`);
          setIsRunning(false);
          return;
        }
      }

      // Run all test cases
      if (currentQuestion && currentQuestion.testCases && currentQuestion.testCases.length > 0) {
        const results = [];
        
        for (let i = 0; i < currentQuestion.testCases.length; i++) {
          const testCase = currentQuestion.testCases[i];
          
          try {
            const parsedInput = parseTestCaseInput(testCase.input, functionName);
            const actualResult = executeWithInput(userCode, parsedInput, functionName);
            const passed = compareResults(actualResult, testCase.expected);
            
            results.push({
              testCase: i + 1,
              input: testCase.input,
              expected: testCase.expected,
              actual: JSON.stringify(actualResult),
              passed: passed,
              error: null
            });
          } catch (err) {
            results.push({
              testCase: i + 1,
              input: testCase.input,
              expected: testCase.expected,
              actual: null,
              passed: false,
              error: `${err.name}: ${err.message}${err.stack ? '\n' + err.stack.split('\n').slice(0, 3).join('\n') : ''}`
            });
          }
        }
        
        setTestResults(results);
        
        // Set summary output
        const passedCount = results.filter(r => r.passed).length;
        const totalCount = results.length;
        const summary = `Test Results: ${passedCount}/${totalCount} passed\n\n`;
        setOutput(summary + results.map(r => 
          `Test Case ${r.testCase}: ${r.passed ? '✅ PASSED' : '❌ FAILED'}\n` +
          `  Input: ${r.input}\n` +
          `  Expected: ${r.expected}\n` +
          (r.actual ? `  Got: ${r.actual}\n` : '') +
          (r.error ? `  Error: ${r.error}\n` : '')
        ).join('\n'));
      } else {
        setOutput('No test cases available for this problem.');
      }
    } catch (err) {
      setError(`${err.name}: ${err.message}\n\nStack Trace:\n${err.stack || 'No stack trace available'}`);
      setOutput('');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="dsa-compiler">
      <div className="compiler-header">
        <h2>💻 DSA Practice Compiler</h2>
        <p>Solve coding problems and test your solutions in real-time</p>
      </div>

      {/* Difficulty Selection */}
      <div className="difficulty-selector">
        <label>Select Difficulty:</label>
        <div className="difficulty-buttons">
          {['Easy', 'Medium', 'Hard'].map((level) => (
            <button
              key={level}
              className={`difficulty-btn ${difficulty === level ? `active ${level.toLowerCase()}` : ''}`}
              onClick={() => setDifficulty(level)}
            >
              {level}
            </button>
          ))}
        </div>
        <button className="new-question-btn" onClick={generateQuestion}>
          🎲 New Question
        </button>
      </div>

      {/* Question Display */}
      {currentQuestion && (
        <div className="question-panel">
          <div className="question-header">
            <h3>{currentQuestion.title}</h3>
            <span className={`difficulty-badge ${difficulty.toLowerCase()}`}>{difficulty}</span>
          </div>
          <div className="question-content">
            <p className="question-description">{currentQuestion.description}</p>
            <div className="question-example">
              <strong>Example:</strong>
              <pre>{currentQuestion.example}</pre>
            </div>
            {currentQuestion.testCases && (
              <div className="test-cases">
                <strong>Test Cases:</strong>
                <ul>
                  {currentQuestion.testCases.map((testCase, idx) => (
                    <li key={idx}>
                      <strong>Input:</strong> {testCase.input} → <strong>Expected:</strong> {testCase.expected}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Code Editor and Output */}
      <div className="compiler-workspace">
        <div className="code-section">
          <div className="section-header">
            <span>📝 Code Editor</span>
            <div className="code-actions">
              <button className="action-btn reset-btn" onClick={handleReset}>
                🔄 Reset
              </button>
              <button 
                className="action-btn run-btn" 
                onClick={executeCode}
                disabled={isRunning}
              >
                {isRunning ? '⏳ Running...' : '▶️ Run Code'}
              </button>
            </div>
          </div>
          <textarea
            className="code-editor"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Write your solution here..."
            spellCheck={false}
          />
        </div>

        <div className="io-section">
          <div className="input-section">
            <div className="section-header">
              <span>📥 Input (Optional)</span>
            </div>
            <textarea
              className="input-editor"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Enter test input (JSON format)..."
            />
          </div>

          <div className="output-section">
            <div className="section-header">
              <span>📤 Results</span>
              {testResults.length > 0 && (
                <span className="test-summary">
                  {testResults.filter(r => r.passed).length}/{testResults.length} Passed
                </span>
              )}
            </div>
            {error ? (
              <div className="output-error">
                <div className="error-header">
                  <strong>❌ Execution Error</strong>
                </div>
                <div className="error-content">
                  <pre>{error}</pre>
                </div>
              </div>
            ) : testResults.length > 0 ? (
              <div className="test-results-container">
                <div className="test-results-summary">
                  <div className={`summary-card ${testResults.every(r => r.passed) ? 'all-passed' : 'some-failed'}`}>
                    <div className="summary-stats">
                      <span className="summary-label">Test Results:</span>
                      <span className="summary-value">
                        {testResults.filter(r => r.passed).length} / {testResults.length} Passed
                      </span>
                    </div>
                    {testResults.every(r => r.passed) ? (
                      <div className="summary-message success">🎉 All test cases passed!</div>
                    ) : (
                      <div className="summary-message failure">⚠️ Some test cases failed</div>
                    )}
                  </div>
                </div>
                <div className="test-cases-results">
                  {testResults.map((result, idx) => (
                    <div key={idx} className={`test-case-result ${result.passed ? 'passed' : 'failed'}`}>
                      <div className="test-case-header">
                        <span className="test-case-number">Test Case {result.testCase}</span>
                        <span className={`test-case-status ${result.passed ? 'passed' : 'failed'}`}>
                          {result.passed ? '✅ PASSED' : '❌ FAILED'}
                        </span>
                      </div>
                      <div className="test-case-details">
                        <div className="test-case-row">
                          <span className="test-label">Input:</span>
                          <span className="test-value">{result.input}</span>
                        </div>
                        <div className="test-case-row">
                          <span className="test-label">Expected:</span>
                          <span className="test-value expected">{result.expected}</span>
                        </div>
                        {result.actual && (
                          <div className="test-case-row">
                            <span className="test-label">Got:</span>
                            <span className={`test-value ${result.passed ? 'actual-passed' : 'actual-failed'}`}>
                              {result.actual}
                            </span>
                          </div>
                        )}
                        {result.error && (
                          <div className="test-case-error">
                            <span className="error-label">Error:</span>
                            <pre className="error-message">{result.error}</pre>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : customOutput ? (
              <div className="output-content">
                <div className="custom-output-header">Custom Input Output:</div>
                <pre>{customOutput}</pre>
              </div>
            ) : output ? (
              <div className="output-content">
                <pre>{output}</pre>
              </div>
            ) : (
              <p className="output-placeholder">Click "Run Code" to test your solution against all test cases...</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DSACompiler;

