import os
import zipfile

def create_project_zip():
    # Target file name
    zip_filename = "ai_scam_call_shield_project.zip"
    
    # Exclude directories
    exclude_dirs = {
        'venv', '.venv', 'node_modules', '.gradle', 'target', 
        '__pycache__', '.git', '.idea', '.vscode', 'build'
    }
    
    # Exclude files/extensions
    exclude_extensions = {'.pyc', '.db', '.log', '.apk', '.zip'}
    
    # Base directory to zip (the parent or current directory)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Creating zip file: {zip_filename} in {base_dir}")
    print("Excluding large files, node_modules, and virtual environments...")
    
    zip_path = os.path.join(base_dir, zip_filename)
    
    count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(base_dir):
            # Modify dirs in-place to avoid walking down excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                # Skip excluded extensions
                ext = os.path.splitext(file)[1].lower()
                if ext in exclude_extensions:
                    continue
                # Skip the zip file itself if it's already there
                if file == zip_filename:
                    continue
                    
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_dir)
                
                zipf.write(full_path, rel_path)
                count += 1
                
    print(f"Successfully zipped {count} files into {zip_filename}!")

if __name__ == "__main__":
    create_project_zip()
