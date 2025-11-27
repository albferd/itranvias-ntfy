# encoding = utf-8

import re


#def mbox(text='', title=''):
"""Esto lo que hace es crear una caja con bordes redondeados:
(necesita soporte unicode);(m)essage(r)ounded(box)
Lo hace creando los bordes y incluyendo el caracter "-", el nº de letras `+ 2 (para hacer un margen) veces
después pone el texto entre barras verticales
y finalmente hace lo mismo que el de arriba pero con los bordes inversos
"""
#    text = str(text)
#    if title == '':
#        print(f'╭{\'─\' * (len(text) + 2)}╮')
#    else:
#        print(f'╭{\'─ \' + str(title) + \' \' + \'─\' * (len(text) - 1 - len(str(title)))}╮')
#    print(f'│ {text} │')
#    print(f'╰{\'─\' * (len(text) + 2)}╯')


def drawtable(table, hpad=1, hlines=True):
    """Dibuja una tabla:
    table = un array 2D al que NO le faltan elementos
    hpad = espacios para añadir a cada lateral de los elementos
    hlines = si se desean líneas horizontales"""
    maxes = []
    # calculate margins
    for i in range(len(table[0])):  # Esto es muy mala idea; leer solo la primera fila 😐
        max_len = 0
        for row in table:
            max_len = max(len(re.sub(r'(\x9b|\x1b\[)[0-?]*[ -/]*[@-~]', '', str(row[i]))), max_len)
        maxes.append(max_len)
    # printl('╭')
    # (f)irst (l)ine
    fl = '╭'
    for i in range(len(maxes)):  # Si hay algo más en la tabla, poner una T en vez de una esquina
        fl += '─' * (maxes[i] + hpad * 2)
        if i < len(maxes) - 1:
            fl += '┬'
        else:
            fl += '╮'
    print(fl)
    # (h)orizontal (g)rid (l)ines
    hgl = fl.replace('╭', '├').replace('┬', '┼').replace('╮', '┤')
    for i in range(len(table)):
        line = '│'
        for j in range(len(table[i])):
            line += (hpad * ' ' + str(table[i][j]) + ' ' * max(0, maxes[j]
                                                               - len(
                re.sub(r'(\x9b|\x1b\[)[0-?]*[ -\/]*[@-~]', '', str(table[i][j]))))
                     # remove unprintable characters so they don't throw len() off
                     + hpad * ' ')  # añadir espacios correspondientes para que cuadre bien

            if j < len(table) - 2:
                line += '│'
            else:
                line += '│'
        print(line)
        if hlines:  # opc de poner lineas entre filas
            if i < len(table) - 1:
                print(hgl)

    ll = fl.replace('╭', '╰').replace('┬', '┴').replace('╮', '╯')
    print(ll)


def promptnumber(prompt='$> ', emsg='Introduce un número'):
    """
    Pide un número y garantiza que devuelva un número
    """
    while True:
        try:
            n = int(input(prompt))
            break
        except ValueError:
            print(emsg)
    return n
