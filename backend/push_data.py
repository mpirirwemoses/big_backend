import glob
import subprocess
import os

BATCH_SIZE = 5

def run_cmd(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing command: {cmd}")
        print(result.stderr)
        return False
    return True

def push_data():
    part_files = sorted(glob.glob("*.gz.part*"))
    if not part_files:
        print("No chunk files found.")
        return
        
    print(f"Found {len(part_files)} chunks to push.")
    
    for i in range(0, len(part_files), BATCH_SIZE):
        batch = part_files[i:i+BATCH_SIZE]
        print(f"\n--- Pushing batch {i//BATCH_SIZE + 1} of {len(part_files)//BATCH_SIZE + 1} (files {i+1} to {min(i+BATCH_SIZE, len(part_files))}) ---")
        
        # Add files
        # Windows requires quotes around files if they have spaces, but ours don't.
        # It's safer to add them one by one or join.
        add_cmd = f"git add {' '.join(batch)}"
        if not run_cmd(add_cmd):
            break
            
        # Commit
        commit_cmd = f'git commit -m "Add data chunks {i+1} to {min(i+BATCH_SIZE, len(part_files))}"'
        if not run_cmd(commit_cmd):
            print("Commit failed (perhaps already committed?). Continuing to push...")
            
        # Push
        if not run_cmd("git push"):
            print("Failed to push. Please check your remote connection and permissions. Stopping.")
            break
            
    print("Done pushing data.")

if __name__ == "__main__":
    push_data()
