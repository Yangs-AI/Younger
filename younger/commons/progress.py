#!/usr/bin/env python3
# -*- encoding=utf8 -*-

########################################################################
# Created time: 2026-01-22 
# Author: Jason Young (杨郑鑫).
# E-Mail: AI.Jason.Young@outlook.com
# Last Modified by: Jason Young (杨郑鑫)
# Last Modified time: 2026-01-22 22:37:45
# Copyright (c) 2025 Yangs.AI
# 
# This source code is licensed under the Apache License 2.0 found in the
# LICENSE file in the root directory of this source tree.
########################################################################


import tqdm
import multiprocessing

from typing import Any
from contextlib import contextmanager


class MultipleProcessProgressManager:
    """
    A utility class to manage progress tracking across multiple processes.

    This manager uses a Queue to collect progress updates from worker processes and displays them in a unified progress bar in the main process.

    Key Features:
    - Automatic queue creation and serialization handling
    - Configurable update percentage at initialization
    - Unified handling for single and multi-process modes
    - Simple API: just pass manager to worker, call update() in loop

    Example usage:
        # In main process:
        mppmanager = MultipleProcessProgressManager(worker_number=4, step=0.01)
        tasks = [(seq, mppmanager) for seq in seqs]

        with mppmanager.progress(total=len(tasks), desc='Processing') as progress:
            with multiprocessing.Pool(processes=4) as pool:
                for result in pool.imap(worker_func, tasks):
                    progress.update()

        # In worker process:
        def worker_function(parameters):
            seq, manager = parameters
            for i, item in enumerate(seq):
                # Do work...
                manager.update(i, len(seq))  # Automatically sends at intervals
            manager.send_final()  # Send final update
            return result
    """

    def __init__(self, worker_number: int = 1, step: float = 0.005):
        """
        Initialize the progress manager.

        Args:
            worker_number: Number of worker processes (1 for single-process mode)
            step: Percentage interval for progress updates (default: 0.005 = 0.5%)
        """
        self.worker_number = worker_number
        self.step = step
        self.queue = multiprocessing.Manager().Queue()

    def __getstate__(self):
        """Custom serialization for multiprocessing."""
        return {
            'queue': self.queue,
            'worker_number': self.worker_number,
            'step': self.step
        }

    def __setstate__(self, state):
        """Custom deserialization for multiprocessing."""
        self.queue = state['queue']
        self.worker_number = state['worker_number']
        self.step = state['step']

    def update(self, current_index: int, total: int):
        """
        Automatically send progress update at configured intervals.
        Call this in your worker loop - it will only send at appropriate times.

        Args:
            current_index: Current iteration index (0-based)
            total: Total number of items

        Example:
            for i, item in enumerate(data):
                # Do work...
                manager.update(i, len(data))
        """
        update_interval = max(1, int(total * self.step))
        if current_index > 0 and current_index % update_interval == 0:
            self.queue.put(update_interval)

    def final(self, total: int):
        """
        Send final progress update with remaining items. Call at end of worker function.

        Args:
            total: Total number of items processed in this worker
        """
        update_interval = max(1, int(total * self.step))
        last_reported_index = (total // update_interval) * update_interval
        remaining = total - last_reported_index
        if remaining > 0:
            self.queue.put(remaining)

    @contextmanager
    def progress(self, total: int, desc: str = 'Processing'):
        """
        Context manager for tracking progress with a unified progress bar.

        Args:
            total: Total number of items/tasks to process
            desc: Description for the progress bar

        Yields:
            ProgressTracker: Object with update() method to handle progress

        Example:
            with manager.progress(total=100, desc='Loading') as tracker:
                with multiprocessing.Pool(4) as pool:
                    for result in pool.imap(func, tasks):
                        tracker.update() # Updates progress bar and drains queue
        """

        class ProgressTracker:
            def __init__(self, queue: multiprocessing.Queue, progress_bar: tqdm.tqdm):
                self.queue = queue
                self.progress_bar = progress_bar

            def update(self, n: int = 1):
                """Update the progress bar and drain queue messages."""
                # Drain queue messages
                while not self.queue.empty():
                    try:
                        increment = self.queue.get_nowait()
                        self.progress_bar.update(increment)
                    except:
                        break
                # Update for the completed task
                self.progress_bar.update(n)

            def drain_remaining(self):
                """Drain all remaining messages from the queue."""
                while not self.queue.empty():
                    try:
                        increment = self.queue.get_nowait()
                        self.progress_bar.update(increment)
                    except:
                        break

        progress_tracker = ProgressTracker(self.queue, tqdm.tqdm(total=total, desc=desc))
        try:
            yield progress_tracker
        finally:
            # Drain any remaining messages
            progress_tracker.drain_remaining()
            progress_tracker.progress_bar.close()

    def cleanup(self):
        """Cleanup the manager resources. Usually not needed as Manager handles cleanup automatically."""
        self.queue = None
