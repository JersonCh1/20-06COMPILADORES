# Makefile para compilar codigo assembly generado

CC = gcc
CFLAGS = -no-pie -g
ASM_DIR = salida-assembly
BIN_DIR = ejecutables

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

compile: $(BIN_DIR)
	$(CC) $(CFLAGS) -o $(BIN_DIR)/$(basename $(FILE)) $(ASM_DIR)/$(FILE)
	@echo "Compilado: $(BIN_DIR)/$(basename $(FILE))"

run: compile
	@echo "Ejecutando $(basename $(FILE))..."
	./$(BIN_DIR)/$(basename $(FILE))

clean:
	rm -rf $(BIN_DIR)
	@echo "Archivos ejecutables eliminados"

help:
	@echo "Comandos disponibles:"
	@echo "  make compile FILE=archivo.s  - Compilar archivo especifico"
	@echo "  make run FILE=archivo.s      - Compilar y ejecutar archivo"
	@echo "  make clean                   - Limpiar ejecutables"

.PHONY: compile run clean help
