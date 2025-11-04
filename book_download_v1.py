#import pandas as pd

#df1 = pd.read_csv("data/books/goodreads_books_descriptions_part0.csv")
#df2 = pd.read_csv("data/books/goodreads_books_descriptions_part1.csv")
#books = pd.concat([df1, df2], ignore_index = True)
# print(books.shape)
# 1021106, 2


import os

def split_csv_strict(file_path, output_dir="split_data", max_size_mb=100):
    os.makedirs(output_dir, exist_ok=True)
    max_size_bytes = max_size_mb * 1024 * 1024

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    with open(file_path, "r", encoding="utf-8") as f:
        header = f.readline()
        chunk_idx = 0
        current_chunk = []
        current_size = len(header.encode("utf-8"))  # include header size

        for line in f:
            line_size = len(line.encode("utf-8"))

            # if adding this line would push us over the limit, write current chunk
            if current_size + line_size > max_size_bytes and current_chunk:
                chunk_file = os.path.join(output_dir, f"{base_name}_part{chunk_idx}.csv")
                with open(chunk_file, "w", encoding="utf-8") as out_f:
                    out_f.write(header)
                    out_f.writelines(current_chunk)
                print(f"✅ Wrote {chunk_file} ({current_size / (1024*1024):.2f} MB)")

                # reset for next chunk
                chunk_idx += 1
                current_chunk = []
                current_size = len(header.encode("utf-8"))

            current_chunk.append(line)
            current_size += line_size

        # write final chunk
        if current_chunk:
            chunk_file = os.path.join(output_dir, f"{base_name}_part{chunk_idx}.csv")
            with open(chunk_file, "w", encoding="utf-8") as out_f:
                out_f.write(header)
                out_f.writelines(current_chunk)
            print(f"✅ Wrote {chunk_file} ({current_size / (1024*1024):.2f} MB)")

    print("🎉 Done! All chunks are safely under 100 MB.")


#split_csv("data/books/goodreads_books_descriptions_part0.csv", output_dir="split_books_0", chunk_size_mb=100)
#split_csv("data/books/goodreads_books_descriptions_part1.csv", output_dir="split_books_0", chunk_size_mb=100)

split_csv_strict("train-00000-of-00002.csv", output_dir = "split_books_0", max_size_mb = 90)
split_csv_strict("train-00001-of-00002.csv", output_dir = "split_books_1", max_size_mb = 90)

# du -h split_books_0/*.csv in the terminal to check file sizes 