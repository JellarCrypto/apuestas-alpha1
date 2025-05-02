def calcular_probabilidades_desde_cuotas(c_l, c_e, c_v):
    p1, p2, p3 = 1/c_l, 1/c_e, 1/c_v
    s = p1 + p2 + p3
    return p1/s, p2/s, p3/s
