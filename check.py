import os
import chardet

def detect_csv_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(100000)
        result = chardet.detect(raw_data)
    
    encoding = result['encoding']
    confidence = result['confidence']
    
    print(f"📄 {os.path.basename(file_path)} → {encoding} (confidence: {confidence})")

    if encoding is None or confidence < 0.5:
        print("⚠️  Low confidence in detection. Falling back to 'latin1'")
        encoding = 'latin1'
    
    return encoding

def detect_all_csv_in_directory(folder_path):
    print(f"\n🔍 Scanning directory: {folder_path}\n")
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            full_path = os.path.join(folder_path, filename)
            detect_csv_encoding(full_path)

if __name__ == "__main__":
    folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
    detect_all_csv_in_directory(folder_path)
