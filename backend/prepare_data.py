import os
import glob
import zlib

CHUNK_SIZE = 45 * 1024 * 1024  # 45 MB chunks

def process_file(filepath):
    print(f"Compressing and splitting {filepath}...")
    base_name = os.path.basename(filepath)
    
    # Compress the file on the fly and chunk the compressed stream
    compressor = zlib.compressobj(level=6, wbits=31) # 31 = gzip format
    
    part_num = 0
    current_part_size = 0
    out_file = None
    
    def get_out_file():
        nonlocal part_num, current_part_size, out_file
        if out_file is None:
            part_name = f"{base_name}.gz.part{part_num:03d}"
            out_file = open(part_name, 'wb')
            current_part_size = 0
        return out_file

    with open(filepath, 'rb') as f_in:
        while True:
            chunk = f_in.read(1024 * 1024 * 10) # read 10MB uncompressed at a time
            if not chunk:
                break
                
            compressed_chunk = compressor.compress(chunk)
            
            # Write compressed chunk to parts
            idx = 0
            while idx < len(compressed_chunk):
                f = get_out_file()
                space_left = CHUNK_SIZE - current_part_size
                to_write = compressed_chunk[idx:idx+space_left]
                f.write(to_write)
                current_part_size += len(to_write)
                idx += len(to_write)
                
                if current_part_size >= CHUNK_SIZE:
                    out_file.close()
                    out_file = None
                    part_num += 1

        # flush compressor at the end
        compressed_chunk = compressor.flush()
        idx = 0
        while idx < len(compressed_chunk):
            f = get_out_file()
            space_left = CHUNK_SIZE - current_part_size
            to_write = compressed_chunk[idx:idx+space_left]
            f.write(to_write)
            current_part_size += len(to_write)
            idx += len(to_write)
            
            if current_part_size >= CHUNK_SIZE:
                out_file.close()
                out_file = None
                part_num += 1
                
        if out_file:
            out_file.close()
            
    total_parts = part_num + (1 if current_part_size > 0 else 0)
    print(f"Finished {filepath} -> {total_parts} parts created.")

if __name__ == "__main__":
    tsv_files = glob.glob("*.tsv")
    if not tsv_files:
        print("No .tsv files found in the current directory.")
    for f in tsv_files:
        process_file(f)
    print("Done preparing data.")
