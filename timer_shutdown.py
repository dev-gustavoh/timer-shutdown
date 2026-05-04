"""
Timer Shutdown
Agende o desligamento, reinicialização ou suspensão do Windows.
Dependências: apenas biblioteca padrão do Python (tkinter).
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import time


# ── Paleta de cores ──────────────────────────────────────────────────────────
BG      = "#1e1e2e"   # fundo geral
SURFACE = "#313244"   # cards/painéis
OVERLAY = "#45475a"   # campos de entrada / botão cancelar
TEXT    = "#cdd6f4"   # texto principal
SUBTEXT = "#a6adc8"   # texto secundário
BLUE    = "#89b4fa"   # cor de destaque (contagem normal)
RED     = "#f38ba8"   # últimos 10 segundos
GREEN   = "#a6e3a1"   # status de cancelado
ORANGE  = "#fab387"   # aviso de 60 segundos


# ── Comandos de sistema para cada ação ──────────────────────────────────────
ACTIONS = {
    "shutdown": {
        "label": "Desligar",
        "status": "desligamento",
        "cmd": ["shutdown", "/s", "/f", "/t", "10",
                "/c", "Timer Shutdown: desligando o computador."],
    },
    "restart": {
        "label": "Reiniciar",
        "status": "reinicialização",
        "cmd": ["shutdown", "/r", "/f", "/t", "10",
                "/c", "Timer Shutdown: reiniciando o computador."],
    },
    "sleep": {
        "label": "Suspender",
        "status": "suspensão",
        # SetSuspendState(Hibernate=0, ForceCritical=1, DisableWakeEvent=0)
        "cmd": ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
    },
}


class TimerShutdownApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self._configure_window()
        self._init_state()
        self._build_ui()

    # ── Configuração da janela ───────────────────────────────────────────────

    def _configure_window(self) -> None:
        self.root.title("Timer Shutdown")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self._center_window(width=430, height=630)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_window(self, width: int, height: int) -> None:
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    # ── Estado interno ───────────────────────────────────────────────────────

    def _init_state(self) -> None:
        self.running       = False
        self.timer_thread  = None
        self.remaining     = 0   # segundos restantes
        self.total         = 0   # total de segundos definidos
        self.warned        = False

    # ── Construção da interface ──────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._build_header()
        self._build_time_input()
        self._build_action_selector()
        self._build_countdown()
        self._build_progress()
        self._build_buttons()

    def _build_header(self) -> None:
        frame = tk.Frame(self.root, bg=BG)
        frame.pack(pady=(26, 10))

        tk.Label(
            frame, text="⏱  Timer Shutdown",
            font=("Segoe UI", 22, "bold"), fg=TEXT, bg=BG,
        ).pack()

        tk.Label(
            frame, text="Agende o desligamento do seu computador",
            font=("Segoe UI", 10), fg=SUBTEXT, bg=BG,
        ).pack(pady=(3, 0))

    def _build_time_input(self) -> None:
        card = self._card(self.root)
        card.pack(pady=6, padx=30, fill="x")

        tk.Label(
            card, text="TEMPO", font=("Segoe UI", 8, "bold"),
            fg=SUBTEXT, bg=SURFACE,
        ).pack(anchor="w", padx=18, pady=(14, 6))

        row = tk.Frame(card, bg=SURFACE)
        row.pack(padx=18, pady=(0, 16))

        self.hours_var   = tk.StringVar(value="0")
        self.minutes_var = tk.StringVar(value="30")
        self.seconds_var = tk.StringVar(value="0")

        # (label, var, field_key, step)
        fields = [
            ("Horas",    self.hours_var,   "h",  1),
            ("Minutos",  self.minutes_var, "m", 30),
            ("Segundos", self.seconds_var, "s", 30),
        ]

        for col_idx, (label, var, field, step) in enumerate(fields):
            col = tk.Frame(row, bg=SURFACE)
            col.grid(row=0, column=col_idx, padx=10)

            tk.Label(
                col, text=label, font=("Segoe UI", 9),
                fg=SUBTEXT, bg=SURFACE,
            ).pack(pady=(0, 2))

            def _arrow_btn(parent, text, f=field, st=step, sign=+1):
                return tk.Button(
                    parent, text=text,
                    font=("Segoe UI", 9, "bold"),
                    fg=SUBTEXT, bg=OVERLAY,
                    activebackground=BLUE, activeforeground=BG,
                    bd=0, width=5, pady=2, cursor="hand2", relief="flat",
                    command=lambda: self._step_time(f, sign * st),
                )

            _arrow_btn(col, "▲", field, step, +1).pack()

            entry = tk.Entry(
                col, textvariable=var,
                width=5, font=("Consolas", 18, "bold"),
                bg=OVERLAY, fg=TEXT, insertbackground=TEXT,
                bd=0, justify="center", relief="flat",
            )
            entry.pack(ipady=8)
            # Scroll do mouse sobre o campo também ajusta o valor
            entry.bind(
                "<MouseWheel>",
                lambda e, f=field, st=step: self._step_time(f, st if e.delta > 0 else -st),
            )

            _arrow_btn(col, "▼", field, step, -1).pack()

    def _build_action_selector(self) -> None:
        card = self._card(self.root)
        card.pack(pady=6, padx=30, fill="x")

        tk.Label(
            card, text="AÇÃO", font=("Segoe UI", 8, "bold"),
            fg=SUBTEXT, bg=SURFACE,
        ).pack(anchor="w", padx=18, pady=(14, 6))

        self.action_var = tk.StringVar(value="shutdown")

        icons = {"shutdown": "🔴", "restart": "🔄", "sleep": "💤"}

        row = tk.Frame(card, bg=SURFACE)
        row.pack(padx=18, pady=(0, 14))

        for key, info in ACTIONS.items():
            tk.Radiobutton(
                row,
                text=f"{icons[key]}  {info['label']}",
                variable=self.action_var,
                value=key,
                font=("Segoe UI", 10),
                fg=TEXT, bg=SURFACE,
                activebackground=SURFACE, activeforeground=BLUE,
                selectcolor=BG, bd=0, padx=4,
            ).pack(side="left", padx=8)

    def _build_countdown(self) -> None:
        frame = tk.Frame(self.root, bg=BG)
        frame.pack(pady=(18, 4))

        self.countdown_var = tk.StringVar(value="00:00:00")
        self.countdown_lbl = tk.Label(
            frame, textvariable=self.countdown_var,
            font=("Consolas", 48, "bold"), fg=BLUE, bg=BG,
        )
        self.countdown_lbl.pack()

        self.status_var = tk.StringVar(value="Aguardando...")
        tk.Label(
            frame, textvariable=self.status_var,
            font=("Segoe UI", 10), fg=SUBTEXT, bg=BG,
        ).pack(pady=(3, 0))

    def _build_progress(self) -> None:
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "App.Horizontal.TProgressbar",
            troughcolor=SURFACE, background=BLUE,
            thickness=6, borderwidth=0,
        )
        self.progress = ttk.Progressbar(
            self.root, style="App.Horizontal.TProgressbar",
            orient="horizontal", length=370, mode="determinate",
        )
        self.progress.pack(pady=6)

    def _build_buttons(self) -> None:
        frame = tk.Frame(self.root, bg=BG)
        frame.pack(pady=20)

        self.start_btn = tk.Button(
            frame, text="▶   Iniciar",
            font=("Segoe UI", 11, "bold"),
            fg=BG, bg=BLUE,
            activebackground="#74c7ec", activeforeground=BG,
            bd=0, padx=28, pady=11, cursor="hand2",
            command=self.start_timer,
        )
        self.start_btn.pack(side="left", padx=8)

        self.cancel_btn = tk.Button(
            frame, text="⏹   Cancelar",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT, bg=OVERLAY,
            activebackground="#585b70", activeforeground=TEXT,
            bd=0, padx=22, pady=11, cursor="hand2",
            state="disabled",
            command=self.cancel_timer,
        )
        self.cancel_btn.pack(side="left", padx=8)

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _card(parent: tk.Widget) -> tk.Frame:
        return tk.Frame(parent, bg=SURFACE, bd=0, relief="flat")

    @staticmethod
    def _fmt(seconds: int) -> str:
        h, rem = divmod(seconds, 3600)
        m, s   = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _step_time(self, field: str, delta: int) -> None:
        """Incrementa/decrementa um campo de tempo propagando carry e borrow entre h, m, s."""
        try:
            h = int(self.hours_var.get())
            m = int(self.minutes_var.get())
            s = int(self.seconds_var.get())
        except ValueError:
            h, m, s = 0, 0, 0

        if field == "h":
            h += delta
        elif field == "m":
            m += delta
        else:
            s += delta

        # Normaliza segundos para [0, 59] com carry/borrow em minutos
        if s >= 60:
            m += s // 60
            s %= 60
        elif s < 0:
            s += 60
            m -= 1

        # Normaliza minutos para [0, 59] com carry/borrow em horas
        if m >= 60:
            h += m // 60
            m %= 60
        elif m < 0:
            m += 60
            h -= 1

        # Horas não vão abaixo de zero
        if h < 0:
            h, m, s = 0, 0, 0

        self.hours_var.set(str(h))
        self.minutes_var.set(str(m))
        self.seconds_var.set(str(s))

    def _parse_time(self):
        """Lê os campos de entrada e retorna o total de segundos, ou None em caso de erro."""
        try:
            h = int(self.hours_var.get())
            m = int(self.minutes_var.get())
            s = int(self.seconds_var.get())

            if any(v < 0 for v in (h, m, s)):
                raise ValueError("Valores negativos não são permitidos.")

            total = h * 3600 + m * 60 + s

            if total <= 0:
                raise ValueError("O tempo total deve ser maior que zero.")

            return total

        except ValueError as exc:
            messagebox.showerror(
                "Entrada inválida",
                f"Verifique os valores informados.\n\n{exc}",
            )
            return None

    # ── Lógica do timer ──────────────────────────────────────────────────────

    def start_timer(self) -> None:
        total = self._parse_time()
        if total is None:
            return

        self.remaining = total
        self.total     = total
        self.running   = True
        self.warned    = False

        action_key = self.action_var.get()
        self.status_var.set(f"⏳ Aguardando {ACTIONS[action_key]['status']}...")
        self.countdown_lbl.config(fg=BLUE)
        self.progress["value"] = 0

        self.start_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")

        self.timer_thread = threading.Thread(target=self._tick_loop, daemon=True)
        self.timer_thread.start()

    def _tick_loop(self) -> None:
        """Executado em thread separada: decrementa o contador a cada segundo."""
        while self.running and self.remaining > 0:
            self.root.after(0, self._refresh_display)
            time.sleep(1)
            if self.running:
                self.remaining -= 1

        if self.running:  # chegou a zero sem cancelamento
            self.root.after(0, self._execute_action)

    def _refresh_display(self) -> None:
        """Atualiza os widgets na thread principal (chamado via root.after)."""
        if not self.running:
            return

        self.countdown_var.set(self._fmt(self.remaining))

        # Barra de progresso (avança conforme o tempo passa)
        if self.total > 0:
            elapsed_pct = (self.total - self.remaining) / self.total * 100
            self.progress["value"] = elapsed_pct

        # Aviso 60 segundos antes do final
        if self.remaining == 60 and not self.warned:
            self.warned = True
            action_key = self.action_var.get()
            status_label = ACTIONS[action_key]["status"].capitalize()
            self.countdown_lbl.config(fg=ORANGE)
            self.status_var.set(f"⚠  {status_label} em 1 minuto!")
            messagebox.showwarning(
                "Aviso — 1 minuto restante",
                f"O {ACTIONS[action_key]['status']} ocorrerá em 60 segundos.\n\n"
                "Clique em  ⏹ Cancelar  para abortar.",
            )

        # Últimos 10 segundos: destaque em vermelho
        if self.remaining <= 10:
            self.countdown_lbl.config(fg=RED)

    def _execute_action(self) -> None:
        """Dispara o comando do sistema ao fim do temporizador."""
        self.running = False
        action_key = self.action_var.get()

        self.countdown_var.set("00:00:00")
        self.status_var.set(f"Executando {ACTIONS[action_key]['status']}...")
        self._reset_buttons()

        subprocess.Popen(ACTIONS[action_key]["cmd"])

    def cancel_timer(self) -> None:
        """Para o temporizador e cancela qualquer shutdown agendado no Windows."""
        self.running = False

        # Cancela shutdown/restart pendente (ignora erro se não houver nenhum)
        subprocess.run(["shutdown", "/a"], capture_output=True)

        self.countdown_var.set("00:00:00")
        self.countdown_lbl.config(fg=BLUE)
        self.status_var.set("✔  Timer cancelado.")
        self.progress["value"] = 0
        self._reset_buttons()

    def _reset_buttons(self) -> None:
        self.start_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")

    # ── Fechar janela ────────────────────────────────────────────────────────

    def _on_close(self) -> None:
        if self.running:
            if not messagebox.askyesno(
                "Sair",
                "O timer ainda está em execução.\nDeseja cancelar e sair?",
            ):
                return
            self.cancel_timer()
        self.root.destroy()


# ── Ponto de entrada ─────────────────────────────────────────────────────────

def main() -> None:
    root = tk.Tk()
    TimerShutdownApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
