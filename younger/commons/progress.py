#!/usr/bin/env python3
# -*- encoding=utf8 -*-

########################################################################
# Created time: 2026-01-22 
# Author: Jason Young (杨郑鑫).
# E-Mail: AI.Jason.Young@outlook.com
# Last Modified by: Jason Young (杨郑鑫)
# Last Modified time: 2026-01-24 19:30:55
# Copyright (c) 2025 Yangs.AI
# 
# This source code is licensed under the Apache License 2.0 found in the
# LICENSE file in the root directory of this source tree.
########################################################################


import tqdm
import queue
import atexit
import threading
import multiprocessing


class MultipleProcessProgressManager:
    """
    A simple manager for tracking progress across multiple processes.

    Workers just call manager.update(n) to report progress and manager.done() when finished!

    Usage:
        manager = MultipleProcessProgressManager(percent=0.1)

        def worker(chunk, manager):
            for item in chunk:
                process(item)
                manager.update(1)  # Just report items
            manager.done()  # Signal completion
            return result

        sequence = [...]
        total_items = len(sequence)
        chunks = split_sequence(sequence, chunk_number=number_of_processes*4)
        tasks = [(chunk, manager) for chunk in chunks]
        with manager.progress(total=total_items, chunks=len(chunks), desc='Processing'):
            with multiprocessing.Pool(4) as pool:
                results = list(pool.imap_unordered(worker, tasks))
            # Progress bar closes automatically after all chunks signal completion
    """

    _DONE_SIGNAL_ = "__CHUNK_DONE__"  # Sentinel for chunk completion

    def __init__(self, percent: float):
        """
        Initialize the progress manager.

        Args:
            percent: Percentage of total items for IPC batching. The effective interval is
                     max(1, int(total * percent / 100)) for each progress run.
        """
        self._queue_ = multiprocessing.Manager().Queue()
        self._percent_ = percent
        self._interval_ = 1
        self._accumulated_ = 0

    def __getstate__(self):
        """Serialization for multiprocessing."""
        return {
            '_queue_': self._queue_,
            '_percent_': self._percent_,
            '_interval_': self._interval_,
            '_accumulated_': 0
        }

    def __setstate__(self, state):
        """Deserialization for multiprocessing."""
        self._queue_ = state['_queue_']
        self._percent_ = state['_percent_']
        self._interval_ = state.get('_interval_', 1)
        self._accumulated_ = 0
        # Ensure remaining accumulated progress is flushed when the worker process exits
        atexit.register(self.flush)

    def flush(self):
        """Flush any remaining accumulated progress into the queue."""
        if self._accumulated_ > 0:
            self._queue_.put(self._accumulated_)
            self._accumulated_ = 0

    def done(self):
        """Signal that this worker has completed all its work."""
        self.flush()  # Ensure any remaining progress is sent
        self._queue_.put(self._DONE_SIGNAL_)

    def update(self, n: int):
        """
        Report progress from worker process (batched for efficiency).

        Args:
            n: Number of items completed
        """
        self._accumulated_ += n
        if self._accumulated_ >= self._interval_:
            self._queue_.put(self._accumulated_)
            self._accumulated_ = 0

    def progress(self, total: int, chunks: int, desc: str = 'Processing'):
        """
        Context manager for real-time progress tracking across multiprocessing.

        Just use it as context manager - all progress updates from workers are automatic!

        Args:
            total: Total items to track
            chunks: Total number of chunks/workers that will call done()
            desc: Progress bar description

        Example:
            with manager.progress(total=1000, chunks=4, desc='Processing'):
                with multiprocessing.Pool(4) as pool:
                    results = list(pool.imap_unordered(worker, tasks))
        """

        # Compute effective interval based on total and percent
        self._interval_ = max(1, int(total * self._percent_ / 100))

        pbar = tqdm.tqdm(total=total, desc=desc)

        def listen():
            """Background listener for real-time queue updates."""
            completed_chunks = 0
            while completed_chunks < chunks:
                try:
                    msg = self._queue_.get(timeout=0.1)
                    if msg == self._DONE_SIGNAL_:
                        completed_chunks += 1
                    else:
                        pbar.update(msg)
                except queue.Empty:
                    pass

        # Start background listener
        listener_thread = threading.Thread(target=listen, daemon=True)
        listener_thread.start()

        class ProgressContext:
            def __enter__(self_ctx):
                return self_ctx

            def __exit__(self_ctx, *args):
                listener_thread.join()
                pbar.close()

        return ProgressContext()
