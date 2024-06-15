ALGO_DIR = ./algorithms
CODE_DIR = ./codes
INPUT_DIR = ./input_files

TRANSLATOR = python ./translator.py
MACHINE = python ./machine.py

INPUT_EMPTY = $(INPUT_DIR)/empty_input
INPUT_CAT = $(INPUT_DIR)/cat_input
INPUT_HELLO_USERNAME = $(INPUT_DIR)/hello_username_input

ASM_FILES = cat.asm hello_username.asm hello.asm prob2.asm alg.asm
JSON_FILES = $(patsubst %.asm,$(CODE_DIR)/%_code.json,$(ASM_FILES))

ASM_CAT = $(ALGO_DIR)/cat.asm
ASM_HELLO_USERNAME = $(ALGO_DIR)/hello_username.asm
ASM_HELLO = $(ALGO_DIR)/hello.asm
ASM_PROB2 = $(ALGO_DIR)/prob2.asm
ASM_ALG = $(ALGO_DIR)/alg.asm

JSON_CAT = $(CODE_DIR)/cat_code.json
JSON_HELLO_USERNAME = $(CODE_DIR)/hello_username_code.json
JSON_HELLO = $(CODE_DIR)/hello_code.json
JSON_PROB2 = $(CODE_DIR)/prob2_code.json
JSON_ALG = $(CODE_DIR)/alg_code.json

# translate and run:

translate_all: translate_cat translate_hello_username translate_hello translate_prob2 translate_alg

run_all: run_cat run_hello_username run_hello run_prob2 run_alg

translate_cat:
	$(TRANSLATOR) $(ASM_CAT) $(JSON_CAT)

translate_hello_username:
	$(TRANSLATOR) $(ASM_HELLO_USERNAME) $(JSON_HELLO_USERNAME)

translate_hello:
	$(TRANSLATOR) $(ASM_HELLO) $(JSON_HELLO)

translate_prob2:
	$(TRANSLATOR) $(ASM_PROB2) $(JSON_PROB2)

translate_alg:
	$(TRANSLATOR) $(ASM_ALG) $(JSON_ALG)

run_cat:
	$(MACHINE) $(JSON_CAT) $(INPUT_CAT)

run_hello_username:
	$(MACHINE) $(JSON_HELLO_USERNAME) $(INPUT_HELLO_USERNAME)

run_hello:
	$(MACHINE) $(JSON_HELLO) $(INPUT_EMPTY)

run_prob2:
	$(MACHINE) $(JSON_PROB2) $(INPUT_EMPTY)

run_alg:
	$(MACHINE) $(JSON_ALG) $(INPUT_EMPTY)

clean:
	rm -f $(JSON_FILES)


# poetry:

format:
	poetry run ruff format .

lint:
	poetry run ruff check .

test:
	poetry run pytest -v

test-update-golden:
	poetry run pytest . -v --update-goldens


.PHONY: translate_all run_all translate_cat translate_hello_username \
		translate_hello translate_prob2 translate_alg run_cat \
		run_hello_username run_hello run_prob2 run_alg clean
