"""
Parcial V - Programación Dinámica (UJAP)
Pregunta 1c: Ruta más corta de la Oficina anterior (1) a la Oficina nueva (13)
usando Floyd-Warshall y Bellman-Ford.
"""

INF = float("inf")
N = 13
ORIGEN, DESTINO = 1, 13

# Aristas del grafo (no dirigido): (u, v, distancia)
ARISTAS = [
    (1, 2, 100), (1, 3, 50), (1, 4, 40), (3, 4, 20),
    (2, 5, 100), (3, 5, 100), (4, 6, 100), (5, 6, 40),
    (5, 7, 120), (5, 8, 130), (6, 9, 100), (7, 8, 50),
    (7, 10, 60), (8, 10, 70), (8, 9, 100), (9, 11, 100),
    (10, 13, 100), (10, 12, 200), (11, 12, 50), (12, 13, 100),
]


def floyd_warshall(n, aristas):
    # dist[i][j] y sig[i][j] (siguiente nodo en la ruta i -> j), índices 1..n
    dist = [[INF] * (n + 1) for _ in range(n + 1)]
    sig = [[None] * (n + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dist[i][i] = 0
        sig[i][i] = i
    for u, v, w in aristas:
        dist[u][v] = dist[v][u] = w
        sig[u][v], sig[v][u] = v, u

    # Recurrencia DP: d_k(i,j) = min(d_{k-1}(i,j), d_{k-1}(i,k) + d_{k-1}(k,j))
    for k in range(1, n + 1):
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    sig[i][j] = sig[i][k]
    return dist, sig


def ruta_fw(sig, i, j):
    if sig[i][j] is None:
        return []
    ruta = [i]
    while i != j:
        i = sig[i][j]
        ruta.append(i)
    return ruta


def bellman_ford(n, aristas, origen):
    # Grafo no dirigido: cada arista se relaja en ambos sentidos
    arcos = [(u, v, w) for u, v, w in aristas] + [(v, u, w) for u, v, w in aristas]
    dist = [INF] * (n + 1)
    pred = [None] * (n + 1)
    dist[origen] = 0

    iteraciones = 0
    for _ in range(n - 1):
        iteraciones += 1
        cambio = False
        for u, v, w in arcos:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                pred[v] = u
                cambio = True
        if not cambio:          # ya convergió
            break

    # Verificación de ciclos negativos
    ciclo_negativo = any(dist[u] + w < dist[v] for u, v, w in arcos)
    return dist, pred, iteraciones, ciclo_negativo


def ruta_bf(pred, destino):
    ruta = []
    while destino is not None:
        ruta.append(destino)
        destino = pred[destino]
    return ruta[::-1]


def fmt(x):
    return "INF" if x == INF else str(int(x))


if __name__ == "__main__":
    print("=" * 70)
    print("FLOYD-WARSHALL")
    print("=" * 70)
    dist, sig = floyd_warshall(N, ARISTAS)
    print("Matriz de distancias mínimas entre todos los pares:")
    print("     " + "".join(f"{j:>5}" for j in range(1, N + 1)))
    for i in range(1, N + 1):
        print(f"{i:>4} " + "".join(f"{fmt(dist[i][j]):>5}" for j in range(1, N + 1)))
    r = ruta_fw(sig, ORIGEN, DESTINO)
    print(f"\nRuta más corta {ORIGEN} -> {DESTINO}: {' -> '.join(map(str, r))}")
    print(f"Distancia total: {fmt(dist[ORIGEN][DESTINO])}")

    print("\n" + "=" * 70)
    print("BELLMAN-FORD (origen = nodo 1)")
    print("=" * 70)
    d, pred, it, neg = bellman_ford(N, ARISTAS, ORIGEN)
    print(f"Convergió en {it} iteraciones (máximo n-1 = {N - 1})")
    print(f"¿Ciclo negativo?: {'Sí' if neg else 'No'}\n")
    print(f"{'Nodo':>5} {'Distancia':>10} {'Predecesor':>11}   Ruta")
    for v in range(1, N + 1):
        print(f"{v:>5} {fmt(d[v]):>10} {str(pred[v] or '-'):>11}   "
              f"{' -> '.join(map(str, ruta_bf(pred, v)))}")
    r2 = ruta_bf(pred, DESTINO)
    print(f"\nRuta más corta {ORIGEN} -> {DESTINO}: {' -> '.join(map(str, r2))}")
    print(f"Distancia total: {fmt(d[DESTINO])}")

    print("\nAmbos algoritmos coinciden:", dist[ORIGEN][DESTINO] == d[DESTINO] and r == r2)
