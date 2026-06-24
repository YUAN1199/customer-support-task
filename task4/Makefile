.PHONY: eval demo replay test clean help install judge-sanity

# Agentic Reasoning Lab Makefile
# Usage: make eval, make demo, make replay TRACE_ID=<id>, etc.

install:
	pip install -r requirements.txt

eval:
	python main.py $(ARGS)

demo:
	python main.py --demo

judge-sanity:
	python main.py --judge-sanity

record-baseline:
	python main.py --record-baseline $(ARGS)

delta:
	python main.py --delta $(ARGS)

replay:
	python -m observability.replay --trace-id $(TRACE_ID) $(REPLAY_ARGS)

cost:
	python -m observability.analysis

clean:
	rm -rf data/traces/*.jsonl
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	echo "Cleaned traces and caches"

test:
	python -c "from eval.metrics import exact_match; print('Metrics OK')"
	python -c "from tools.calculator import calculator; print('Tools OK')"
	python -c "from config import CONFIG; print(f'Config OK: solver_model={CONFIG.solver_model}')"
	python -c "from strategies.react_strategy import ReActStrategy; from strategies.plan_execute_strategy import PlanExecuteStrategy; from strategies.self_consistency_strategy import SelfConsistencyStrategy; from strategies.tot_strategy import ToTStrategy; print('All strategies importable')"

help:
	@echo "Agentic Reasoning Lab Commands:"
	@echo "  make install          Install dependencies"
	@echo "  make eval             Run full evaluation on all strategies"
	@echo "  make eval ARGS=--problems=5   Run on first 5 problems"
	@echo "  make demo             Run one example with all strategies"
	@echo "  make judge-sanity     Run LLM judge sanity check"
	@echo "  make record-baseline  Record current results as baseline"
	@echo "  make delta            Show delta vs saved baseline"
	@echo "  make replay TRACE_ID=<id>  Replay a single problem from trace"
	@echo "  make cost             Show cost/latency analysis"
	@echo "  make test             Quick import/sanity test"
	@echo "  make clean            Clean traces and caches"