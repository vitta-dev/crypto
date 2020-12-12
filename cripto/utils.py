def split_to_chunks(ll, chunk_size):
    chunk_size_counter = 0
    chunk = []
    for item in ll:
        chunk.append(item)
        chunk_size_counter += 1
        if chunk_size_counter == chunk_size:
            yield chunk
            chunk = []
            chunk_size_counter = 0

    if chunk:
        yield chunk