.section .data
    format_int: .asciz "%d\n"
    format_float: .asciz "%.2f\n"
    format_string: .asciz "%s\n"
    input_int: .asciz "%d"
    input_float: .asciz "%f"
    input_string: .asciz "%s"

.section .bss
    .lcomm buffer, 256

.section .text
    .global _start

main:
    push %rbp                      ; guardar base pointer
    mov %rsp, %rbp                 ; establecer nuevo base pointer

    mov $0, %eax                   ; valor de retorno por defecto
    mov %rbp, %rsp                 ; restaurar stack pointer
    pop %rbp                       ; restaurar base pointer
    ret                            ; retornar
    

_start:
    call main
    mov %eax, %edi
    mov $60, %eax
    syscall
