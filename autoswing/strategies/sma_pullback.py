apply_patch <<'EOF'
*** Begin Patch
*** Update File: autoswing/strategies/sma_pullback.py
@@
-class SMAPullbackStrategy(BaseStrategy):
-    timeframe = "1d"
-    warmup_bars = 30
+class SMAPullbackStrategy(BaseStrategy):
+    timeframe = "1d"
+    warmup_bars = 30
+    max_positions = 5      # will be overwritten by settings if passed in
+    alloc_pct = 0.20       # 20% of settled cash per entry (capped by open slots)
+    max_hold_days = 5      # default timed exit
@@
-    def position_size(self, account, signal):
-        # Phase 1 naive sizing: equal-dollar allocations from account.settled_cash
-        cash = getattr(account, "settled_cash", 0)
-        if cash <= 0:
-            return 0
-        alloc = cash / self.max_positions
-        return int(alloc // signal.price)
+    def position_size(self, account, signal):
+        """Deprecated (Phase 3A uses executor sizing)."""
+        return 0
*** End Patch
EOF
