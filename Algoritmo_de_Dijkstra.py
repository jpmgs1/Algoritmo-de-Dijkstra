import tkinter as tk
from tkinter import messagebox
import math
import heapq
import time
import threading

# ── Paleta refinada ──────────────────────────────────────────────────
BG       = "#080b12"
PANEL    = "#0d111c"
CARD     = "#131929"
CARD2    = "#1a2138"
ACCENT   = "#3b82f6"
ACCENT2  = "#60a5fa"
GREEN    = "#10d9a0"
GREEN2   = "#34eba8"
YELLOW   = "#f59e0b"
YELLOW2  = "#fcd34d"
RED      = "#ef4444"
RED2     = "#f87171"
PURPLE   = "#8b5cf6"
PURPLE2  = "#a78bfa"
TEXT     = "#e2e8f0"
TEXT2    = "#94a3b8"
TEXT3    = "#475569"
EDGE_DEF = "#1e2d4a"
EDGE_HI  = "#2d4070"
NODE_DEF = "#111827"
NODE_BOR = "#1d3a5f"
GLOW     = "#1a3a6e"
R        = 24   # raio do nó


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
            "dist":    dict(dist_map),
            "prev":    dict(prev_map),
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

    path_nodes = []
    cur = target
    while cur is not None:
        path_nodes.append(cur)
        cur = prev_map[cur]
    path_nodes.reverse()
    if not path_nodes or path_nodes[0] != source:
        path_nodes = []

    return states, path_nodes, dist_map


class Tooltip:
    """Tooltip simples para widgets tkinter."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tw = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        x = self.widget.winfo_rootx() + 30
        y = self.widget.winfo_rooty() + 24
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(
            self.tw, text=self.text, bg=CARD2, fg=TEXT2,
            font=("Consolas", 9), relief="flat", padx=8, pady=4,
            bd=0
        )
        lbl.pack()

    def hide(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dijkstra · Simulador Visual")
        self.configure(bg=BG)
        self.geometry("1280x760")
        self.resizable(True, True)

        # Estado do grafo
        self.nodes    = {}
        self.edges    = {}
        self.node_id  = 0

        self.start_node = None
        self.end_node   = None
        self.sel        = []

        # Animação
        self.step_states = []
        self.path_nodes  = []
        self.step_idx    = -1
        self.animating   = False

        # Variáveis Tk
        self.mode       = tk.StringVar(value="add_node")
        self.weight_var = tk.StringVar(value="1")
        self.speed_var  = tk.DoubleVar(value=0.6)

        self._build_ui()
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Button-3>", self._cancel_sel)

    # ─────────────────────────────────────────────────────────────────
    # Construção da UI
    # ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Painel esquerdo ──────────────────────────────────────────
        left = tk.Frame(self, bg=PANEL, width=248)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        # Cabeçalho
        hdr = tk.Frame(left, bg=CARD, pady=0)
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="◈  DIJKSTRA", bg=CARD, fg=ACCENT2,
            font=("Consolas", 15, "bold"), pady=14, padx=18, anchor="w"
        ).pack(fill="x")
        tk.Label(
            hdr, text="  Simulador de Caminho Mínimo", bg=CARD, fg=TEXT3,
            font=("Consolas", 9), pady=0, padx=18, anchor="w"
        ).pack(fill="x")
        tk.Frame(hdr, bg=ACCENT, height=2).pack(fill="x", pady=(10, 0))

        # Seção: Modo de Interação
        self._section(left, "INTERAÇÃO")
        modes = [
            ("add_node",  "⊕", "Adicionar Nó",     TEXT,    "Clique no canvas para criar nós"),
            ("add_edge",  "⟵", "Adicionar Aresta",  TEXT,    "Clique em dois nós para conectar"),
            ("set_start", "◉", "Definir Origem",    ACCENT2, "Define o nó de partida (S)"),
            ("set_end",   "◎", "Definir Destino",   RED2,    "Define o nó de chegada (E)"),
            ("remove",    "⊗", "Remover",           TEXT3,   "Clique em um nó para remover"),
        ]
        self.mode_btns = []
        for val, icon, label, col, tip in modes:
            btn = self._mode_radio(left, icon, label, val, col)
            Tooltip(btn, tip)
            self.mode_btns.append(btn)

        # Seção: Configurações
        self._section(left, "CONFIGURAÇÕES")

        wf = tk.Frame(left, bg=PANEL)
        wf.pack(fill="x", padx=18, pady=4)
        tk.Label(wf, text="⚖  Peso da Aresta", bg=PANEL, fg=TEXT2,
                 font=("Consolas", 9), anchor="w").pack(fill="x")
        entry_frame = tk.Frame(wf, bg=EDGE_HI, pady=1)
        entry_frame.pack(fill="x", pady=(4, 0))
        tk.Entry(
            entry_frame, textvariable=self.weight_var,
            bg=CARD2, fg=ACCENT2, insertbackground=ACCENT2,
            font=("Consolas", 13, "bold"), relief="flat",
            justify="center", bd=0
        ).pack(fill="x", padx=1, pady=1, ipady=4)

        sf = tk.Frame(left, bg=PANEL)
        sf.pack(fill="x", padx=18, pady=(12, 4))
        spd_header = tk.Frame(sf, bg=PANEL)
        spd_header.pack(fill="x")
        tk.Label(spd_header, text="⏱  Velocidade", bg=PANEL, fg=TEXT2,
                 font=("Consolas", 9), anchor="w").pack(side="left")
        self.spd_lbl = tk.Label(spd_header, text="0.60s", bg=PANEL, fg=ACCENT,
                                 font=("Consolas", 9, "bold"))
        self.spd_lbl.pack(side="right")
        tk.Scale(
            sf, from_=0.05, to=2.0, resolution=0.05,
            variable=self.speed_var, orient="horizontal",
            bg=PANEL, fg=TEXT2, troughcolor=CARD2,
            highlightthickness=0, sliderrelief="flat",
            activebackground=ACCENT, showvalue=False,
            command=lambda v: self.spd_lbl.config(text=f"{float(v):.2f}s")
        ).pack(fill="x", pady=(4, 0))

        # Seção: Controles
        self._section(left, "CONTROLES")
        self._action_btn(left, "▶  EXECUTAR",         self._run,        ACCENT,  CARD2)
        ctrl_row = tk.Frame(left, bg=PANEL)
        ctrl_row.pack(fill="x", padx=18, pady=2)
        self._small_btn(ctrl_row, "◀  Anterior", self._step_prev, PURPLE)
        tk.Frame(ctrl_row, bg=PANEL, width=6).pack(side="left")
        self._small_btn(ctrl_row, "Próximo  ▶", self._step_next, PURPLE)
        self._action_btn(left, "✕  LIMPAR TUDO",      self._clear,      RED,     CARD2)

        # Seção: Legenda
        self._section(left, "LEGENDA")
        legends = [
            (NODE_DEF, NODE_BOR, "Nó comum"),
            (ACCENT,   ACCENT2,  "Origem  (S)"),
            (RED,      RED2,     "Destino  (E)"),
            (YELLOW,   YELLOW2,  "Processando"),
            (PURPLE,   PURPLE2,  "Visitado"),
            (GREEN,    GREEN2,   "Caminho mínimo"),
        ]
        for fill, border, label in legends:
            row = tk.Frame(left, bg=PANEL)
            row.pack(fill="x", padx=18, pady=2)
            c = tk.Canvas(row, width=16, height=16, bg=PANEL,
                          highlightthickness=0)
            c.pack(side="left")
            c.create_oval(1, 1, 15, 15, fill=fill, outline=border, width=2)
            tk.Label(row, text=f"  {label}", bg=PANEL, fg=TEXT2,
                     font=("Consolas", 9)).pack(side="left")

        # ── Canvas central ───────────────────────────────────────────
        center = tk.Frame(self, bg=BG)
        center.pack(side="left", fill="both", expand=True)

        # barra de status no topo
        top_bar = tk.Frame(center, bg=CARD, height=36)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)
        tk.Label(top_bar, text="◈", bg=CARD, fg=ACCENT,
                 font=("Consolas", 11), padx=12).pack(side="left")
        self.status_var = tk.StringVar(
            value="Selecione 'Adicionar Nó' e clique no canvas")
        tk.Label(top_bar, textvariable=self.status_var, bg=CARD, fg=TEXT2,
                 font=("Consolas", 10), anchor="w").pack(side="left", fill="y")
        # indicador de modo
        self.mode_indicator = tk.Label(
            top_bar, text="MODO: Adicionar Nó", bg=CARD, fg=ACCENT2,
            font=("Consolas", 9, "bold"), padx=12)
        self.mode_indicator.pack(side="right", fill="y")
        # traça modo atual
        self.mode.trace_add("write", self._update_mode_indicator)

        self.canvas = tk.Canvas(center, bg=BG, highlightthickness=0,
                                cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)

        # ── Painel direito ───────────────────────────────────────────
        right = tk.Frame(self, bg=PANEL, width=220)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        # Distâncias
        dhdr = tk.Frame(right, bg=CARD)
        dhdr.pack(fill="x")
        tk.Label(dhdr, text="⊶  DISTÂNCIAS", bg=CARD, fg=ACCENT2,
                 font=("Consolas", 11, "bold"), pady=12, padx=14,
                 anchor="w").pack(fill="x")
        tk.Frame(dhdr, bg=ACCENT, height=2).pack(fill="x")

        self.dist_canvas = tk.Canvas(right, bg=PANEL,
                                      highlightthickness=0, height=260)
        self.dist_canvas.pack(fill="x")
        self.dist_frame = tk.Frame(self.dist_canvas, bg=PANEL)
        self.dist_canvas.create_window(0, 0, anchor="nw", window=self.dist_frame)

        tk.Frame(right, bg=EDGE_DEF, height=1).pack(fill="x", pady=4)

        # Caminho
        tk.Label(right, text="⟶  CAMINHO", bg=PANEL, fg=GREEN,
                 font=("Consolas", 11, "bold"), padx=14, anchor="w",
                 pady=6).pack(fill="x")
        self.path_label = tk.Label(
            right, text="—", bg=CARD, fg=TEXT2,
            font=("Consolas", 10), wraplength=200,
            justify="left", padx=12, pady=8, anchor="nw")
        self.path_label.pack(fill="x", padx=10)

        tk.Frame(right, bg=EDGE_DEF, height=1).pack(fill="x", pady=4)

        # Passo atual
        tk.Label(right, text="◉  ESTADO ATUAL", bg=PANEL, fg=YELLOW,
                 font=("Consolas", 11, "bold"), padx=14, anchor="w",
                 pady=6).pack(fill="x")
        self.step_label = tk.Label(
            right, text="—", bg=CARD, fg=TEXT2,
            font=("Consolas", 10), wraplength=200,
            justify="left", padx=12, pady=8, anchor="nw")
        self.step_label.pack(fill="x", padx=10)

        # progresso
        tk.Frame(right, bg=EDGE_DEF, height=1).pack(fill="x", pady=4)
        tk.Label(right, text="◈  PROGRESSO", bg=PANEL, fg=TEXT3,
                 font=("Consolas", 10, "bold"), padx=14, anchor="w").pack(fill="x")
        prog_frame = tk.Frame(right, bg=PANEL, padx=10, pady=6)
        prog_frame.pack(fill="x")
        self.prog_bg = tk.Canvas(prog_frame, bg=CARD2, height=6,
                                  highlightthickness=0)
        self.prog_bg.pack(fill="x")
        self.prog_fill = None

    # ─────────────────────────────────────────────────────────────────
    # Helpers de UI
    # ─────────────────────────────────────────────────────────────────
    def _section(self, parent, title):
        f = tk.Frame(parent, bg=PANEL)
        f.pack(fill="x", padx=14, pady=(14, 4))
        tk.Label(f, text=title, bg=PANEL, fg=TEXT3,
                 font=("Consolas", 8, "bold"), anchor="w").pack(side="left")
        tk.Frame(f, bg=TEXT3, height=1).pack(side="left", fill="x",
                                               expand=True, padx=(8, 0), pady=4)

    def _mode_radio(self, parent, icon, label, value, color):
        var = self.mode
        frame = tk.Frame(parent, bg=PANEL, cursor="hand2")
        frame.pack(fill="x", padx=14, pady=1)

        def on_enter(e):
            if var.get() != value:
                frame.config(bg=CARD)
                icon_lbl.config(bg=CARD)
                text_lbl.config(bg=CARD)

        def on_leave(e):
            if var.get() != value:
                frame.config(bg=PANEL)
                icon_lbl.config(bg=PANEL)
                text_lbl.config(bg=PANEL)

        def select(e=None):
            var.set(value)
            self._refresh_mode_btns()

        icon_lbl = tk.Label(frame, text=icon, bg=PANEL, fg=color,
                             font=("Consolas", 13), width=3, padx=4,
                             pady=5, anchor="center")
        icon_lbl.pack(side="left")
        text_lbl = tk.Label(frame, text=label, bg=PANEL, fg=TEXT,
                             font=("Consolas", 10), anchor="w", pady=5)
        text_lbl.pack(side="left", fill="x", expand=True)

        for w in (frame, icon_lbl, text_lbl):
            w.bind("<Button-1>", select)
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

        frame._value     = value
        frame._icon_lbl  = icon_lbl
        frame._text_lbl  = text_lbl
        frame._color     = color
        return frame

    def _refresh_mode_btns(self):
        cur = self.mode.get()
        for frame in self.mode_btns:
            active = (frame._value == cur)
            bg = CARD2 if active else PANEL
            frame.config(bg=bg)
            frame._icon_lbl.config(
                bg=bg,
                fg=frame._color if active else TEXT3
            )
            frame._text_lbl.config(
                bg=bg,
                fg=TEXT if active else TEXT2
            )

    def _update_mode_indicator(self, *_):
        labels = {
            "add_node":  "Adicionar Nó",
            "add_edge":  "Adicionar Aresta",
            "set_start": "Definir Origem",
            "set_end":   "Definir Destino",
            "remove":    "Remover",
        }
        self.mode_indicator.config(
            text=f"MODO: {labels.get(self.mode.get(), '')}")

    def _action_btn(self, parent, text, cmd, color, bg=None):
        bg = bg or PANEL
        btn = tk.Button(
            parent, text=text, command=cmd,
            bg=color, fg="white", relief="flat",
            font=("Consolas", 10, "bold"),
            activebackground=BG, activeforeground=color,
            pady=8, cursor="hand2", bd=0,
            activerelief="flat"
        )
        btn.pack(fill="x", padx=18, pady=3)

        def on_enter(e): btn.config(bg=self._lighten(color))
        def on_leave(e): btn.config(bg=color)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def _small_btn(self, parent, text, cmd, color):
        btn = tk.Button(
            parent, text=text, command=cmd,
            bg=CARD2, fg=color, relief="flat",
            font=("Consolas", 9, "bold"),
            activebackground=color, activeforeground="white",
            pady=6, cursor="hand2", bd=0,
            activerelief="flat"
        )
        btn.pack(side="left", fill="x", expand=True, ipady=1)
        return btn

    def _lighten(self, hex_color):
        """Clareia levemente uma cor hex para hover."""
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, r + 30)
        g = min(255, g + 30)
        b = min(255, b + 30)
        return f"#{r:02x}{g:02x}{b:02x}"

    # ─────────────────────────────────────────────────────────────────
    # Eventos do canvas
    # ─────────────────────────────────────────────────────────────────
    def _on_click(self, event):
        x, y = event.x, event.y
        mode = self.mode.get()

        if mode == "add_node":
            for nx, ny in self.nodes.values():
                if math.hypot(x - nx, y - ny) < R * 2.2:
                    self._set_status("⚠  Muito perto de outro nó!", RED2)
                    return
            nid = self.node_id
            self.nodes[nid] = (x, y)
            self.node_id += 1
            self._set_status(f"✔  Nó {nid} criado")
            self._redraw()

        elif mode == "add_edge":
            nid = self._node_at(x, y)
            if nid is None:
                self._set_status("⊕  Clique em cima de um nó")
                return
            if nid not in self.sel:
                self.sel.append(nid)
            self._redraw()
            if len(self.sel) == 2:
                u, v = self.sel
                self.sel.clear()
                if u == v:
                    self._set_status("⚠  Selecione nós diferentes!", RED2)
                    return
                try:
                    w = float(self.weight_var.get())
                    assert w > 0
                except Exception:
                    messagebox.showerror("Erro", "Peso deve ser número positivo")
                    return
                key = (min(u, v), max(u, v))
                self.edges[key] = w
                self._set_status(f"✔  Aresta {u} ↔ {v}  |  peso = {w}")
                self._redraw()

        elif mode == "set_start":
            nid = self._node_at(x, y)
            if nid is not None:
                self.start_node = nid
                self._set_status(f"◉  Origem definida → Nó {nid}", ACCENT2)
                self._redraw()

        elif mode == "set_end":
            nid = self._node_at(x, y)
            if nid is not None:
                self.end_node = nid
                self._set_status(f"◎  Destino definido → Nó {nid}", RED2)
                self._redraw()

        elif mode == "remove":
            nid = self._node_at(x, y)
            if nid is not None:
                del self.nodes[nid]
                self.edges = {k: v for k, v in self.edges.items()
                              if nid not in k}
                if self.start_node == nid: self.start_node = None
                if self.end_node   == nid: self.end_node   = None
                self._set_status(f"✕  Nó {nid} removido", RED2)
                self._redraw()

    def _cancel_sel(self, event=None):
        self.sel.clear()
        self._redraw()

    def _node_at(self, x, y):
        for nid, (nx, ny) in self.nodes.items():
            if math.hypot(x - nx, y - ny) <= R:
                return nid
        return None

    def _set_status(self, msg, color=TEXT2):
        self.status_var.set(msg)

    # ─────────────────────────────────────────────────────────────────
    # Dijkstra / animação
    # ─────────────────────────────────────────────────────────────────
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
        if not self.step_states:
            return
        self.step_idx = max(0, self.step_idx - 1)
        self._apply(self.step_states[self.step_idx],
                    self.step_idx == len(self.step_states) - 1)

    def _step_next(self):
        if not self.step_states:
            return
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
            txt = "∞" if d == INF else str(round(d, 2))
            is_path = final and nid in self.path_nodes
            row = tk.Frame(self.dist_frame, bg=CARD2 if is_path else PANEL,
                           pady=2)
            row.pack(fill="x", pady=1)
            icon = "◈" if nid == state.get("current") else \
                   ("✔" if is_path else "·")
            icon_col = YELLOW if nid == state.get("current") else \
                       (GREEN if is_path else TEXT3)
            tk.Label(row, text=icon, bg=row.cget("bg"), fg=icon_col,
                     font=("Consolas", 9), width=2).pack(side="left", padx=(6, 0))
            tk.Label(row, text=f"N{nid}", bg=row.cget("bg"), fg=TEXT2,
                     font=("Consolas", 9), width=4, anchor="w").pack(side="left")
            tk.Label(row, text=txt, bg=row.cget("bg"),
                     fg=GREEN if is_path else TEXT,
                     font=("Consolas", 10, "bold")).pack(side="right", padx=8)

        # progresso
        total = len(self.step_states)
        pct = (self.step_idx + 1) / total if total else 0
        self.prog_bg.delete("all")
        w = self.prog_bg.winfo_width() or 180
        self.prog_bg.config(width=w)
        self.prog_bg.create_rectangle(0, 0, w, 6, fill=CARD2, outline="")
        self.prog_bg.create_rectangle(0, 0, int(w * pct), 6,
                                       fill=ACCENT, outline="")

        # step label
        cur = state.get("current")
        self.step_label.config(
            text=f"Visitando: Nó {cur}\n"
                 f"Passo {self.step_idx + 1} de {total}",
            fg=YELLOW if not final else GREEN
        )

        if final:
            if self.path_nodes:
                cost = state["dist"].get(self.end_node, INF)
                self.path_label.config(
                    text="  ·  ".join(str(n) for n in self.path_nodes)
                    + f"\n\nCusto total: {round(cost, 2)}",
                    fg=GREEN
                )
                self.step_label.config(text="✔  Concluído!", fg=GREEN)
                self._set_status(
                    f"✔  Caminho encontrado! Custo = {round(cost, 2)}", GREEN)
            else:
                self.path_label.config(text="✕  Sem caminho!", fg=RED2)
                self._set_status("✕  Nenhum caminho encontrado.", RED2)

    # ─────────────────────────────────────────────────────────────────
    # Limpar
    # ─────────────────────────────────────────────────────────────────
    def _clear(self):
        self.nodes.clear()
        self.edges.clear()
        self.node_id  = 0
        self.start_node = None
        self.end_node   = None
        self.sel.clear()
        self.step_states.clear()
        self.path_nodes.clear()
        self.step_idx   = -1
        self.path_label.config(text="—", fg=TEXT2)
        self.step_label.config(text="—", fg=TEXT2)
        for w in self.dist_frame.winfo_children():
            w.destroy()
        self.prog_bg.delete("all")
        self._redraw()
        self._set_status("✕  Canvas limpo")

    # ─────────────────────────────────────────────────────────────────
    # Desenho
    # ─────────────────────────────────────────────────────────────────
    def _redraw(self, state=None, final=False):
        c = self.canvas
        c.delete("all")

        visited_set = state["visited"] if state else set()
        current     = state["current"] if state else None
        dist_map    = state["dist"]    if state else {}

        path_set  = set(self.path_nodes) if final else set()
        path_edges = set()
        if final and len(self.path_nodes) > 1:
            for i in range(len(self.path_nodes) - 1):
                a, b = self.path_nodes[i], self.path_nodes[i + 1]
                path_edges.add((min(a, b), max(a, b)))

        # grade de fundo sutil
        cw = c.winfo_width() or 1280
        ch = c.winfo_height() or 700
        GRID = 48
        for gx in range(0, cw, GRID):
            c.create_line(gx, 0, gx, ch, fill="#0e1420", width=1)
        for gy in range(0, ch, GRID):
            c.create_line(0, gy, cw, gy, fill="#0e1420", width=1)

        # ── Arestas ──────────────────────────────────────────────────
        for (u, v), w in self.edges.items():
            if u not in self.nodes or v not in self.nodes:
                continue
            x1, y1 = self.nodes[u]
            x2, y2 = self.nodes[v]
            key = (min(u, v), max(u, v))

            if key in path_edges:
                # sombra glow
                c.create_line(x1, y1, x2, y2, fill=GREEN2,
                               width=7, capstyle="round")
                c.create_line(x1, y1, x2, y2, fill=GREEN,
                               width=3, capstyle="round")
                edge_col, lbl_fg = GREEN, BG
            elif u in visited_set and v in visited_set:
                c.create_line(x1, y1, x2, y2, fill=PURPLE,
                               width=2, capstyle="round",
                               dash=(6, 3))
                edge_col, lbl_fg = PURPLE, TEXT
            else:
                c.create_line(x1, y1, x2, y2, fill=EDGE_DEF,
                               width=2, capstyle="round")
                edge_col, lbl_fg = EDGE_DEF, TEXT2

            # rótulo do peso
            mx, my = (x1 + x2) // 2, (y1 + y2) // 2
            pw = int(str(w).__len__() * 6 + 12)
            c.create_oval(mx - pw // 2, my - 9,
                           mx + pw // 2, my + 9,
                           fill=CARD2, outline=edge_col, width=1)
            c.create_text(mx, my, text=str(w), fill=lbl_fg,
                           font=("Consolas", 8, "bold"))

        # ── Nós ──────────────────────────────────────────────────────
        for nid, (x, y) in self.nodes.items():
            if final and nid in path_set:
                fill, border, tc = GREEN, GREEN2, BG
                glow_col = GREEN2
                glow_r   = 10
            elif nid == current:
                fill, border, tc = YELLOW, YELLOW2, BG
                glow_col = YELLOW2
                glow_r   = 12
            elif nid in visited_set:
                fill, border, tc = PURPLE, PURPLE2, TEXT
                glow_col = PURPLE2
                glow_r   = 6
            elif nid == self.start_node:
                fill, border, tc = ACCENT, ACCENT2, BG
                glow_col = ACCENT2
                glow_r   = 8
            elif nid == self.end_node:
                fill, border, tc = RED, RED2, TEXT
                glow_col = RED2
                glow_r   = 8
            elif nid in self.sel:
                fill, border, tc = YELLOW, YELLOW2, BG
                glow_col = YELLOW2
                glow_r   = 10
            else:
                fill, border, tc = NODE_DEF, NODE_BOR, TEXT2
                glow_col = None
                glow_r   = 0

            # halo/glow
            if glow_col:
                for i in range(3, 0, -1):
                    alpha = i * glow_r // 3
                    c.create_oval(
                        x - R - alpha, y - R - alpha,
                        x + R + alpha, y + R + alpha,
                        fill="", outline=glow_col,
                        width=1
                    )

            # corpo do nó
            c.create_oval(x - R, y - R, x + R, y + R,
                           fill=fill, outline=border, width=2)

            # reflexo sutil no topo
            c.create_oval(x - R + 5, y - R + 4, x + 2, y - 4,
                           fill=self._blend(fill, "#ffffff", 0.15),
                           outline="")

            # label do nó
            c.create_text(x, y, text=str(nid),
                           fill=tc, font=("Consolas", 11, "bold"))

            # distância acima
            if dist_map:
                d = dist_map.get(nid, float('inf'))
                lbl = "∞" if d == float('inf') else str(round(d, 1))
                c.create_text(x, y - R - 10, text=lbl,
                               fill=YELLOW2, font=("Consolas", 8, "bold"))

            # marcadores S / E
            if nid == self.start_node:
                c.create_text(x + R + 10, y - R - 2, text="S",
                               fill=ACCENT2, font=("Consolas", 10, "bold"))
            if nid == self.end_node:
                c.create_text(x + R + 10, y - R - 2, text="E",
                               fill=RED2, font=("Consolas", 10, "bold"))

    def _blend(self, hex1, hex2, ratio):
        """Mistura duas cores hex pelo ratio (0=hex1, 1=hex2)."""
        h1 = hex1.lstrip("#")
        h2 = hex2.lstrip("#")
        r1, g1, b1 = int(h1[0:2], 16), int(h1[2:4], 16), int(h1[4:6], 16)
        r2, g2, b2 = int(h2[0:2], 16), int(h2[2:4], 16), int(h2[4:6], 16)
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        return f"#{r:02x}{g:02x}{b:02x}"


if __name__ == "__main__":
    App().mainloop()
