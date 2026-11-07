"""Independent audit, held-out labels, recall/F1 and coverage evaluation.

Component evaluation is in ``components.py``; the frame-bound final edge-audit
packet preparation/scoring is separate in ``edge_audit.py``. Component labels
are joined and scored only against an exact frozen frame. These tools cannot
verify reviewer identity, independence or label correctness.
"""
