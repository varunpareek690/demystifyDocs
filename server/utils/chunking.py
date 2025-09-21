import re
from typing import List

class DocumentChunker:
    """Utility for splitting large documents into manageable chunks for AI processing."""
    
    def __init__(self, 
                 max_chunk_size: int = 3000,
                 overlap_size: int = 200,
                 preserve_sentences: bool = True):
        """
        Initialize document chunker.
        
        Args:
            max_chunk_size: Maximum characters per chunk
            overlap_size: Number of characters to overlap between chunks
            preserve_sentences: Whether to try to preserve sentence boundaries
        """
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.preserve_sentences = preserve_sentences

    def chunk_document(self, text: str) -> List[str]:
        """
        Split document into chunks with optional sentence preservation.
        
        Args:
            text: Document text to chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.max_chunk_size:
            return [text]
        
        if self.preserve_sentences:
            return self._chunk_by_sentences(text)
        else:
            return self._chunk_by_characters(text)

    def _chunk_by_sentences(self, text: str) -> List[str]:
        """Chunk text while preserving sentence boundaries."""
        try:
            sentences = re.split(r'(?<=[.!?])\s+', text)
            
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                potential_chunk = current_chunk + (" " if current_chunk else "") + sentence
                
                if len(potential_chunk) <= self.max_chunk_size:
                    current_chunk = potential_chunk
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    
                    if len(sentence) > self.max_chunk_size:
                        long_sentence_chunks = self._chunk_by_characters(sentence)
                        chunks.extend(long_sentence_chunks[:-1])
                        current_chunk = long_sentence_chunks[-1] if long_sentence_chunks else ""
                    else:
                        current_chunk = sentence
            
            # Add final chunk
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            # Add overlap if requested
            if self.overlap_size > 0:
                chunks = self._add_overlap(chunks)
            
            return chunks
            
        except Exception as e:
            return self._chunk_by_characters(text)

    def _chunk_by_characters(self, text: str) -> List[str]:
        """Simple character-based chunking with overlap."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.max_chunk_size
            
            # If this is not the last chunk, try to end at a word boundary
            if end < len(text):
                # Find the last space within the chunk
                last_space = text.rfind(' ', start, end)
                if last_space != -1 and last_space > start + (self.max_chunk_size * 0.7):
                    end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(start + 1, end - self.overlap_size)
        
        return chunks

    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """Add overlap between consecutive chunks."""
        if len(chunks) <= 1 or self.overlap_size <= 0:
            return chunks
        
        overlapped_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            current_chunk = chunks[i]
            
            # Get overlap from previous chunk
            if len(prev_chunk) > self.overlap_size:
                overlap = prev_chunk[-self.overlap_size:]
                last_space = overlap.rfind(' ')
                if last_space != -1:
                    overlap = overlap[last_space+1:]
            else:
                overlap = prev_chunk
            
            # Combine with current chunk
            overlapped_chunk = overlap + " " + current_chunk
            overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks

    def chunk_for_summarization(self, text: str, target_chunks: int = 5) -> List[str]:
        """
        Chunk document specifically for summarization, aiming for a target number of chunks.
        
        Args:
            text: Document text
            target_chunks: Desired number of chunks
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.max_chunk_size:
            return [text]
        
        # Calculate chunk size to get approximately target_chunks
        estimated_chunk_size = min(self.max_chunk_size, len(text) // target_chunks)
        
        # Temporarily adjust chunk size
        original_chunk_size = self.max_chunk_size
        self.max_chunk_size = max(1000, estimated_chunk_size)  # Minimum 1000 chars
        
        try:
            chunks = self.chunk_document(text)
            
            # If we got too many chunks, merge some
            while len(chunks) > target_chunks * 1.5:
                new_chunks = []
                i = 0
                while i < len(chunks):
                    if i + 1 < len(chunks) and len(chunks[i] + " " + chunks[i + 1]) <= self.max_chunk_size:
                        # Merge two chunks
                        new_chunks.append(chunks[i] + " " + chunks[i + 1])
                        i += 2
                    else:
                        new_chunks.append(chunks[i])
                        i += 1
                chunks = new_chunks
            
            return chunks
            
        finally:
            # Restore original chunk size
            self.max_chunk_size = original_chunk_size

    def find_relevant_chunks(self, text: str, query: str, max_chunks: int = 3) -> List[str]:
        """
        Find the most relevant chunks based on keyword matching.
        
        Args:
            text: Document text
            query: Search query or user message
            max_chunks: Maximum chunks to return
            
        Returns:
            List of most relevant chunks
        """
        chunks = self.chunk_document(text)
        
        if len(chunks) <= max_chunks:
            return chunks
        
        # Extract keywords from query
        query_words = set(word.lower().strip('.,!?;:()[]{}')
                         for word in query.split()
                         if len(word) > 2)
        
        chunk_scores = []
        for i, chunk in enumerate(chunks):
            chunk_words = set(word.lower().strip('.,!?;:()[]{}')
                             for word in chunk.split())
            
            # Calculate relevance score
            overlap = query_words.intersection(chunk_words)
            score = len(overlap) / max(len(query_words), 1)
            
            # Boost score for exact phrase matches
            if len(query.strip()) > 10:
                query_lower = query.lower()
                chunk_lower = chunk.lower()
                if query_lower in chunk_lower:
                    score += 0.5
                elif any(phrase in chunk_lower for phrase in query_lower.split('.') if len(phrase.strip()) > 5):
                    score += 0.2
            
            chunk_scores.append((score, i, chunk))
        
        chunk_scores.sort(key=lambda x: x[0], reverse=True)
        selected = sorted(chunk_scores[:max_chunks], key=lambda x: x[1])
        return [chunk for _, _, chunk in selected]

    def get_chunk_metadata(self, chunks: List[str]) -> List[dict]:
        """
        Get metadata for each chunk.
        
        Args:
            chunks: List of text chunks
            
        Returns:
            List of metadata dicts for each chunk
        """
        metadata = []
        
        for i, chunk in enumerate(chunks):
            word_count = len(chunk.split())
            char_count = len(chunk)
            
            # Estimate sentences
            sentence_count = len([s for s in chunk.replace('!', '.').replace('?', '.').split('.') if s.strip()])
            
            metadata.append({
                'chunk_index': i,
                'character_count': char_count,
                'word_count': word_count,
                'sentence_count': sentence_count,
                'avg_words_per_sentence': word_count / max(sentence_count, 1),
                'preview': chunk[:100] + ('...' if len(chunk) > 100 else '')
            })
        
        return metadata

    def recombine_chunks(self, chunks: List[str], separator: str = "\n\n") -> str:
        """
        Recombine chunks back into a single document.
        
        Args:
            chunks: List of text chunks
            separator: String to use between chunks
            
        Returns:
            Combined text
        """
        return separator.join(chunk.strip() for chunk in chunks if chunk.strip())

    def estimate_processing_cost(self, text: str, cost_per_token: float = 0.0001) -> dict:
        """
        Estimate the processing cost for the text based on chunking.
        
        Args:
            text: Document text
            cost_per_token: Cost per token (rough estimate)
            
        Returns:
            Dict with cost estimates
        """
        chunks = self.chunk_document(text)
        
        # Rough token estimation (1 token ≈ 4 characters)
        total_tokens = sum(len(chunk) // 4 for chunk in chunks)
        
        return {
            'total_chunks': len(chunks),
            'estimated_tokens': total_tokens,
            'estimated_cost_usd': total_tokens * cost_per_token,
            'processing_time_estimate_seconds': len(chunks) * 2,  # Rough estimate
            'chunk_sizes': [len(chunk) for chunk in chunks]
        }