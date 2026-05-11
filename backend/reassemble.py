import glob
import os
import zlib

def reassemble(base_name):
    print(f"Reassembling {base_name}...")
    parts = sorted(glob.glob(f"{base_name}.gz.part*"))
    if not parts:
        print(f"No parts found for {base_name}")
        return
        
    decompressor = zlib.decompressobj(wbits=31) # 31 = gzip format
    
    with open(base_name, 'wb') as f_out:
        for part in parts:
            print(f"  Reading {part}...")
            with open(part, 'rb') as f_in:
                while True:
                    chunk = f_in.read(1024 * 1024 * 10) # 10MB chunks
                    if not chunk:
                        break
                    f_out.write(decompressor.decompress(chunk))
                    
        # Flush the decompressor at the end
        f_out.write(decompressor.flush())
        
    print(f"Successfully reassembled {base_name}.")

if __name__ == "__main__":
    # find all base names
    all_parts = glob.glob("*.tsv.gz.part*")
    if not all_parts:
        print("No chunked files found to reassemble.")
    else:
        # Extract unique base names, e.g., 'g_patent.tsv' from 'g_patent.tsv.gz.part000'
        tsv_files = sorted(list(set([f.split('.gz.part')[0] for f in all_parts])))
        for tsv in tsv_files:
            reassemble(tsv)
        print("Done reassembling data.")
