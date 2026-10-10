"""
Parcial V - Programación Dinámica (UJAP)
Interfaz gráfica (Tkinter) para los dos problemas:
  - Pregunta 1c: Ruta más corta (Floyd-Warshall y Bellman-Ford)  -> rutas.py
  - Pregunta 2:  Volumen de carga por etapas                       -> volumen_carga.py

Ejecutar:  python interfaz.py
"""

import math
import tkinter as tk
from tkinter import ttk, messagebox

import rutas
import volumen_carga as vc

# Posiciones (0..1) de los nodos del grafo original, ordenados por etapas
POSICIONES = {
    1: (0.05, 0.50), 2: (0.20, 0.15), 3: (0.20, 0.50), 4: (0.20, 0.85),
    5: (0.38, 0.30), 6: (0.38, 0.75), 7: (0.56, 0.12), 8: (0.56, 0.45),
    9: (0.56, 0.85), 10: (0.75, 0.25), 11: (0.75, 0.85), 12: (0.88, 0.60),
    13: (0.95, 0.20),
}

COLOR_NODO = "#dfe9f5"
COLOR_RUTA = "#d9480f"
FUENTE_MONO = ("Consolas", 10)


def tabla(padre, columnas, anchos, alto=10):
    """Treeview con scroll vertical y horizontal."""
    marco = ttk.Frame(padre)
    tv = ttk.Treeview(marco, columns=columnas, show="headings", height=alto)
    for c, a in zip(columnas, anchos):
        tv.heading(c, text=c)
        tv.column(c, width=a, anchor="center", stretch=False)
    sy = ttk.Scrollbar(marco, orient="vertical", command=tv.yview)
    sx = ttk.Scrollbar(marco, orient="horizontal", command=tv.xview)
    tv.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
    tv.grid(row=0, column=0, sticky="nsew")
    sy.grid(row=0, column=1, sticky="ns")
    sx.grid(row=1, column=0, sticky="ew")
    marco.rowconfigure(0, weight=1)
    marco.columnconfigure(0, weight=1)
    return marco, tv


def entero(texto, nombre, minimo=None):
    try:
        v = int(texto)
    except ValueError:
        raise ValueError(f"'{nombre}' debe ser un número entero.")
    if minimo is not None and v < minimo:
        raise ValueError(f"'{nombre}' debe ser mayor o igual a {minimo}.")
    return v


# ---------------------------------------------------------------------------
# Pestaña 1: Ruta más corta
# ---------------------------------------------------------------------------
class PestanaRutas(ttk.Frame):
    def __init__(self, padre):
        super().__init__(padre, padding=8)
        self.ruta = []
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._panel_datos()
        self._panel_resultados()
        self.restaurar()

    # --- Construcción -----------------------------------------------------
    def _panel_datos(self):
        izq = ttk.LabelFrame(self, text="Datos del grafo (no dirigido)", padding=8)
        izq.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        izq.rowconfigure(0, weight=1)

        marco, self.tv_aristas = tabla(izq, ("Desde", "Hasta", "Distancia"), (70, 70, 80), 14)
        marco.grid(row=0, column=0, columnspan=4, sticky="nsew")
        self.tv_aristas.bind("<<TreeviewSelect>>", self._cargar_seleccion)

        self.e_u, self.e_v, self.e_w = tk.StringVar(), tk.StringVar(), tk.StringVar()
        for col, (txt, var) in enumerate((("Desde", self.e_u), ("Hasta", self.e_v), ("Dist.", self.e_w))):
            ttk.Label(izq, text=txt).grid(row=1, column=col, pady=(8, 0))
            ttk.Entry(izq, textvariable=var, width=8, justify="center").grid(row=2, column=col, padx=2)

        botones = ttk.Frame(izq)
        botones.grid(row=3, column=0, columnspan=4, pady=6, sticky="ew")
        ttk.Button(botones, text="Agregar / actualizar", command=self.agregar).pack(side="left", expand=True, fill="x")
        ttk.Button(botones, text="Eliminar", command=self.eliminar).pack(side="left", expand=True, fill="x")

        od = ttk.Frame(izq)
        od.grid(row=4, column=0, columnspan=4, pady=(6, 0), sticky="ew")
        self.origen, self.destino = tk.StringVar(), tk.StringVar()
        ttk.Label(od, text="Origen").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(od, from_=1, to=999, textvariable=self.origen, width=6).grid(row=0, column=1, padx=4)
        ttk.Label(od, text="Destino").grid(row=0, column=2, sticky="w", padx=(8, 0))
        ttk.Spinbox(od, from_=1, to=999, textvariable=self.destino, width=6).grid(row=0, column=3, padx=4)

        ttk.Button(izq, text="Calcular ruta más corta", style="Accion.TButton",
                   command=self.calcular).grid(row=5, column=0, columnspan=4, sticky="ew", pady=(10, 2))
        ttk.Button(izq, text="Restaurar datos del parcial",
                   command=self.restaurar).grid(row=6, column=0, columnspan=4, sticky="ew")

    def _panel_resultados(self):
        der = ttk.Frame(self)
        der.grid(row=0, column=1, sticky="nsew")
        der.columnconfigure(0, weight=1)
        der.rowconfigure(0, weight=1)
        der.rowconfigure(2, weight=1)

        self.canvas = tk.Canvas(der, background="white", highlightthickness=1,
                                highlightbackground="#c8c8c8", height=300)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda e: self.dibujar())

        self.resumen = ttk.Label(der, text="", style="Resumen.TLabel", wraplength=700, justify="left")
        self.resumen.grid(row=1, column=0, sticky="ew", pady=6)

        nb = ttk.Notebook(der)
        nb.grid(row=2, column=0, sticky="nsew")
        self.f_fw = ttk.Frame(nb, padding=4)
        self.f_bf = ttk.Frame(nb, padding=4)
        nb.add(self.f_fw, text="Floyd-Warshall (matriz de distancias)")
        nb.add(self.f_bf, text="Bellman-Ford (desde el origen)")
        for f in (self.f_fw, self.f_bf):
            f.rowconfigure(0, weight=1)
            f.columnconfigure(0, weight=1)

        marco, self.tv_bf = tabla(self.f_bf, ("Nodo", "Distancia", "Predecesor", "Ruta"), (60, 90, 90, 360), 8)
        self.tv_bf.column("Ruta", anchor="w")
        marco.grid(row=0, column=0, sticky="nsew")
        self.tv_fw = None

    # --- Datos ------------------------------------------------------------
    def aristas(self):
        return [tuple(int(x) for x in self.tv_aristas.item(i, "values")) for i in self.tv_aristas.get_children()]

    def _poner_aristas(self, aristas):
        self.tv_aristas.delete(*self.tv_aristas.get_children())
        for u, v, w in sorted(aristas):
            self.tv_aristas.insert("", "end", values=(u, v, w))

    def _cargar_seleccion(self, _evento):
        sel = self.tv_aristas.selection()
        if sel:
            u, v, w = self.tv_aristas.item(sel[0], "values")
            self.e_u.set(u), self.e_v.set(v), self.e_w.set(w)

    def agregar(self):
        try:
            u = entero(self.e_u.get(), "Desde", 1)
            v = entero(self.e_v.get(), "Hasta", 1)
            w = entero(self.e_w.get(), "Distancia")
            if u == v:
                raise ValueError("Una arista debe unir dos nodos distintos.")
        except ValueError as e:
            messagebox.showerror("Dato inválido", str(e))
            return
        resto = [a for a in self.aristas() if {a[0], a[1]} != {u, v}]
        self._poner_aristas(resto + [(min(u, v), max(u, v), w)])
        self.calcular()

    def eliminar(self):
        sel = self.tv_aristas.selection()
        if not sel:
            messagebox.showinfo("Eliminar", "Seleccione una arista de la tabla.")
            return
        for i in sel:
            self.tv_aristas.delete(i)
        self.calcular()

    def restaurar(self):
        self._poner_aristas(rutas.ARISTAS)
        self.origen.set(rutas.ORIGEN)
        self.destino.set(rutas.DESTINO)
        self.calcular()

    # --- Cálculo ----------------------------------------------------------
    def calcular(self):
        aristas = self.aristas()
        if not aristas:
            messagebox.showerror("Sin datos", "Agregue al menos una arista.")
            return
        n = max(max(u, v) for u, v, _ in aristas)
        try:
            o = entero(self.origen.get(), "Origen", 1)
            d = entero(self.destino.get(), "Destino", 1)
            if o > n or d > n:
                raise ValueError(f"Origen y destino deben estar entre 1 y {n}.")
        except ValueError as e:
            messagebox.showerror("Dato inválido", str(e))
            return

        dist, sig = rutas.floyd_warshall(n, aristas)
        d_bf, pred, it, neg = rutas.bellman_ford(n, aristas, o)
        r_fw = rutas.ruta_fw(sig, o, d)
        r_bf = rutas.ruta_bf(pred, d) if d_bf[d] != rutas.INF else []

        self._mostrar_fw(n, dist, r_fw)
        self.tv_bf.delete(*self.tv_bf.get_children())
        for v in range(1, n + 1):
            camino = rutas.ruta_bf(pred, v) if d_bf[v] != rutas.INF else []
            tags = ("ruta",) if v in r_bf else ()
            self.tv_bf.insert("", "end", tags=tags, values=(
                v, rutas.fmt(d_bf[v]), pred[v] or "-", " → ".join(map(str, camino)) or "sin ruta"))
        self.tv_bf.tag_configure("ruta", foreground=COLOR_RUTA)

        if not r_fw:
            texto = f"No existe ruta de {o} a {d}."
        else:
            coinciden = dist[o][d] == d_bf[d] and r_fw == r_bf
            texto = (f"Ruta más corta {o} → {d}:  {' → '.join(map(str, r_fw))}     "
                     f"Distancia total: {rutas.fmt(dist[o][d])}\n"
                     f"Bellman-Ford convergió en {it} iteraciones (máx. n-1 = {n - 1}) · "
                     f"Ciclo negativo: {'Sí' if neg else 'No'} · "
                     f"Ambos algoritmos coinciden: {'Sí' if coinciden else 'No'}")
        self.resumen.configure(text=texto)
        self.ruta = r_fw
        self.dibujar()

    def _mostrar_fw(self, n, dist, ruta):
        if self.tv_fw is not None:
            self.tv_fw.master.destroy()
        cols = ["i \\ j"] + [str(j) for j in range(1, n + 1)]
        marco, self.tv_fw = tabla(self.f_fw, cols, [55] + [48] * n, 8)
        marco.grid(row=0, column=0, sticky="nsew")
        for i in range(1, n + 1):
            tags = ("ruta",) if i in ruta else ()
            self.tv_fw.insert("", "end", tags=tags,
                              values=[i] + [rutas.fmt(dist[i][j]) for j in range(1, n + 1)])
        self.tv_fw.tag_configure("ruta", foreground=COLOR_RUTA)

    # --- Dibujo del grafo -------------------------------------------------
    def dibujar(self):
        c = self.canvas
        c.delete("all")
        aristas = self.aristas()
        if not aristas:
            return
        W, H = c.winfo_width(), c.winfo_height()
        mx, my, rad = 30, 25, 15
        nodos = sorted({x for u, v, _ in aristas for x in (u, v)})
        usar_fijas = all(x in POSICIONES for x in nodos)

        def pos(k):
            if usar_fijas:
                px, py = POSICIONES[k]
            else:  # disposición circular para grafos editados
                ang = 2 * math.pi * nodos.index(k) / len(nodos) - math.pi / 2
                px, py = 0.5 + 0.45 * math.cos(ang), 0.5 + 0.45 * math.sin(ang)
            return mx + px * (W - 2 * mx), my + py * (H - 2 * my)

        en_ruta = {frozenset(p) for p in zip(self.ruta, self.ruta[1:])}
        for u, v, w in aristas:
            (x1, y1), (x2, y2) = pos(u), pos(v)
            marcada = frozenset((u, v)) in en_ruta
            c.create_line(x1, y1, x2, y2, width=4 if marcada else 1.5,
                          fill=COLOR_RUTA if marcada else "#8a8a8a")
            xm, ym = (x1 + x2) / 2, (y1 + y2) / 2
            c.create_rectangle(xm - 15, ym - 8, xm + 15, ym + 8, fill="white", outline="")
            c.create_text(xm, ym, text=str(w), font=("Segoe UI", 8, "bold" if marcada else "normal"),
                          fill=COLOR_RUTA if marcada else "#444")
        for k in nodos:
            x, y = pos(k)
            marcado = k in self.ruta
            c.create_oval(x - rad, y - rad, x + rad, y + rad,
                          fill=COLOR_RUTA if marcado else COLOR_NODO,
                          outline="#333" if not marcado else COLOR_RUTA, width=1.5)
            c.create_text(x, y, text=str(k), font=("Segoe UI", 9, "bold"),
                          fill="white" if marcado else "#222")


# ---------------------------------------------------------------------------
# Pestaña 2: Volumen de carga
# ---------------------------------------------------------------------------
class PestanaCarga(ttk.Frame):
    def __init__(self, padre):
        super().__init__(padre, padding=8)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._panel_datos()
        self._panel_resultados()
        self.restaurar()

    def _panel_datos(self):
        izq = ttk.LabelFrame(self, text="Productos", padding=8)
        izq.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        izq.rowconfigure(0, weight=1)

        marco, self.tv_prod = tabla(izq, ("Producto", "Peso (kg)", "Precio ($)"), (170, 75, 75), 10)
        marco.grid(row=0, column=0, columnspan=3, sticky="nsew")
        self.tv_prod.column("Producto", anchor="w")
        self.tv_prod.bind("<<TreeviewSelect>>", self._cargar_seleccion)

        self.e_nom, self.e_peso, self.e_precio = tk.StringVar(), tk.StringVar(), tk.StringVar()
        ttk.Label(izq, text="Nombre").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Label(izq, text="Peso").grid(row=1, column=1, pady=(8, 0))
        ttk.Label(izq, text="Precio").grid(row=1, column=2, pady=(8, 0))
        ttk.Entry(izq, textvariable=self.e_nom, width=22).grid(row=2, column=0, sticky="ew")
        ttk.Entry(izq, textvariable=self.e_peso, width=7, justify="center").grid(row=2, column=1, padx=2)
        ttk.Entry(izq, textvariable=self.e_precio, width=7, justify="center").grid(row=2, column=2, padx=2)

        botones = ttk.Frame(izq)
        botones.grid(row=3, column=0, columnspan=3, pady=6, sticky="ew")
        ttk.Button(botones, text="Agregar / actualizar", command=self.agregar).pack(side="left", expand=True, fill="x")
        ttk.Button(botones, text="Eliminar", command=self.eliminar).pack(side="left", expand=True, fill="x")
        ttk.Button(botones, text="↑", width=3, command=lambda: self.mover(-1)).pack(side="left")
        ttk.Button(botones, text="↓", width=3, command=lambda: self.mover(1)).pack(side="left")

        par = ttk.LabelFrame(izq, text="Parámetros", padding=6)
        par.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        self.capacidad = tk.StringVar()
        ttk.Label(par, text="Capacidad (kg)").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(par, from_=1, to=1000, textvariable=self.capacidad, width=7).grid(row=0, column=1, sticky="w", padx=4)

        self.modo = tk.StringVar(value="01")
        self.max_u = tk.StringVar(value="2")
        ttk.Radiobutton(par, text="0/1 (una unidad de cada producto)", value="01",
                        variable=self.modo).grid(row=1, column=0, columnspan=3, sticky="w", pady=(6, 0))
        ttk.Radiobutton(par, text="Unidades ilimitadas", value="ilim",
                        variable=self.modo).grid(row=2, column=0, columnspan=3, sticky="w")
        ttk.Radiobutton(par, text="Máximo de unidades:", value="max",
                        variable=self.modo).grid(row=3, column=0, sticky="w")
        ttk.Spinbox(par, from_=1, to=100, textvariable=self.max_u, width=5).grid(row=3, column=1, sticky="w", padx=4)

        ttk.Button(izq, text="Resolver", style="Accion.TButton",
                   command=self.calcular).grid(row=5, column=0, columnspan=3, sticky="ew", pady=(10, 2))
        ttk.Button(izq, text="Restaurar datos del parcial",
                   command=self.restaurar).grid(row=6, column=0, columnspan=3, sticky="ew")

    def _panel_resultados(self):
        der = ttk.Frame(self)
        der.grid(row=0, column=1, sticky="nsew")
        der.columnconfigure(0, weight=1)
        der.rowconfigure(1, weight=1)

        sol = ttk.LabelFrame(der, text="Solución óptima", padding=8)
        sol.grid(row=0, column=0, sticky="ew")
        sol.columnconfigure(0, weight=1)
        marco, self.tv_sol = tabla(sol, ("Producto", "Unidades", "Peso (kg)", "Valor ($)"), (220, 80, 90, 90), 5)
        self.tv_sol.column("Producto", anchor="w")
        marco.grid(row=0, column=0, sticky="ew")
        self.resumen = ttk.Label(sol, text="", style="Resumen.TLabel")
        self.resumen.grid(row=1, column=0, sticky="w", pady=(6, 0))

        tab = ttk.LabelFrame(der, text="Tablas por etapa (recursión hacia atrás)", padding=4)
        tab.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        self.txt = tk.Text(tab, font=FUENTE_MONO, wrap="none", background="white", relief="flat")
        sy = ttk.Scrollbar(tab, orient="vertical", command=self.txt.yview)
        sx = ttk.Scrollbar(tab, orient="horizontal", command=self.txt.xview)
        self.txt.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.txt.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        self.txt.tag_configure("titulo", font=("Consolas", 10, "bold"), foreground="#1f4e79")
        self.txt.tag_configure("optimo", background="#ffe8cc", foreground=COLOR_RUTA)

    # --- Datos ------------------------------------------------------------
    def productos(self):
        res = []
        for i in self.tv_prod.get_children():
            nom, w, r = self.tv_prod.item(i, "values")
            res.append((nom, int(w), int(r)))
        return res

    def _poner_productos(self, productos):
        self.tv_prod.delete(*self.tv_prod.get_children())
        for p in productos:
            self.tv_prod.insert("", "end", values=p)

    def _cargar_seleccion(self, _evento):
        sel = self.tv_prod.selection()
        if sel:
            nom, w, r = self.tv_prod.item(sel[0], "values")
            self.e_nom.set(nom), self.e_peso.set(w), self.e_precio.set(r)

    def agregar(self):
        nom = self.e_nom.get().strip()
        try:
            if not nom:
                raise ValueError("Indique el nombre del producto.")
            w = entero(self.e_peso.get(), "Peso", 1)
            r = entero(self.e_precio.get(), "Precio", 0)
        except ValueError as e:
            messagebox.showerror("Dato inválido", str(e))
            return
        for i in self.tv_prod.get_children():
            if self.tv_prod.item(i, "values")[0] == nom:
                self.tv_prod.item(i, values=(nom, w, r))
                break
        else:
            self.tv_prod.insert("", "end", values=(nom, w, r))
        self.calcular()

    def eliminar(self):
        sel = self.tv_prod.selection()
        if not sel:
            messagebox.showinfo("Eliminar", "Seleccione un producto de la tabla.")
            return
        for i in sel:
            self.tv_prod.delete(i)
        self.calcular()

    def mover(self, delta):
        """Cambia el orden de los productos (= orden de las etapas)."""
        for i in self.tv_prod.selection():
            self.tv_prod.move(i, "", self.tv_prod.index(i) + delta)
        self.calcular()

    def restaurar(self):
        self._poner_productos(vc.PRODUCTOS)
        self.capacidad.set(vc.CAPACIDAD)
        self.modo.set("01")
        self.calcular()

    # --- Cálculo ----------------------------------------------------------
    def calcular(self):
        productos = self.productos()
        if not productos:
            messagebox.showerror("Sin datos", "Agregue al menos un producto.")
            return
        try:
            W = entero(self.capacidad.get(), "Capacidad", 1)
            if self.modo.get() == "01":
                max_u = 1
            elif self.modo.get() == "ilim":
                max_u = W
            else:
                max_u = entero(self.max_u.get(), "Máximo de unidades", 1)
        except ValueError as e:
            messagebox.showerror("Dato inválido", str(e))
            return

        valor, plan, tablas = vc.volumen_carga(productos, W, max_u)

        self.tv_sol.delete(*self.tv_sol.get_children())
        peso = 0
        for (nom, w, r), m in zip(productos, plan):
            if m:
                self.tv_sol.insert("", "end", values=(nom, m, w * m, r * m))
                peso += w * m
        self.resumen.configure(
            text=f"Valor total máximo: ${valor}     Peso usado: {peso} de {W} kg (libre: {W - peso} kg)")

        # Estados visitados por la solución óptima en cada etapa
        estados, x = {}, W
        for i, m in enumerate(plan, start=1):
            estados[i] = x
            x -= productos[i - 1][1] * m

        t = self.txt
        t.configure(state="normal")
        t.delete("1.0", "end")
        t.insert("end", "f_i(x) = max { r_i·m_i + f_{i+1}(x − w_i·m_i) },  f_{n+1}(x) = 0\n\n")
        for i, nom, w, r, filas in tablas:
            t.insert("end", f"Etapa {i}: {nom} (w={w} kg, r=${r})\n", "titulo")
            cols = list(range(0, min(max_u, W // w) + 1))
            t.insert("end", f"{'x':>4} | " + "".join(f"{'m=' + str(m):>7}" for m in cols)
                     + f" | {'f(x)':>6} {'m*':>4}\n")
            t.insert("end", "-" * (8 + 7 * len(cols) + 13) + "\n")
            for x, valores, fx, m_opt in filas:
                celdas = "".join(f"{(str(valores[m]) if m in valores else '-'):>7}" for m in cols)
                linea = f"{x:>4} | {celdas} | {fx:>6} {m_opt:>4}\n"
                t.insert("end", linea, "optimo" if estados.get(i) == x else ())
            t.insert("end", "\n")
        t.configure(state="disabled")


# ---------------------------------------------------------------------------
class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Parcial V - Programación Dinámica (UJAP)")
        self.geometry("1150x720")
        self.minsize(950, 600)

        estilo = ttk.Style(self)
        if "vista" in estilo.theme_names():
            estilo.theme_use("vista")
        estilo.configure("Accion.TButton", font=("Segoe UI", 10, "bold"))
        estilo.configure("Resumen.TLabel", font=("Segoe UI", 10, "bold"), foreground="#1f4e79")
        estilo.configure("Treeview", rowheight=22)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        nb.add(PestanaRutas(nb), text="  1c · Ruta más corta  ")
        nb.add(PestanaCarga(nb), text="  2 · Volumen de carga  ")


if __name__ == "__main__":
    Aplicacion().mainloop()
