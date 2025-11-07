import React, { useState, useEffect } from 'react';
import './DSACompiler.css';

const DSACompiler = () => {
  const [difficulty, setDifficulty] = useState('Easy');
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [code, setCode] = useState('');
  const [input, setInput] = useState('');
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [isRunning, setIsRunning] = useState(false);

  // DSA Questions Database
  const questions = {
    Easy: [
      {
        id: 1,
        title: 'Two Sum',
        description: 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.',
        example: 'Input: nums = [2,7,11,15], target = 9\nOutput: [0,1]\nExplanation: Because nums[0] + nums[1] == 9, we return [0, 1].',
        template: 'function twoSum(nums, target) {\n    // Your code here\n    return [];\n}',
        testCases: [
          { input: '[2,7,11,15], 9', expected: '[0,1]' },
          { input: '[3,2,4], 6', expected: '[1,2]' },
          { input: '[3,3], 6', expected: '[0,1]' }
        ]
      },
      {
        id: 2,
        title: 'Palindrome Number',
        description: 'Given an integer x, return true if x is a palindrome, and false otherwise.',
        example: 'Input: x = 121\nOutput: true\nExplanation: 121 reads as 121 from left to right and from right to left.',
        template: 'function isPalindrome(x) {\n    // Your code here\n    return false;\n}',
        testCases: [
          { input: '121', expected: 'true' },
          { input: '-121', expected: 'false' },
          { input: '10', expected: 'false' }
        ]
      },
      {
        id: 3,
        title: 'Reverse String',
        description: 'Write a function that reverses a string. The input string is given as an array of characters s.',
        example: 'Input: s = ["h","e","l","l","o"]\nOutput: ["o","l","l","e","h"]',
        template: 'function reverseString(s) {\n    // Your code here\n    return s;\n}',
        testCases: [
          { input: '["h","e","l","l","o"]', expected: '["o","l","l","e","h"]' },
          { input: '["H","a","n","n","a","h"]', expected: '["h","a","n","n","a","H"]' }
        ]
      },
      {
        id: 4,
        title: 'Valid Parentheses',
        description: 'Given a string s containing just the characters \'(\', \')\', \'{\', \'}\', \'[\' and \']\', determine if the input string is valid.',
        example: 'Input: s = "()"\nOutput: true',
        template: 'function isValid(s) {\n    // Your code here\n    return false;\n}',
        testCases: [
          { input: '"()"', expected: 'true' },
          { input: '"()[]{}"', expected: 'true' },
          { input: '"(]"', expected: 'false' }
        ]
      },
      {
        id: 5,
        title: 'Maximum Subarray',
        description: 'Given an integer array nums, find the contiguous subarray (containing at least one number) which has the largest sum and return its sum.',
        example: 'Input: nums = [-2,1,-3,4,-1,2,1,-5,4]\nOutput: 6\nExplanation: [4,-1,2,1] has the largest sum = 6.',
        template: 'function maxSubArray(nums) {\n    // Your code here\n    return 0;\n}',
        testCases: [
          { input: '[-2,1,-3,4,-1,2,1,-5,4]', expected: '6' },
          { input: '[1]', expected: '1' },
          { input: '[5,4,-1,7,8]', expected: '23' }
        ]
      }
    ],
    Medium: [
      {
        id: 6,
        title: 'Longest Palindromic Substring',
        description: 'Given a string s, return the longest palindromic substring in s.',
        example: 'Input: s = "babad"\nOutput: "bab"\nExplanation: "aba" is also a valid answer.',
        template: 'function longestPalindrome(s) {\n    // Your code here\n    return "";\n}',
        testCases: [
          { input: '"babad"', expected: '"bab" or "aba"' },
          { input: '"cbbd"', expected: '"bb"' },
          { input: '"a"', expected: '"a"' }
        ]
      },
      {
        id: 7,
        title: 'Container With Most Water',
        description: 'You are given an integer array height of length n. Find two lines that together with the x-axis form a container, such that the container contains the most water.',
        example: 'Input: height = [1,8,6,2,5,4,8,3,7]\nOutput: 49',
        template: 'function maxArea(height) {\n    // Your code here\n    return 0;\n}',
        testCases: [
          { input: '[1,8,6,2,5,4,8,3,7]', expected: '49' },
          { input: '[1,1]', expected: '1' }
        ]
      },
      {
        id: 8,
        title: '3Sum',
        description: 'Given an integer array nums, return all the triplets [nums[i], nums[j], nums[k]] such that i != j, i != k, and j != k, and nums[i] + nums[j] + nums[k] == 0.',
        example: 'Input: nums = [-1,0,1,2,-1,-4]\nOutput: [[-1,-1,2],[-1,0,1]]',
        template: 'function threeSum(nums) {\n    // Your code here\n    return [];\n}',
        testCases: [
          { input: '[-1,0,1,2,-1,-4]', expected: '[[-1,-1,2],[-1,0,1]]' },
          { input: '[0,1,1]', expected: '[]' },
          { input: '[0,0,0]', expected: '[[0,0,0]]' }
        ]
      },
      {
        id: 9,
        title: 'Longest Substring Without Repeating Characters',
        description: 'Given a string s, find the length of the longest substring without repeating characters.',
        example: 'Input: s = "abcabcbb"\nOutput: 3\nExplanation: The answer is "abc", with the length of 3.',
        template: 'function lengthOfLongestSubstring(s) {\n    // Your code here\n    return 0;\n}',
        testCases: [
          { input: '"abcabcbb"', expected: '3' },
          { input: '"bbbbb"', expected: '1' },
          { input: '"pwwkew"', expected: '3' }
        ]
      },
      {
        id: 10,
        title: 'Add Two Numbers',
        description: 'You are given two non-empty linked lists representing two non-negative integers. The digits are stored in reverse order. Add the two numbers and return the sum as a linked list.',
        example: 'Input: l1 = [2,4,3], l2 = [5,6,4]\nOutput: [7,0,8]\nExplanation: 342 + 465 = 807.',
        template: 'function addTwoNumbers(l1, l2) {\n    // Your code here\n    return null;\n}',
        testCases: [
          { input: '[2,4,3], [5,6,4]', expected: '[7,0,8]' },
          { input: '[0], [0]', expected: '[0]' },
          { input: '[9,9,9,9,9,9,9], [9,9,9,9]', expected: '[8,9,9,9,0,0,0,1]' }
        ]
      }
    ],
    Hard: [
      {
        id: 11,
        title: 'Median of Two Sorted Arrays',
        description: 'Given two sorted arrays nums1 and nums2 of size m and n respectively, return the median of the two sorted arrays.',
        example: 'Input: nums1 = [1,3], nums2 = [2]\nOutput: 2.00000\nExplanation: merged array = [1,2,3] and median is 2.',
        template: 'function findMedianSortedArrays(nums1, nums2) {\n    // Your code here\n    return 0;\n}',
        testCases: [
          { input: '[1,3], [2]', expected: '2.0' },
          { input: '[1,2], [3,4]', expected: '2.5' }
        ]
      },
      {
        id: 12,
        title: 'Merge k Sorted Lists',
        description: 'You are given an array of k linked-lists lists, each linked-list is sorted in ascending order. Merge all the linked-lists into one sorted linked-list and return it.',
        example: 'Input: lists = [[1,4,5],[1,3,4],[2,6]]\nOutput: [1,1,2,3,4,4,5,6]',
        template: 'function mergeKLists(lists) {\n    // Your code here\n    return null;\n}',
        testCases: [
          { input: '[[1,4,5],[1,3,4],[2,6]]', expected: '[1,1,2,3,4,4,5,6]' },
          { input: '[]', expected: '[]' },
          { input: '[[]]', expected: '[]' }
        ]
      },
      {
        id: 13,
        title: 'Trapping Rain Water',
        description: 'Given n non-negative integers representing an elevation map where the width of each bar is 1, compute how much water it can trap after raining.',
        example: 'Input: height = [0,1,0,2,1,0,1,3,2,1,2,1]\nOutput: 6',
        template: 'function trap(height) {\n    // Your code here\n    return 0;\n}',
        testCases: [
          { input: '[0,1,0,2,1,0,1,3,2,1,2,1]', expected: '6' },
          { input: '[4,2,0,3,2,5]', expected: '9' }
        ]
      },
      {
        id: 14,
        title: 'N-Queens',
        description: 'The n-queens puzzle is the problem of placing n queens on an n x n chessboard such that no two queens attack each other. Given an integer n, return all distinct solutions to the n-queens puzzle.',
        example: 'Input: n = 4\nOutput: [[".Q..","...Q","Q...","..Q."],["..Q.","Q...","...Q",".Q.."]]',
        template: 'function solveNQueens(n) {\n    // Your code here\n    return [];\n}',
        testCases: [
          { input: '4', expected: '2 solutions' },
          { input: '1', expected: '1 solution' }
        ]
      },
      {
        id: 15,
        title: 'Edit Distance',
        description: 'Given two strings word1 and word2, return the minimum number of operations required to convert word1 to word2. You have three operations: insert, delete, or replace a character.',
        example: 'Input: word1 = "horse", word2 = "ros"\nOutput: 3\nExplanation: horse -> rorse -> rose -> ros',
        template: 'function minDistance(word1, word2) {\n    // Your code here\n    return 0;\n}',
        testCases: [
          { input: '"horse", "ros"', expected: '3' },
          { input: '"intention", "execution"', expected: '5' }
        ]
      }
    ]
  };

  // Generate random question when difficulty changes
  useEffect(() => {
    generateQuestion();
  }, [difficulty]);

  const generateQuestion = () => {
    const difficultyQuestions = questions[difficulty];
    const randomIndex = Math.floor(Math.random() * difficultyQuestions.length);
    const question = difficultyQuestions[randomIndex];
    setCurrentQuestion(question);
    setCode(question.template);
    setInput('');
    setOutput('');
    setError('');
  };

  const executeCode = () => {
    setIsRunning(true);
    setError('');
    setOutput('');

    try {
      // Create a safe execution context
      const userCode = code;
      const userInput = input.trim();

      // Wrap the code in a try-catch for error handling
      const wrappedCode = `
        try {
          ${userCode}
          
          // Parse input if provided
          let parsedInput = null;
          if (userInput) {
            try {
              parsedInput = JSON.parse(userInput);
            } catch (e) {
              parsedInput = userInput;
            }
          }
          
          // Execute the function based on question type
          let result;
          if (typeof twoSum === 'function') {
            const [nums, target] = parsedInput || [[2,7,11,15], 9];
            result = twoSum(nums, target);
          } else if (typeof isPalindrome === 'function') {
            result = isPalindrome(parsedInput !== null ? parsedInput : 121);
          } else if (typeof reverseString === 'function') {
            const arr = parsedInput || ["h","e","l","l","o"];
            reverseString(arr);
            result = arr;
          } else if (typeof isValid === 'function') {
            result = isValid(parsedInput !== null ? parsedInput : "()");
          } else if (typeof maxSubArray === 'function') {
            const nums = parsedInput || [-2,1,-3,4,-1,2,1,-5,4];
            result = maxSubArray(nums);
          } else if (typeof longestPalindrome === 'function') {
            result = longestPalindrome(parsedInput !== null ? parsedInput : "babad");
          } else if (typeof maxArea === 'function') {
            const height = parsedInput || [1,8,6,2,5,4,8,3,7];
            result = maxArea(height);
          } else if (typeof threeSum === 'function') {
            const nums = parsedInput || [-1,0,1,2,-1,-4];
            result = threeSum(nums);
          } else if (typeof lengthOfLongestSubstring === 'function') {
            result = lengthOfLongestSubstring(parsedInput !== null ? parsedInput : "abcabcbb");
          } else if (typeof addTwoNumbers === 'function') {
            result = "Linked list solution - check manually";
          } else if (typeof findMedianSortedArrays === 'function') {
            const [nums1, nums2] = parsedInput || [[1,3], [2]];
            result = findMedianSortedArrays(nums1, nums2);
          } else if (typeof mergeKLists === 'function') {
            result = "Linked list solution - check manually";
          } else if (typeof trap === 'function') {
            const height = parsedInput || [0,1,0,2,1,0,1,3,2,1,2,1];
            result = trap(height);
          } else if (typeof solveNQueens === 'function') {
            const n = parsedInput !== null ? parsedInput : 4;
            result = solveNQueens(n);
          } else if (typeof minDistance === 'function') {
            const [word1, word2] = parsedInput || ["horse", "ros"];
            result = minDistance(word1, word2);
          } else {
            result = "Function not recognized. Please use the provided template.";
          }
          
          return JSON.stringify(result, null, 2);
        } catch (err) {
          throw err;
        }
      `;

      // Execute in a controlled environment
      const func = new Function('userInput', wrappedCode);
      const result = func(userInput);
      setOutput(result);
    } catch (err) {
      setError(err.message || 'An error occurred while executing the code.');
      setOutput('');
    } finally {
      setIsRunning(false);
    }
  };

  const handleReset = () => {
    if (currentQuestion) {
      setCode(currentQuestion.template);
      setInput('');
      setOutput('');
      setError('');
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
              <span>📤 Output</span>
            </div>
            {error ? (
              <div className="output-error">
                <strong>Error:</strong>
                <pre>{error}</pre>
              </div>
            ) : (
              <div className="output-content">
                {output ? (
                  <pre>{output}</pre>
                ) : (
                  <p className="output-placeholder">Output will appear here...</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DSACompiler;

