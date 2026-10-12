.PHONY: test benchmark report package
PYTHON ?= python3

test:
	./tests/failure_tests.escript
	@./project2-bonus 4 full gossip -0.1 >/dev/null 2>&1; test $$? -eq 1
	@./project2-bonus 4 full gossip 1.1 >/dev/null 2>&1; test $$? -eq 1

benchmark:
	$(PYTHON) scripts/benchmark.py

report:
	$(PYTHON) scripts/report.py

package:
	$(PYTHON) scripts/package.py
