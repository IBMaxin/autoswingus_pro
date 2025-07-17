apply_patch <<'EOF'
*** Begin Patch
*** Update File: autoswing/backtest/backtester.py
@@
-from autoswing.engine.portfolio import Portfolio, Position
-
-
-def run_backtest(data_bundle: Dict[str, pd.DataFrame], strategy, starting_cash: float = 1000.0):
-    pf = Portfolio(cash=starting_cash)
-    # strategy.scan called once at end-of-data for Phase 1 demo
-    signals = strategy.scan(data_bundle)
-    for sig in signals:
-        if sig.action != "buy":
-            continue
-        df = data_bundle[sig.symbol]
-        price = df.close.iloc[-1]
-        size = strategy.position_size(pf, sig)
-        cost = size * price
-        if cost <= pf.cash:
-            pf.cash -= cost
-            pf.positions[sig.symbol] = Position(sig.symbol, size, price)
-    return pf
+from autoswing.engine.paper_executor import run_bar_backtest
+
+def run_backtest(data_bundle: Dict[str, pd.DataFrame], strategy, starting_cash: float = 1000.0, project_root=None):
+    """Phase 3A realistic paper backtest on daily bars."""
+    final_eq, trades, acct = run_bar_backtest(
+        bundle=data_bundle,
+        strategy=strategy,
+        starting_cash=starting_cash,
+        max_hold_days=getattr(strategy, "max_hold_days", None),
+        fee_per_share=0.0,
+        project_root=project_root,
+    )
+    # return something Portfolio-like shim for compatibility
+    class _Shim:
+        def equity(self_inner): return float(final_eq)
+    return _Shim()
*** End Patch
EOF
