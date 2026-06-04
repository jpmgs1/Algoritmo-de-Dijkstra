import tkinter as tk
from tkinter import messagebox
import math
import heapq
import time
import threading

# ── Cores ────────────────────────────────────────────────────────────
BG       = "#0f1117"
PANEL    = "#1a1d27"
CARD     = "#21253a"
ACCENT   = "#4f8ef7"
GREEN    = "#22d3a0"
YELLOW   = "#f5c542"
RED      = "#f75f5f"
PURPLE   = "#a855f7"
TEXT     = "#e8eaf0"
SUBTEXT  = "#8890a8"
EDGE_COL = "#3a3f5c"
NODE_DEF = "#2c3150"
NODE_BOR = "#4f6080"
R = 22  # raio do nó


def dijkstra_steps(nodes, edges, source, target):
    INF = float('inf')
    dist_map = {n: INF for n in nodes}
    prev_map = {n: None for n in nodes}
    dist_map[source] = 0
    pq = [(0, source)]
    vis = set()
    states = []

    while pq:
        d, u = heapq.heappop(pq)
        if u in vis:
            continue
        vis.add(u)
        states.append({
            "dist": dict(dist_map),
            "prev": dict(prev_map),
            "visited": set(vis),
            "current": u,
        })
        if u == target:
            break
        for (a, b), w in edges.items():
            v = b if a == u else (a if b == u else None)
            if v is None or v in vis:
                continue
            nd = d + w
            if nd < dist_map[v]:
                dist_map[v] = nd
                prev_map[v] = u
                heapq.heappush(pq, (nd, v))

    # reconstruir caminho
    path_nodes = []
    cur = target
    while cur is not None:
        path_nodes.append(cur)
        cur = prev_map[cur]
    path_nodes.reverse()
    if not path_nodes or path_nodes[0] != source:
        path_nodes = []

    return states, path_nodes, dist_map


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador de Dijkstra")
        self.configure(bg=BG)
        self.geometry("1180x740")
        self.resizable(True, True)

        # Estado do grafo
        self.nodes = {}          # id -> (x, y)
        self.edges = {}          # (u,v) -> weight   u < v
        self.node_id = 0

        self.start_node = None
        self.end_node   = None
        self.sel        = []     # nós selecionados para aresta

        # Estado da animação
        self.step_states = []
        self.path_nodes  = []
        self.step_idx    = -1
        self.animating   = False

        # Tkinter vars
        self.mode       = tk.StringVar(value="add_node")
        self.weight_var = tk.StringVar(value="1")
        self.speed_var  = tk.DoubleVar(value=0.6)

        self._build_ui()
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Button-3>", self._cancel_sel)

    # ── UI ────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Painel esquerdo
        left = tk.Frame(self, bg=PANEL, width=230)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="DIJKSTRA", bg=PANEL, fg=ACCENT,
                 font=("Courier", 16, "bold"), pady=10).pack()
        tk.Label(left, text="Simulador Visual", bg=PANEL, fg=SUBTEXT,
                 font=("Courier", 10)).pack()
        self._sep(left)

        tk.Label(left, text="MODO", bg=PANEL, fg=SUBTEXT,
                 font=("Courier", 8), anchor="w", padx=16).pack(fill="x")

        for label, val, col in [
            ("+ Adicionar Nó",    "add_node",  TEXT),
            ("~ Adicionar Aresta","add_edge",  TEXT),
            ("S  Definir Origem", "set_start", ACCENT),
            ("E  Definir Destino","set_end",   RED),
            ("x  Remover",       "remove",    SUBTEXT),
        ]:
            tk.Radiobutton(
                left, text=label, variable=self.mode, value=val,
                bg=PANEL, fg=col, selectcolor=CARD,
                activebackground=PANEL, activeforeground=ACCENT,
                font=("Courier", 10), anchor="w", padx=20,
            ).pack(fill="x", pady=1)

        self._sep(left)
        tk.Label(left, text="PESO DA ARESTA", bg=PANEL, fg=SUBTEXT,
                 font=("Courier", 8), anchor="w", padx=16).pack(fill="x")
        tk.Entry(left, textvariable=self.weight_var, bg=CARD, fg=TEXT,
                 insertbackground=TEXT, font=("Courier", 12), relief="flat",
                 justify="center").pack(pady=4, padx=20, fill="x")

        self._sep(left)
        tk.Label(left, text="VELOCIDADE", bg=PANEL, fg=SUBTEXT,
                 font=("Courier", 8), anchor="w", padx=16).pack(fill="x")
        tk.Scale(left, from_=0.05, to=2.0, resolution=0.05,
                 variable=self.speed_var, orient="horizontal",
                 bg=PANEL, fg=TEXT, troughcolor=CARD,
                 highlightthickness=0, sliderrelief="flat",
                 activebackground=ACCENT).pack(fill="x", padx=16)

        self._sep(left)
        self._btn(left, "EXECUTAR",       self._run,        ACCENT)
        self._btn(left, "< Passo Anterior", self._step_prev, PURPLE)
        self._btn(left, "Proximo Passo >",  self._step_next, PURPLE)
        self._btn(left, "LIMPAR TUDO",    self._clear,      RED)

        self._sep(left)
        tk.Label(left, text="LEGENDA", bg=PANEL, fg=SUBTEXT,
                 font=("Courier", 8), anchor="w", padx=16).pack(fill="x")
        for color, label in [
            (NODE_DEF, "No comum"),
            (ACCENT,   "Origem (S)"),
            (RED,      "Destino (E)"),
            (YELLOW,   "Processando"),
            (PURPLE,   "Visitado"),
            (GREEN,    "Caminho minimo"),
        ]:
            row = tk.Frame(left, bg=PANEL)
            row.pack(fill="x", padx=16, pady=1)
            tk.Canvas(row, width=14, height=14, bg=color,
                      highlightthickness=1, relief="flat").pack(side="left")
            tk.Label(row, text=f"  {label}", bg=PANEL, fg=SUBTEXT,
                     font=("Courier", 9)).pack(side="left")

        # Canvas central
        center = tk.Frame(self, bg=BG)
        center.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(center, bg=BG, highlightthickness=0,
                                cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)

        self.status_var = tk.StringVar(value="Selecione 'Adicionar No' e clique no canvas")
        tk.Label(center, textvariable=self.status_var, bg=PANEL, fg=SUBTEXT,
                 font=("Courier", 10), anchor="w", padx=10,
                 pady=5).pack(fill="x", side="bottom")

        # Painel direito
        right = tk.Frame(self, bg=PANEL, width=210)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        tk.Label(right, text="DISTANCIAS", bg=PANEL, fg=ACCENT,
                 font=("Courier", 11, "bold"), pady=8).pack()
        self._sep(right)
        self.dist_frame = tk.Frame(right, bg=PANEL)
        self.dist_frame.pack(fill="both", expand=True, padx=8)

        self._sep(right)
        tk.Label(right, text="CAMINHO", bg=PANEL, fg=GREEN,
                 font=("Courier", 11, "bold")).pack()
        self.path_label = tk.Label(right, text="—", bg=PANEL, fg=TEXT,
                                    font=("Courier", 10), wraplength=195,
                                    justify="left")
        self.path_label.pack(padx=8, pady=4)

        self._sep(right)
        tk.Label(right, text="PASSO ATUAL", bg=PANEL, fg=YELLOW,
                 font=("Courier", 11, "bold")).pack()
        self.step_label = tk.Label(right, text="—", bg=PANEL, fg=TEXT,
                                    font=("Courier", 10), wraplength=195,
                                    justify="left")
        self.step_label.pack(padx=8, pady=4)

    def _sep(self, parent):
        tk.Frame(parent, bg=EDGE_COL, height=1).pack(fill="x", pady=5)

    def _btn(self, parent, text, cmd, color):
        tk.Button(parent, text=text, command=cmd, bg=color, fg="white",
                  relief="flat", font=("Courier", 10, "bold"),
                  activebackground=BG, activeforeground=color,
                  pady=6, cursor="hand2").pack(fill="x", padx=16, pady=3)

    # ── Eventos ───────────────────────────────────────────────────────
    def _on_click(self, event):
        x, y = event.x, event.y
        mode = self.mode.get()

        if mode == "add_node":
            # verifica sobreposição
            for nx, ny in self.nodes.values():
                if math.hypot(x - nx, y - ny) < R * 2:
                    self.status_var.set("Muito perto de outro no!")
                    return
            nid = self.node_id
            self.nodes[nid] = (x, y)
            self.node_id += 1
            self.status_var.set(f"No {nid} criado")
            self._redraw()

        elif mode == "add_edge":
            nid = self._node_at(x, y)
            if nid is None:
                self.status_var.set("Clique em cima de um no")
                return
            if nid not in self.sel:
                self.sel.append(nid)
            self._redraw()
            if len(self.sel) == 2:
                u, v = self.sel
                self.sel.clear()
                if u == v:
                    self.status_var.set("Selecione nos diferentes")
                    return
                try:
                    w = float(self.weight_var.get())
                    assert w > 0
                except Exception:
                    messagebox.showerror("Erro", "Peso deve ser numero positivo")
                    return
                key = (min(u, v), max(u, v))
                self.edges[key] = w
                self.status_var.set(f"Aresta {u}<->{v}  peso={w}")
                self._redraw()

        elif mode == "set_start":
            nid = self._node_at(x, y)
            if nid is not None:
                self.start_node = nid
                self.status_var.set(f"Origem = No {nid}")
                self._redraw()

        elif mode == "set_end":
            nid = self._node_at(x, y)
            if nid is not None:
                self.end_node = nid
                self.status_var.set(f"Destino = No {nid}")
                self._redraw()

        elif mode == "remove":
            nid = self._node_at(x, y)
            if nid is not None:
                del self.nodes[nid]
                self.edges = {k: v for k, v in self.edges.items() if nid not in k}
                if self.start_node == nid: self.start_node = None
                if self.end_node   == nid: self.end_node   = None
                self.status_var.set(f"No {nid} removido")
                self._redraw()

    def _cancel_sel(self, event=None):
        self.sel.clear()
        self._redraw()

    def _node_at(self, x, y):
        for nid, (nx, ny) in self.nodes.items():
            if math.hypot(x - nx, y - ny) <= R:
                return nid
        return None

    # ── Dijkstra ──────────────────────────────────────────────────────
    def _run(self):
        if self.start_node is None or self.end_node is None:
            messagebox.showinfo("Aviso", "Defina Origem (S) e Destino (E) primeiro.")
            return
        if self.animating:
            return
        states, path, _ = dijkstra_steps(
            self.nodes, self.edges, self.start_node, self.end_node)
        if not states:
            messagebox.showinfo("Aviso", "Nenhum caminho encontrado.")
            return
        self.step_states = states
        self.path_nodes  = path
        self.step_idx    = -1
        self._animate()

    def _animate(self):
        self.animating = True
        def run():
            for i, state in enumerate(self.step_states):
                self.step_idx = i
                final = (i == len(self.step_states) - 1)
                self.after(0, lambda s=state, f=final: self._apply(s, f))
                time.sleep(self.speed_var.get())
            self.animating = False
        threading.Thread(target=run, daemon=True).start()

    def _step_prev(self):
        if not self.step_states: return
        self.step_idx = max(0, self.step_idx - 1)
        self._apply(self.step_states[self.step_idx],
                    self.step_idx == len(self.step_states) - 1)

    def _step_next(self):
        if not self.step_states: return
        self.step_idx = min(len(self.step_states) - 1, self.step_idx + 1)
        self._apply(self.step_states[self.step_idx],
                    self.step_idx == len(self.step_states) - 1)

    def _apply(self, state, final):
        self._redraw(state=state, final=final)
        # painel de distâncias
        for w in self.dist_frame.winfo_children():
            w.destroy()
        INF = float('inf')
        for nid in sorted(self.nodes.keys()):
            d = state["dist"].get(nid, INF)
            txt = "inf" if d == INF else str(round(d, 2))
            col = GREEN if (final and nid in self.path_nodes) else TEXT
            row = tk.Frame(self.dist_frame, bg=PANEL)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=f"No {nid}:", bg=PANEL, fg=SUBTEXT,
                     font=("Courier", 9), width=7, anchor="w").pack(side="left")
            tk.Label(row, text=txt, bg=PANEL, fg=col,
                     font=("Courier", 9, "bold")).pack(side="left")
        # step label
        cur = state.get("current")
        total = len(self.step_states)
        self.step_label.config(
            text=f"No atual: {cur}\nPasso {self.step_idx+1}/{total}")
        # caminho
        if final:
            if self.path_nodes:
                cost = state["dist"].get(self.end_node, INF)
                self.path_label.config(
                    text=" -> ".join(str(n) for n in self.path_nodes)
                         + f"\nCusto: {round(cost,2)}")
                self.step_label.config(text="Concluido!")
            else:
                self.path_label.config(text="Sem caminho!")

    # ── Limpar ────────────────────────────────────────────────────────
    def _clear(self):
        self.nodes.clear(); self.edges.clear()
        self.node_id = 0
        self.start_node = None; self.end_node = None
        self.sel.clear()
        self.step_states.clear(); self.path_nodes.clear()
        self.step_idx = -1
        self.path_label.config(text="—")
        self.step_label.config(text="—")
        for w in self.dist_frame.winfo_children(): w.destroy()
        self._redraw()
        self.status_var.set("Canvas limpo")

    # ── Desenho ───────────────────────────────────────────────────────
    def _redraw(self, state=None, final=False):
        c = self.canvas
        c.delete("all")

        visited_set = state["visited"] if state else set()
        current     = state["current"] if state else None
        dist_map    = state["dist"]    if state else {}

        path_set   = set(self.path_nodes) if final else set()
        path_edges = set()
        if final and len(self.path_nodes) > 1:
            for i in range(len(self.path_nodes) - 1):
                a, b = self.path_nodes[i], self.path_nodes[i+1]
                path_edges.add((min(a, b), max(a, b)))

        # Desenha arestas
        for (u, v), w in self.edges.items():
            if u not in self.nodes or v not in self.nodes:
                continue
            x1, y1 = self.nodes[u]
            x2, y2 = self.nodes[v]
            key = (min(u, v), max(u, v))
            if key in path_edges:
                col, width = GREEN, 4
            elif u in visited_set and v in visited_set:
                col, width = PURPLE, 2
            else:
                col, width = EDGE_COL, 2
            c.create_line(x1, y1, x2, y2, fill=col, width=width)
            mx, my = (x1+x2)//2, (y1+y2)//2
            c.create_oval(mx-12, my-10, mx+12, my+10, fill=CARD, outline=col)
            c.create_text(mx, my, text=str(w), fill=TEXT, font=("Courier", 9, "bold"))

        # Desenha nós
        for nid, (x, y) in self.nodes.items():
            if final and nid in path_set:
                fill, border, tc = GREEN,  "#16a87e", BG
            elif nid == current:
                fill, border, tc = YELLOW, "#d4a800", BG
            elif nid in visited_set:
                fill, border, tc = PURPLE, "#7c3aed", TEXT
            elif nid == self.start_node:
                fill, border, tc = ACCENT, "#2563eb", BG
            elif nid == self.end_node:
                fill, border, tc = RED,    "#b91c1c", TEXT
            elif nid in self.sel:
                fill, border, tc = YELLOW, "#d4a800", BG
            else:
                fill, border, tc = NODE_DEF, NODE_BOR, TEXT

            c.create_oval(x-R, y-R, x+R, y+R,
                          fill=fill, outline=border, width=2)
            c.create_text(x, y, text=str(nid),
                          fill=tc, font=("Courier", 10, "bold"))

            # distância acima do nó
            if dist_map:
                d = dist_map.get(nid, float('inf'))
                lbl = "inf" if d == float('inf') else str(round(d, 1))
                c.create_text(x, y - R - 9, text=lbl,
                              fill=YELLOW, font=("Courier", 8))

            # marcadores S / E
            if nid == self.start_node:
                c.create_text(x+R+6, y-R-4, text="S",
                              fill=ACCENT, font=("Courier", 9, "bold"))
            if nid == self.end_node:
                c.create_text(x+R+6, y-R-4, text="E",
                              fill=RED, font=("Courier", 9, "bold"))


if __name__ == "__main__":
    App().mainloop()
