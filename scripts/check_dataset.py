
from datasets import load_dataset
try:
    print("Trying to load clue/csl...")
    dataset = load_dataset("clue", "csl", split="train", streaming=True)
    print("Success!")
    print(list(dataset.take(1)))
except Exception as e:
    print(f"Failed: {e}")
