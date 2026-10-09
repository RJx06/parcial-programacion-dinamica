"""
Parcial V - Programación Dinámica (UJAP)
Pregunta 2: Problema de Volumen de Carga (mochila) resuelto por etapas.

Etapa i = producto i, estado x = capacidad (kg) disponible para los productos i..n
Recursión hacia atrás:
    f_i(x) = max { r_i * m_i + f_{i+1}(x - w_i * m_i) },  m_i = 0..min(max_unidades, x // w_i)
    f_{n+1}(x) = 0
"""

CAPACIDAD = 10
PRODUCTOS = [  # (nombre, peso kg, precio $)
    ("Tablet Samsung", 2, 40),
    ("Dron DJI Mini", 3, 50),
    ("Proyector portatil", 4, 65),
    ("Laptop ASUS ZenBook", 5, 60),
]


def volumen_carga(productos, W, max_unidades=1):
    n = len(productos)
    f = [[0] * (W + 1) for _ in range(n + 2)]     # f[n+1][x] = 0
    dec = [[0] * (W + 1) for _ in range(n + 1)]   # m_i óptimo para cada estado

    tablas = []
    for i in range(n, 0, -1):
        nombre, w, r = productos[i - 1]
        filas = []
        for x in range(W + 1):
            limite = min(max_unidades, x // w)
            valores = {m: r * m + f[i + 1][x - w * m] for m in range(limite + 1)}
            m_opt = max(valores, key=lambda m: valores[m])
            f[i][x], dec[i][x] = valores[m_opt], m_opt
            filas.append((x, valores, f[i][x], m_opt))
        tablas.append((i, nombre, w, r, filas))

    # Reconstrucción hacia adelante
    x, plan = W, []
    for i in range(1, n + 1):
        m = dec[i][x]
        plan.append(m)
        x -= productos[i - 1][1] * m
    return f[1][W], plan, tablas


def imprimir(titulo, productos, W, max_unidades):
    print("=" * 70)
    print(titulo)
    print("=" * 70)
    valor, plan, tablas = volumen_carga(productos, W, max_unidades)
    maxm = max_unidades
    for i, nombre, w, r, filas in tablas:
        print(f"\nEtapa {i}: {nombre} (w={w} kg, r=${r})")
        cols = list(range(0, min(maxm, W // w) + 1))
        print(f"{'x':>3} | " + "".join(f"{'m=' + str(m):>7}" for m in cols) + f" | {'f(x)':>5} {'m*':>3}")
        for x, valores, fx, m_opt in filas:
            celdas = "".join(f"{(str(valores[m]) if m in valores else '-'):>7}" for m in cols)
            print(f"{x:>3} | {celdas} | {fx:>5} {m_opt:>3}")

    print("\nSOLUCION OPTIMA")
    peso = 0
    for (nombre, w, r), m in zip(productos, plan):
        if m:
            print(f"  Llevar {m} x {nombre:<20} {w * m:>3} kg   ${r * m}")
            peso += w * m
    print(f"  Peso usado: {peso} kg de {W} kg (libre: {W - peso} kg)")
    print(f"  Valor total maximo: ${valor}\n")


if __name__ == "__main__":
    imprimir("VOLUMEN DE CARGA 0/1 (una unidad de cada producto)", PRODUCTOS, CAPACIDAD, 1)
    imprimir("VARIANTE: unidades ilimitadas por producto", PRODUCTOS, CAPACIDAD, CAPACIDAD)
