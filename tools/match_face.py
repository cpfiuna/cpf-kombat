"""
Simple face-image matcher: place your sample image as
  images/caras/sample.png
then run this script from the project root:
  python tools/match_face.py

It compares the sample against all files in images/caras using a simple
average-hash (aHash) and reports the top matches (smallest Hamming distance).
This does NOT attempt to identify the person (privacy) — it only finds the
most visually similar image files in your `images/caras/` folder so you can
rename or wire them into the game.
"""
import os
import sys
from PIL import Image

CAND_DIR = os.path.join('images', 'caras')
SAMPLE_PATH = os.path.join(CAND_DIR, 'sample.png')

# a simple average hash (aHash) implementation
def average_hash(img, hash_size=8):
    # convert to grayscale and resize to hash_size x hash_size
    img = img.convert('L').resize((hash_size, hash_size), Image.Resampling.LANCZOS)
    pixels = list(img.getdata())
    avg = sum(pixels) / len(pixels)
    bits = ''.join('1' if p > avg else '0' for p in pixels)
    # return as integer
    return int(bits, 2)

def hamming_distance(hash1, hash2):
    x = hash1 ^ hash2
    # count bits
    return bin(x).count('1')

def find_matches(sample_path=SAMPLE_PATH, candidates_dir=CAND_DIR, top_n=5):
    if not os.path.exists(sample_path):
        print(f"Sample image not found: {sample_path}\nPlace the image you showed into this path and name it 'sample.png'.")
        return 1
    if not os.path.isdir(candidates_dir):
        print(f"Candidates directory not found: {candidates_dir}")
        return 1
    try:
        sample = Image.open(sample_path)
    except Exception as e:
        print(f"Failed to open sample: {e}")
        return 1
    s_hash = average_hash(sample)
    results = []
    for fn in os.listdir(candidates_dir):
        fp = os.path.join(candidates_dir, fn)
        if not os.path.isfile(fp):
            continue
        # skip the sample itself
        if os.path.abspath(fp) == os.path.abspath(sample_path):
            continue
        try:
            other = Image.open(fp)
        except Exception:
            continue
        h = average_hash(other)
        dist = hamming_distance(s_hash, h)
        results.append((dist, fn))
    results.sort(key=lambda x: x[0])
    if not results:
        print("No candidate images found in images/caras/")
        return 1
    print(f"Top {min(top_n, len(results))} matches (lower = more similar):")
    for dist, fn in results[:top_n]:
        print(f"  {fn}: distance={dist}")
    return 0

if __name__ == '__main__':
    sys.exit(find_matches())
