import sys
import os

print("--- Python Environment Check ---")
print(f"Python Executable: {sys.executable}")
print("\n--- sys.path ---")
for path in sys.path:
    print(path)
print("----------------------------")

# Check for moviepy specifically
try:
    import moviepy.editor
    print("\nSUCCESS: 'moviepy.editor' was imported successfully.")
except ImportError as e:
    print(f"\nERROR: Could not import 'moviepy.editor'. Reason: {e}")