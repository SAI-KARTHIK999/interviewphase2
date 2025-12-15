// Shared DSA Questions Database
export const questions = {
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
    },
    {
      id: 16,
      title: 'Best Time to Buy and Sell Stock',
      description: 'You are given an array prices where prices[i] is the price of a given stock on the ith day. You want to maximize your profit by choosing a single day to buy one stock and choosing a different day in the future to sell that stock.',
      example: 'Input: prices = [7,1,5,3,6,4]\nOutput: 5\nExplanation: Buy on day 2 (price = 1) and sell on day 5 (price = 6), profit = 6-1 = 5.',
      template: 'function maxProfit(prices) {\n    // Your code here\n    return 0;\n}',
      testCases: [
        { input: '[7,1,5,3,6,4]', expected: '5' },
        { input: '[7,6,4,3,1]', expected: '0' }
      ]
    },
    {
      id: 17,
      title: 'Contains Duplicate',
      description: 'Given an integer array nums, return true if any value appears at least twice in the array, and return false if every element is distinct.',
      example: 'Input: nums = [1,2,3,1]\nOutput: true',
      template: 'function containsDuplicate(nums) {\n    // Your code here\n    return false;\n}',
      testCases: [
        { input: '[1,2,3,1]', expected: 'true' },
        { input: '[1,2,3,4]', expected: 'false' },
        { input: '[1,1,1,3,3,4,3,2,4,2]', expected: 'true' }
      ]
    },
    {
      id: 18,
      title: 'Single Number',
      description: 'Given a non-empty array of integers nums, every element appears twice except for one. Find that single one.',
      example: 'Input: nums = [2,2,1]\nOutput: 1',
      template: 'function singleNumber(nums) {\n    // Your code here\n    return 0;\n}',
      testCases: [
        { input: '[2,2,1]', expected: '1' },
        { input: '[4,1,2,1,2]', expected: '4' },
        { input: '[1]', expected: '1' }
      ]
    },
    {
      id: 19,
      title: 'Climbing Stairs',
      description: 'You are climbing a staircase. It takes n steps to reach the top. Each time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?',
      example: 'Input: n = 3\nOutput: 3\nExplanation: There are three ways to climb to the top.\n1. 1 step + 1 step + 1 step\n2. 1 step + 2 steps\n3. 2 steps + 1 step',
      template: 'function climbStairs(n) {\n    // Your code here\n    return 0;\n}',
      testCases: [
        { input: '2', expected: '2' },
        { input: '3', expected: '3' },
        { input: '5', expected: '8' }
      ]
    },
    {
      id: 20,
      title: 'Merge Sorted Array',
      description: 'You are given two integer arrays nums1 and nums2, sorted in non-decreasing order. Merge nums2 into nums1 in-place.',
      example: 'Input: nums1 = [1,2,3,0,0,0], m = 3, nums2 = [2,5,6], n = 3\nOutput: [1,2,2,3,5,6]',
      template: 'function merge(nums1, m, nums2, n) {\n    // Your code here\n}',
      testCases: [
        { input: '[1,2,3,0,0,0], 3, [2,5,6], 3', expected: '[1,2,2,3,5,6]' },
        { input: '[1], 1, [], 0', expected: '[1]' },
        { input: '[0], 0, [1], 1', expected: '[1]' }
      ]
    },
    {
      id: 21,
      title: 'Symmetric Tree',
      description: 'Given the root of a binary tree, check whether it is a mirror of itself (i.e., symmetric around its center).',
      example: 'Input: root = [1,2,2,3,4,4,3]\nOutput: true',
      template: 'function isSymmetric(root) {\n    // Your code here\n    return false;\n}',
      testCases: [
        { input: '[1,2,2,3,4,4,3]', expected: 'true' },
        { input: '[1,2,2,null,3,null,3]', expected: 'false' }
      ]
    },
    {
      id: 22,
      title: 'Maximum Depth of Binary Tree',
      description: 'Given the root of a binary tree, return its maximum depth.',
      example: 'Input: root = [3,9,20,null,null,15,7]\nOutput: 3',
      template: 'function maxDepth(root) {\n    // Your code here\n    return 0;\n}',
      testCases: [
        { input: '[3,9,20,null,null,15,7]', expected: '3' },
        { input: '[1,null,2]', expected: '2' }
      ]
    },
    {
      id: 23,
      title: 'Same Tree',
      description: 'Given the roots of two binary trees p and q, write a function to check if they are the same or not.',
      example: 'Input: p = [1,2,3], q = [1,2,3]\nOutput: true',
      template: 'function isSameTree(p, q) {\n    // Your code here\n    return false;\n}',
      testCases: [
        { input: '[1,2,3], [1,2,3]', expected: 'true' },
        { input: '[1,2], [1,null,2]', expected: 'false' }
      ]
    },
    {
      id: 24,
      title: 'Path Sum',
      description: 'Given the root of a binary tree and an integer targetSum, return true if the tree has a root-to-leaf path such that adding up all the values along the path equals targetSum.',
      example: 'Input: root = [5,4,8,11,null,13,4,7,2,null,null,null,1], targetSum = 22\nOutput: true',
      template: 'function hasPathSum(root, targetSum) {\n    // Your code here\n    return false;\n}',
      testCases: [
        { input: '[5,4,8,11,null,13,4,7,2,null,null,null,1], 22', expected: 'true' },
        { input: '[1,2,3], 5', expected: 'false' }
      ]
    },
    {
      id: 25,
      title: 'Binary Tree Inorder Traversal',
      description: 'Given the root of a binary tree, return the inorder traversal of its nodes\' values.',
      example: 'Input: root = [1,null,2,3]\nOutput: [1,3,2]',
      template: 'function inorderTraversal(root) {\n    // Your code here\n    return [];\n}',
      testCases: [
        { input: '[1,null,2,3]', expected: '[1,3,2]' },
        { input: '[]', expected: '[]' },
        { input: '[1]', expected: '[1]' }
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
    },
    {
      id: 26,
      title: 'Group Anagrams',
      description: 'Given an array of strings strs, group the anagrams together. You can return the answer in any order.',
      example: 'Input: strs = ["eat","tea","tan","ate","nat","bat"]\nOutput: [["bat"],["nat","tan"],["ate","eat","tea"]]',
      template: 'function groupAnagrams(strs) {\n    // Your code here\n    return [];\n}',
      testCases: [
        { input: '["eat","tea","tan","ate","nat","bat"]', expected: '[["bat"],["nat","tan"],["ate","eat","tea"]]' },
        { input: '[""]', expected: '[[""]]' },
        { input: '["a"]', expected: '[["a"]]' }
      ]
    },
    {
      id: 27,
      title: 'Product of Array Except Self',
      description: 'Given an integer array nums, return an array answer such that answer[i] is equal to the product of all the elements of nums except nums[i].',
      example: 'Input: nums = [1,2,3,4]\nOutput: [24,12,8,6]',
      template: 'function productExceptSelf(nums) {\n    // Your code here\n    return [];\n}',
      testCases: [
        { input: '[1,2,3,4]', expected: '[24,12,8,6]' },
        { input: '[-1,1,0,-3,3]', expected: '[0,0,9,0,0]' }
      ]
    },
    {
      id: 28,
      title: 'Search in Rotated Sorted Array',
      description: 'There is an integer array nums sorted in ascending order (with distinct values). Given the array after rotation, find target.',
      example: 'Input: nums = [4,5,6,7,0,1,2], target = 0\nOutput: 4',
      template: 'function search(nums, target) {\n    // Your code here\n    return -1;\n}',
      testCases: [
        { input: '[4,5,6,7,0,1,2], 0', expected: '4' },
        { input: '[4,5,6,7,0,1,2], 3', expected: '-1' },
        { input: '[1], 0', expected: '-1' }
      ]
    },
    {
      id: 29,
      title: 'Combination Sum',
      description: 'Given an array of distinct integers candidates and a target integer target, return a list of all unique combinations of candidates where the chosen numbers sum to target.',
      example: 'Input: candidates = [2,3,6,7], target = 7\nOutput: [[2,2,3],[7]]',
      template: 'function combinationSum(candidates, target) {\n    // Your code here\n    return [];\n}',
      testCases: [
        { input: '[2,3,6,7], 7', expected: '[[2,2,3],[7]]' },
        { input: '[2,3,5], 8', expected: '[[2,2,2,2],[2,3,3],[3,5]]' },
        { input: '[2], 1', expected: '[]' }
      ]
    },
    {
      id: 30,
      title: 'Rotate Image',
      description: 'You are given an n x n 2D matrix representing an image, rotate the image by 90 degrees (clockwise).',
      example: 'Input: matrix = [[1,2,3],[4,5,6],[7,8,9]]\nOutput: [[7,4,1],[8,5,2],[9,6,3]]',
      template: 'function rotate(matrix) {\n    // Your code here\n}',
      testCases: [
        { input: '[[1,2,3],[4,5,6],[7,8,9]]', expected: '[[7,4,1],[8,5,2],[9,6,3]]' },
        { input: '[[5,1,9,11],[2,4,8,10],[13,3,6,7],[15,14,12,16]]', expected: '[[15,13,2,5],[14,3,4,1],[12,6,8,9],[16,7,10,11]]' }
      ]
    },
    {
      id: 31,
      title: 'Word Search',
      description: 'Given an m x n grid of characters board and a string word, return true if word exists in the grid.',
      example: 'Input: board = [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], word = "ABCCED"\nOutput: true',
      template: 'function exist(board, word) {\n    // Your code here\n    return false;\n}',
      testCases: [
        { input: '[["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], "ABCCED"', expected: 'true' },
        { input: '[["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], "SEE"', expected: 'true' },
        { input: '[["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], "ABCB"', expected: 'false' }
      ]
    },
    {
      id: 32,
      title: 'Validate Binary Search Tree',
      description: 'Given the root of a binary tree, determine if it is a valid binary search tree (BST).',
      example: 'Input: root = [2,1,3]\nOutput: true',
      template: 'function isValidBST(root) {\n    // Your code here\n    return false;\n}',
      testCases: [
        { input: '[2,1,3]', expected: 'true' },
        { input: '[5,1,4,null,null,3,6]', expected: 'false' }
      ]
    },
    {
      id: 33,
      title: 'Binary Tree Level Order Traversal',
      description: 'Given the root of a binary tree, return the level order traversal of its nodes\' values.',
      example: 'Input: root = [3,9,20,null,null,15,7]\nOutput: [[3],[9,20],[15,7]]',
      template: 'function levelOrder(root) {\n    // Your code here\n    return [];\n}',
      testCases: [
        { input: '[3,9,20,null,null,15,7]', expected: '[[3],[9,20],[15,7]]' },
        { input: '[1]', expected: '[[1]]' },
        { input: '[]', expected: '[]' }
      ]
    },
    {
      id: 34,
      title: 'Construct Binary Tree from Preorder and Inorder Traversal',
      description: 'Given two integer arrays preorder and inorder where preorder is the preorder traversal of a binary tree and inorder is the inorder traversal of the same tree, construct and return the binary tree.',
      example: 'Input: preorder = [3,9,20,15,7], inorder = [9,3,15,20,7]\nOutput: [3,9,20,null,null,15,7]',
      template: 'function buildTree(preorder, inorder) {\n    // Your code here\n    return null;\n}',
      testCases: [
        { input: '[3,9,20,15,7], [9,3,15,20,7]', expected: '[3,9,20,null,null,15,7]' },
        { input: '[-1], [-1]', expected: '[-1]' }
      ]
    },
    {
      id: 35,
      title: 'Kth Largest Element in an Array',
      description: 'Given an integer array nums and an integer k, return the kth largest element in the array.',
      example: 'Input: nums = [3,2,1,5,6,4], k = 2\nOutput: 5',
      template: 'function findKthLargest(nums, k) {\n    // Your code here\n    return 0;\n}',
      testCases: [
        { input: '[3,2,1,5,6,4], 2', expected: '5' },
        { input: '[3,2,3,1,2,4,5,5,6], 4', expected: '4' }
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
    },
    {
      id: 36,
      title: 'Regular Expression Matching',
      description: 'Given an input string s and a pattern p, implement regular expression matching with support for \'.\' and \'*\' where \'.\' matches any single character and \'*\' matches zero or more of the preceding element.',
      example: 'Input: s = "aa", p = "a*"\nOutput: true\nExplanation: \'*\' means zero or more of the preceding element, \'a\'.',
      template: 'function isMatch(s, p) {\n    // Your code here\n    return false;\n}',
      testCases: [
        { input: '"aa", "a"', expected: 'false' },
        { input: '"aa", "a*"', expected: 'true' },
        { input: '"ab", ".*"', expected: 'true' }
      ]
    },
    {
      id: 37,
      title: 'Merge Intervals',
      description: 'Given an array of intervals where intervals[i] = [starti, endi], merge all overlapping intervals, and return an array of the non-overlapping intervals that cover all the intervals in the input.',
      example: 'Input: intervals = [[1,3],[2,6],[8,10],[15,18]]\nOutput: [[1,6],[8,10],[15,18]]',
      template: 'function merge(intervals) {\n    // Your code here\n    return [];\n}',
      testCases: [
        { input: '[[1,3],[2,6],[8,10],[15,18]]', expected: '[[1,6],[8,10],[15,18]]' },
        { input: '[[1,4],[4,5]]', expected: '[[1,5]]' }
      ]
    },
    {
      id: 38,
      title: 'Serialize and Deserialize Binary Tree',
      description: 'Design an algorithm to serialize and deserialize a binary tree. There is no restriction on how your serialization/deserialization algorithm should work.',
      example: 'Input: root = [1,2,3,null,null,4,5]\nOutput: [1,2,3,null,null,4,5]',
      template: 'function serialize(root) {\n    // Your code here\n    return "";\n}\n\nfunction deserialize(data) {\n    // Your code here\n    return null;\n}',
      testCases: [
        { input: '[1,2,3,null,null,4,5]', expected: 'Serialized and deserialized correctly' }
      ]
    },
    {
      id: 39,
      title: 'Word Ladder',
      description: 'A transformation sequence from word beginWord to word endWord using a dictionary wordList is a sequence such that: Only one letter can be changed at a time. Each transformed word must exist in the word list.',
      example: 'Input: beginWord = "hit", endWord = "cog", wordList = ["hot","dot","dog","lot","log","cog"]\nOutput: 5',
      template: 'function ladderLength(beginWord, endWord, wordList) {\n    // Your code here\n    return 0;\n}',
      testCases: [
        { input: '"hit", "cog", ["hot","dot","dog","lot","log","cog"]', expected: '5' },
        { input: '"hit", "cog", ["hot","dot","dog","lot","log"]', expected: '0' }
      ]
    },
    {
      id: 40,
      title: 'Longest Consecutive Sequence',
      description: 'Given an unsorted array of integers nums, return the length of the longest consecutive elements sequence.',
      example: 'Input: nums = [100,4,200,1,3,2]\nOutput: 4\nExplanation: The longest consecutive elements sequence is [1, 2, 3, 4].',
      template: 'function longestConsecutive(nums) {\n    // Your code here\n    return 0;\n}',
      testCases: [
        { input: '[100,4,200,1,3,2]', expected: '4' },
        { input: '[0,3,7,2,5,8,4,6,0,1]', expected: '9' }
      ]
    },
    {
      id: 41,
      title: 'Candy',
      description: 'There are n children standing in a line. Each child is assigned a rating value. You are giving candies to these children. Each child must have at least one candy. Children with a higher rating get more candies than their neighbors.',
      example: 'Input: ratings = [1,0,2]\nOutput: 5\nExplanation: You can allocate to the first, second and third child with 2, 1, 2 candies respectively.',
      template: 'function candy(ratings) {\n    // Your code here\n    return 0;\n}',
      testCases: [
        { input: '[1,0,2]', expected: '5' },
        { input: '[1,2,2]', expected: '4' }
      ]
    },
    {
      id: 42,
      title: 'Word Break II',
      description: 'Given a string s and a dictionary of strings wordDict, add spaces in s to construct a sentence where each word is a valid dictionary word. Return all such possible sentences in any order.',
      example: 'Input: s = "catsanddog", wordDict = ["cat","cats","and","sand","dog"]\nOutput: ["cats and dog","cat sand dog"]',
      template: 'function wordBreak(s, wordDict) {\n    // Your code here\n    return [];\n}',
      testCases: [
        { input: '"catsanddog", ["cat","cats","and","sand","dog"]', expected: '["cats and dog","cat sand dog"]' },
        { input: '"pineapplepenapple", ["apple","pen","applepen","pine","pineapple"]', expected: '["pine apple pen apple","pineapple pen apple","pine applepen apple"]' }
      ]
    },
    {
      id: 43,
      title: 'LRU Cache',
      description: 'Design a data structure that follows the constraints of a Least Recently Used (LRU) cache.',
      example: 'Input: ["LRUCache","put","put","get","put","get","put","get","get","get"]\n[[2],[1,1],[2,2],[1],[3,3],[2],[4,4],[1],[3],[4]]\nOutput: [null,null,null,1,null,-1,null,-1,3,4]',
      template: 'class LRUCache {\n    constructor(capacity) {\n        // Your code here\n    }\n    \n    get(key) {\n        // Your code here\n    }\n    \n    put(key, value) {\n        // Your code here\n    }\n}',
      testCases: [
        { input: 'Capacity: 2, Operations: put(1,1), put(2,2), get(1), put(3,3), get(2), put(4,4), get(1), get(3), get(4)', expected: '[null,null,null,1,null,-1,null,-1,3,4]' }
      ]
    },
    {
      id: 44,
      title: 'Binary Tree Maximum Path Sum',
      description: 'A path in a binary tree is a sequence of nodes where each pair of adjacent nodes in the sequence has an edge connecting them. Return the maximum path sum.',
      example: 'Input: root = [1,2,3]\nOutput: 6',
      template: 'function maxPathSum(root) {\n    // Your code here\n    return 0;\n}',
      testCases: [
        { input: '[1,2,3]', expected: '6' },
        { input: '[-10,9,20,null,null,15,7]', expected: '42' }
      ]
    },
    {
      id: 45,
      title: 'Wildcard Matching',
      description: 'Given an input string (s) and a pattern (p), implement wildcard pattern matching with support for \'?\' and \'*\' where \'?\' matches any single character and \'*\' matches any sequence of characters.',
      example: 'Input: s = "aa", p = "a"\nOutput: false\nInput: s = "aa", p = "*"\nOutput: true',
      template: 'function isMatch(s, p) {\n    // Your code here\n    return false;\n}',
      testCases: [
        { input: '"aa", "a"', expected: 'false' },
        { input: '"aa", "*"', expected: 'true' },
        { input: '"cb", "?a"', expected: 'false' }
      ]
    }
  ]
};


