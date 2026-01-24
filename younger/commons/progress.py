#!/usr/bin/env python3
# -*- encoding=utf8 -*-

########################################################################
# Created time: 2026-01-22 
# Author: Jason Young (杨郑鑫).
# E-Mail: AI.Jason.Young@outlook.com
# Last Modified by: Jason Young (杨郑鑫)
# Last Modified time: 2026-01-24 19:01:01
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

    Workers just call manager.update(n) to report progress - everything else is automatic!

    Usage:
        manager = MultipleProcessProgressManager(percent=0.1)

        def worker(chunk, manager):
            for item in chunk:
                process(item)
                manager.update(1)  # Just report items
            return result

        sequence = [...]
        total_items = len(sequence)
        chunks = split_sequence(sequence, chunk_number=number_of_processes*4)
        tasks = [(chunk, manager) for chunk in chunks]
        with manager.progress(total=total_items, desc='Processing'):
            with multiprocessing.Pool(4) as pool:
                results = list(pool.imap_unordered(worker, tasks))
            # Progress bar closes automatically, updates flushed
    """

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

    def flush(self):
        """Flush any remaining accumulated progress into the queue."""
        if self._accumulated_ > 0:
            self._queue_.put(self._accumulated_)
            self._accumulated_ = 0

    def progress(self, total: int, desc: str = 'Processing'):
        """
        Context manager for real-time progress tracking across multiprocessing.

        Just use it as context manager - all progress updates from workers are automatic!

        Args:
            total: Total items to track
            desc: Progress bar description

        Example:
            with manager.progress(total=1000, desc='Processing'):
                with multiprocessing.Pool(4) as pool:
                    results = list(pool.imap_unordered(worker, tasks))
        """

        # Compute effective interval based on total and percent
        self._interval_ = max(1, int(total * self._percent_ / 100))

        pbar = tqdm.tqdm(total=total, desc=desc)
        stop_event = threading.Event()

        def listen():
            """Background listener for real-time queue updates."""
            while not stop_event.is_set():
                try:
                    pbar.update(self._queue_.get(timeout=0.1))
                except queue.Empty:
                    pass
            # After stop_event is set, do a final flush to consume any remaining items in queue
            # This is critical because workers might flush their accumulated progress
            # to the queue right as we're setting stop_event
            while True:
                try:
                    pbar.update(self._queue_.get_nowait())
                except queue.Empty:
                    break

        # Start background listener
        listener_thread = threading.Thread(target=listen, daemon=True)
        listener_thread.start()

        class ProgressContext:
            def __enter__(self_ctx):
                return self_ctx

            def __exit__(self_ctx, *args):
                stop_event.set()
                listener_thread.join()
                # The listener thread now handles final flush internally
                # Just close the progress bar
                pbar.close()

        return ProgressContext()
