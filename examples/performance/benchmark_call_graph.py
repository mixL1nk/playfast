#!/usr/bin/env python3
"""
Benchmark: Sequential vs Parallel Call Graph Construction (Memory Efficient)

Runs each version separately to avoid memory issues with large APKs.
"""

import sys
import time
import gc
from playfast import core


def benchmark_sequential(apk_path, class_filter=None):
    """Benchmark sequential version only"""
    print("[1/2] Sequential version...")
    gc.collect()

    start = time.time()
    try:
        graph = core.build_call_graph_from_apk(apk_path, class_filter)
        elapsed = time.time() - start
        stats = graph.get_stats()

        print(f"      ✅ Done in {elapsed:.1f}s")
        print(f"      Methods: {stats['total_methods']}")
        print(f"      Edges: {stats['total_edges']}")

        return elapsed, stats
    except Exception as e:
        print(f"      ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    finally:
        # Force garbage collection to free memory
        gc.collect()


def benchmark_parallel(apk_path, class_filter=None):
    """Benchmark parallel version only"""
    print("\n[2/2] Parallel version...")
    gc.collect()

    start = time.time()
    try:
        graph = core.build_call_graph_from_apk_parallel(apk_path, class_filter)
        elapsed = time.time() - start
        stats = graph.get_stats()

        print(f"      ✅ Done in {elapsed:.1f}s")
        print(f"      Methods: {stats['total_methods']}")
        print(f"      Edges: {stats['total_edges']}")

        return elapsed, stats
    except Exception as e:
        print(f"      ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    finally:
        # Force garbage collection to free memory
        gc.collect()


def main():
    if len(sys.argv) < 2:
        print("Usage: python benchmark_parallel_separate.py <apk> [package_filter]")
        print("\nExample:")
        print("  python benchmark_parallel_separate.py app.apk")
        print("  python benchmark_parallel_separate.py app.apk com.example")
        return

    apk_path = sys.argv[1]
    class_filter = [sys.argv[2]] if len(sys.argv) > 2 else None

    print("\n" + "="*70)
    print("Call Graph Performance Benchmark (Memory Efficient)")
    print("="*70)
    print(f"APK: {apk_path}")
    if class_filter:
        print(f"Filter: {class_filter}")
    print()

    # Run benchmarks separately
    time_seq, stats_seq = benchmark_sequential(apk_path, class_filter)

    if time_seq is None:
        print("\n❌ Sequential version failed, aborting")
        return

    time_par, stats_par = benchmark_parallel(apk_path, class_filter)

    if time_par is None:
        print("\n❌ Parallel version failed, aborting")
        return

    # Comparison
    print("\n" + "="*70)
    print("Performance Comparison")
    print("="*70)

    speedup = time_seq / time_par if time_par > 0 else 0
    time_saved = time_seq - time_par

    print(f"Sequential: {time_seq:.1f}s")
    print(f"Parallel:   {time_par:.1f}s")
    print(f"")
    print(f"⚡ Speedup:   {speedup:.2f}x")
    print(f"⏱️  Time saved: {time_saved:.1f}s ({time_saved/time_seq*100:.0f}%)")

    # Verify correctness
    if stats_seq == stats_par:
        print(f"\n✅ Results match - parallel version is correct!")
    else:
        print(f"\n⚠️  Warning: Results differ!")
        print(f"   Sequential: {stats_seq}")
        print(f"   Parallel:   {stats_par}")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()
