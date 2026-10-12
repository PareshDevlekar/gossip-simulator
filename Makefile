.PHONY: test benchmark report package
PYTHON ?= python3

test:
	./tests/simulator_tests.escript
	@./project2 0 full gossip >/dev/null 2>&1; test $$? -eq 1
	@./project2 4 invalid gossip >/dev/null 2>&1; test $$? -eq 1

benchmark:
	$(PYTHON) scripts/benchmark.py

report:
	$(PYTHON) scripts/report.py

package:
	$(PYTHON) scripts/package.py
