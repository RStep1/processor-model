# processor-model

- Рыков Степан Олегович | P3230
- asm | risc | neum | hw | instr | struct | stream | mem | cstr | prob2
- С упрощением

## Язык программирования - Assembly

Синтаксис в расширенной БНФ.

- [ ... ] -- вхождение 0 или 1 раз
- { ... } -- повторение 0 или несколько раз
- { ... }- -- повторение 1 или несколько раз

'''
program ::= { line }

line ::= label [ comment ] "\n"
       | instr [ comment ] "\n"
       | [ comment ] "\n"

label ::= label_name ":"

instr ::= op0
        | op1 register, (register, address | integer | char)
        | op2 register, register, rigister
        | op3 label_name
        | op4 register
        | op5 register, register

op0 ::= "halt"
      | "ret"

op1 ::= "store"
      | "ld"
      | "li"

op2 ::= "add"
      | "sub"
      | "mul"
      | "div"
      | "mod"

op3 ::= "jmp"
      | "jnz"
      | "jz"
      | "call"

op4 ::= "inc"
      | "dec"
      | "asl"
      | "push"
      | "pop"
      | "in"
      | "out"

op5 ::= "cmp"
      | "mov"

register ::= "r" {<any of "0-9">}-

integer ::= "#" [ "-" ] { <any of "0-9"> }-

char ::= '<"a-z A-z">'

address ::= <any of *> { <any of "0-9"> }

arg ::= <any of "0-9">

label_name ::= <any of "a-z A-Z_"> { <any of "a-z A-Z 0-9 _"> }

comment ::= ";" <any symbols except "\n">
'''

**Операции:**
Арифметические опрерации:
`add` - сложить значения двух регистров и записать результат в первый
`sub` - вычесть значения двух регистров и записать результат в первый
`mul`
`div`
`mod`
`inc`
`dec`

Операции с памятью:
`load`
`store`

Инструкции перехода:
`jmp`
`jz`

`halt` - останов

**Метки**
Метки для переходов определяются на отдельных строчках:

```asm
label:
    inc
```

И в другом месте (неважно, до или после определения) сослаться на эту метку:

```asm
jmp label   ; --> `jmp 123`, где 123 - номер инструкции после объявления метки
```

На этапе трансляции вместо метки ставится адрес команды, идущей на следующей строке после метки.
В программе не может быть дублирующихся меток, определенных в разных местах с одним именем.

## Организация памяти

## Система команд

### Кодирование инструкций

- Машинный код сериализуется в список JSON;
- Один элемент списка - одна инструкция;
- Индекс списка - адрес инструкции. Используется для команд перехода.

```JSON
[
      {
            "index": "cmd_addr",
            "opcode": "command",
            "args": [
                  "reg", "reg", "reg", "addr | int | char", "arg"
            ]
      }
]
```

## Транслятор

## Тестирование
