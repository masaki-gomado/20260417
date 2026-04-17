# Pomodoro Timer App
"""
カスタマイズ可能なポモドーロタイマーアプリ

機能:
- 作業時間設定: 15/25/35/45分
- 休憩時間設定: 5/10/15分
- テーマ切り替え: ライト / ダーク / フォーカス（ミニマルUI）
- サウンド設定: 開始音 / 終了音 / Tick音 の ON/OFF
"""

import tkinter as tk
from tkinter import ttk
import platform
import threading


# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------
WORK_TIMES = [15, 25, 35, 45]
BREAK_TIMES = [5, 10, 15]

# サウンド関連定数
BEEP_START_FREQ = 880
BEEP_START_DURATION = 150
BEEP_END_FREQ_LO = 660
BEEP_END_FREQ_HI = 880
BEEP_END_DURATION = 400
BEEP_END_DELAY_MS = 500
BEEP_TICK_FREQ = 440
BEEP_TICK_DURATION = 30

THEMES: dict[str, dict] = {
    "light": {
        "bg": "#FFFFFF",
        "fg": "#333333",
        "accent": "#E74C3C",
        "accent_fg": "#FFFFFF",
        "panel_bg": "#F5F5F5",
        "btn_bg": "#E74C3C",
        "btn_fg": "#FFFFFF",
        "btn_hover": "#C0392B",
        "canvas_bg": "#FFFFFF",
        "arc_fg": "#E74C3C",
        "arc_bg": "#EEEEEE",
        "label": "ライト",
    },
    "dark": {
        "bg": "#1E1E2E",
        "fg": "#CDD6F4",
        "accent": "#F38BA8",
        "accent_fg": "#1E1E2E",
        "panel_bg": "#313244",
        "btn_bg": "#F38BA8",
        "btn_fg": "#1E1E2E",
        "btn_hover": "#EBA0AC",
        "canvas_bg": "#1E1E2E",
        "arc_fg": "#F38BA8",
        "arc_bg": "#45475A",
        "label": "ダーク",
    },
    "focus": {
        "bg": "#0D0D0D",
        "fg": "#AAAAAA",
        "accent": "#AAAAAA",
        "accent_fg": "#0D0D0D",
        "panel_bg": "#0D0D0D",
        "btn_bg": "#333333",
        "btn_fg": "#AAAAAA",
        "btn_hover": "#555555",
        "canvas_bg": "#0D0D0D",
        "arc_fg": "#AAAAAA",
        "arc_bg": "#222222",
        "label": "フォーカス",
    },
}


# ---------------------------------------------------------------------------
# サウンドユーティリティ
# ---------------------------------------------------------------------------
def _play_beep(frequency: int = 800, duration_ms: int = 200) -> None:
    """プラットフォームに応じてビープ音を鳴らす（ブロッキングしない）。"""

    def _beep() -> None:
        try:
            if platform.system() == "Windows":
                import winsound  # type: ignore[import]
                winsound.Beep(frequency, duration_ms)
            elif platform.system() == "Darwin":
                import subprocess
                subprocess.run(
                    ["afplay", "/System/Library/Sounds/Tink.aiff"],
                    check=False,
                    capture_output=True,
                )
            else:
                import subprocess
                subprocess.run(
                    ["paplay", "/usr/share/sounds/freedesktop/stereo/audio-volume-change.oga"],
                    check=False,
                    capture_output=True,
                )
        except Exception:
            pass  # サウンドが利用できない環境ではスキップ

    threading.Thread(target=_beep, daemon=True).start()


# ---------------------------------------------------------------------------
# 設定モデル
# ---------------------------------------------------------------------------
class Settings:
    """ユーザー設定を保持するモデル。将来的な設定項目拡張を考慮した構造。"""

    def __init__(self) -> None:
        self.work_minutes: int = 25
        self.break_minutes: int = 5
        self.theme: str = "light"
        self.sound_start: bool = True
        self.sound_end: bool = True
        self.sound_tick: bool = False


# ---------------------------------------------------------------------------
# メインアプリ
# ---------------------------------------------------------------------------
class PomodoroApp:
    CANVAS_SIZE = 260
    ARC_MARGIN = 20
    ARC_WIDTH = 14

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Pomodoro Timer")
        self.root.resizable(False, False)

        self.settings = Settings()

        # タイマー状態
        self._total_seconds: int = self.settings.work_minutes * 60
        self._remaining: int = self._total_seconds
        self._running: bool = False
        self._on_break: bool = False
        self._sessions: int = 0
        self._after_id: str | None = None

        # StringVar / BooleanVar
        self._work_var = tk.IntVar(value=self.settings.work_minutes)
        self._break_var = tk.IntVar(value=self.settings.break_minutes)
        self._theme_var = tk.StringVar(value=self.settings.theme)
        self._sound_start_var = tk.BooleanVar(value=self.settings.sound_start)
        self._sound_end_var = tk.BooleanVar(value=self.settings.sound_end)
        self._sound_tick_var = tk.BooleanVar(value=self.settings.sound_tick)

        self._build_ui()
        self._apply_theme()
        self._refresh_display()

    # ------------------------------------------------------------------
    # UI 構築
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        theme = THEMES[self.settings.theme]

        # ---- ルートフレーム ----
        self.root_frame = tk.Frame(self.root, bg=theme["bg"])
        self.root_frame.pack(fill="both", expand=True)

        # ---- ヘッダー ----
        self.header_frame = tk.Frame(self.root_frame, bg=theme["bg"])
        self.header_frame.pack(fill="x", padx=20, pady=(16, 0))

        self.title_label = tk.Label(
            self.header_frame,
            text="🍅 Pomodoro Timer",
            font=("Helvetica", 16, "bold"),
            bg=theme["bg"],
            fg=theme["fg"],
        )
        self.title_label.pack(side="left")

        self.session_label = tk.Label(
            self.header_frame,
            text="セッション: 0",
            font=("Helvetica", 11),
            bg=theme["bg"],
            fg=theme["fg"],
        )
        self.session_label.pack(side="right")

        # ---- 円形タイマーキャンバス ----
        self.canvas = tk.Canvas(
            self.root_frame,
            width=self.CANVAS_SIZE,
            height=self.CANVAS_SIZE,
            bg=theme["canvas_bg"],
            highlightthickness=0,
        )
        self.canvas.pack(pady=(10, 0))

        # ---- モードラベル（作業 / 休憩） ----
        self.mode_label = tk.Label(
            self.root_frame,
            text="作業",
            font=("Helvetica", 12),
            bg=theme["bg"],
            fg=theme["accent"],
        )
        self.mode_label.pack(pady=(4, 0))

        # ---- コントロールボタン ----
        self.btn_frame = tk.Frame(self.root_frame, bg=theme["bg"])
        self.btn_frame.pack(pady=10)

        self.start_btn = tk.Button(
            self.btn_frame,
            text="▶ 開始",
            font=("Helvetica", 12, "bold"),
            bg=theme["btn_bg"],
            fg=theme["btn_fg"],
            activebackground=theme["btn_hover"],
            activeforeground=theme["btn_fg"],
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self._toggle_timer,
        )
        self.start_btn.pack(side="left", padx=6)

        self.reset_btn = tk.Button(
            self.btn_frame,
            text="↺ リセット",
            font=("Helvetica", 12),
            bg=theme["panel_bg"],
            fg=theme["fg"],
            activebackground=theme["btn_hover"],
            activeforeground=theme["btn_fg"],
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2",
            command=self._reset_timer,
        )
        self.reset_btn.pack(side="left", padx=6)

        # ---- 設定パネル（フォーカスモード時は非表示） ----
        self.settings_frame = tk.Frame(self.root_frame, bg=theme["panel_bg"])
        self.settings_frame.pack(fill="x", padx=20, pady=(8, 16))

        self._build_settings_panel()

    def _build_settings_panel(self) -> None:
        theme = THEMES[self.settings.theme]
        parent = self.settings_frame

        # --- 作業時間 ---
        row0 = tk.Frame(parent, bg=theme["panel_bg"])
        row0.pack(fill="x", padx=12, pady=(10, 4))
        self._create_setting_label(row0, "作業時間", theme)
        for mins in WORK_TIMES:
            rb = tk.Radiobutton(
                row0,
                text=f"{mins}分",
                variable=self._work_var,
                value=mins,
                font=("Helvetica", 10),
                bg=theme["panel_bg"],
                fg=theme["fg"],
                selectcolor=theme["bg"],
                activebackground=theme["panel_bg"],
                cursor="hand2",
                command=self._on_work_time_change,
            )
            rb.pack(side="left", padx=4)

        # --- 休憩時間 ---
        row1 = tk.Frame(parent, bg=theme["panel_bg"])
        row1.pack(fill="x", padx=12, pady=4)
        self._create_setting_label(row1, "休憩時間", theme)
        for mins in BREAK_TIMES:
            rb = tk.Radiobutton(
                row1,
                text=f"{mins}分",
                variable=self._break_var,
                value=mins,
                font=("Helvetica", 10),
                bg=theme["panel_bg"],
                fg=theme["fg"],
                selectcolor=theme["bg"],
                activebackground=theme["panel_bg"],
                cursor="hand2",
                command=self._on_break_time_change,
            )
            rb.pack(side="left", padx=4)

        # --- テーマ ---
        row2 = tk.Frame(parent, bg=theme["panel_bg"])
        row2.pack(fill="x", padx=12, pady=4)
        self._create_setting_label(row2, "テーマ", theme)
        for key, val in THEMES.items():
            rb = tk.Radiobutton(
                row2,
                text=val["label"],
                variable=self._theme_var,
                value=key,
                font=("Helvetica", 10),
                bg=theme["panel_bg"],
                fg=theme["fg"],
                selectcolor=theme["bg"],
                activebackground=theme["panel_bg"],
                cursor="hand2",
                command=self._on_theme_change,
            )
            rb.pack(side="left", padx=4)

        # --- サウンド設定 ---
        row3 = tk.Frame(parent, bg=theme["panel_bg"])
        row3.pack(fill="x", padx=12, pady=(4, 10))
        self._create_setting_label(row3, "サウンド", theme)
        for label, var in [("開始音", self._sound_start_var), ("終了音", self._sound_end_var), ("Tick音", self._sound_tick_var)]:
            cb = tk.Checkbutton(
                row3,
                text=label,
                variable=var,
                font=("Helvetica", 10),
                bg=theme["panel_bg"],
                fg=theme["fg"],
                selectcolor=theme["bg"],
                activebackground=theme["panel_bg"],
                cursor="hand2",
                command=self._on_sound_change,
            )
            cb.pack(side="left", padx=4)

    @staticmethod
    def _create_setting_label(parent: tk.Frame, text: str, theme: dict) -> None:
        """設定行のラベルを統一されたスタイルで作成する。"""
        tk.Label(
            parent,
            text=text,
            font=("Helvetica", 10),
            bg=theme["panel_bg"],
            fg=theme["fg"],
            width=12,
            anchor="w",
        ).pack(side="left")


    # ------------------------------------------------------------------
    # テーマ適用
    # ------------------------------------------------------------------
    def _apply_theme(self) -> None:
        theme = THEMES[self.settings.theme]
        is_focus = self.settings.theme == "focus"

        self.root.configure(bg=theme["bg"])
        self.root_frame.configure(bg=theme["bg"])
        self.header_frame.configure(bg=theme["bg"])
        self.title_label.configure(bg=theme["bg"], fg=theme["fg"])
        self.session_label.configure(bg=theme["bg"], fg=theme["fg"])
        self.canvas.configure(bg=theme["canvas_bg"])
        self.mode_label.configure(bg=theme["bg"], fg=theme["accent"])
        self.btn_frame.configure(bg=theme["bg"])
        self.start_btn.configure(bg=theme["btn_bg"], fg=theme["btn_fg"], activebackground=theme["btn_hover"])
        self.reset_btn.configure(bg=theme["panel_bg"], fg=theme["fg"], activebackground=theme["btn_hover"])

        # フォーカスモードは設定パネルを非表示
        if is_focus:
            self.settings_frame.pack_forget()
        else:
            self.settings_frame.pack(fill="x", padx=20, pady=(8, 16))
            # 設定パネル内ウィジェットの再構築（テーマ色を更新）
            for widget in self.settings_frame.winfo_children():
                widget.destroy()
            self._build_settings_panel()

        self._refresh_display()

    # ------------------------------------------------------------------
    # タイマー描画
    # ------------------------------------------------------------------
    def _refresh_display(self) -> None:
        theme = THEMES[self.settings.theme]
        self.canvas.delete("all")

        cx = cy = self.CANVAS_SIZE // 2
        r = cx - self.ARC_MARGIN

        # 背景円弧
        x0, y0 = cx - r, cy - r
        x1, y1 = cx + r, cy + r
        self.canvas.create_arc(
            x0, y0, x1, y1,
            start=90, extent=360,
            style="arc",
            outline=theme["arc_bg"],
            width=self.ARC_WIDTH,
        )

        # 進捗円弧
        ratio = self._remaining / self._total_seconds if self._total_seconds > 0 else 0
        extent = ratio * 360
        if extent > 0:
            self.canvas.create_arc(
                x0, y0, x1, y1,
                start=90, extent=extent,
                style="arc",
                outline=theme["arc_fg"],
                width=self.ARC_WIDTH,
            )

        # 時間テキスト
        mins, secs = divmod(self._remaining, 60)
        time_str = f"{mins:02d}:{secs:02d}"
        self.canvas.create_text(
            cx, cy - 10,
            text=time_str,
            font=("Helvetica", 42, "bold"),
            fill=theme["fg"],
        )

        # モード補助テキスト
        mode_text = "☕ 休憩中" if self._on_break else "🍅 作業中"
        self.canvas.create_text(
            cx, cy + 34,
            text=mode_text,
            font=("Helvetica", 12),
            fill=theme["accent"],
        )

        # セッション数更新
        self.session_label.configure(text=f"セッション: {self._sessions}")

        # モードラベル更新
        self.mode_label.configure(text="☕ 休憩" if self._on_break else "🍅 作業")

    # ------------------------------------------------------------------
    # タイマーロジック
    # ------------------------------------------------------------------
    def _toggle_timer(self) -> None:
        if self._running:
            self._pause_timer()
        else:
            self._start_timer()

    def _start_timer(self) -> None:
        if self.settings.sound_start:
            _play_beep(BEEP_START_FREQ, BEEP_START_DURATION)
        self._running = True
        self.start_btn.configure(text="⏸ 一時停止")
        self._tick()

    def _pause_timer(self) -> None:
        self._running = False
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self.start_btn.configure(text="▶ 再開")

    def _reset_timer(self) -> None:
        self._running = False
        self._on_break = False
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self._total_seconds = self.settings.work_minutes * 60
        self._remaining = self._total_seconds
        self.start_btn.configure(text="▶ 開始")
        self._refresh_display()

    def _tick(self) -> None:
        if not self._running:
            return

        if self.settings.sound_tick:
            _play_beep(BEEP_TICK_FREQ, BEEP_TICK_DURATION)

        if self._remaining <= 0:
            self._on_timer_end()
            return

        self._remaining -= 1
        self._refresh_display()
        self._after_id = self.root.after(1000, self._tick)

    def _on_timer_end(self) -> None:
        self._running = False
        self.start_btn.configure(text="▶ 開始")

        if self.settings.sound_end:
            _play_beep(BEEP_END_FREQ_LO, BEEP_END_DURATION)
            self.root.after(BEEP_END_DELAY_MS, lambda: _play_beep(BEEP_END_FREQ_HI, BEEP_END_DURATION))

        if not self._on_break:
            # 作業終了 → 休憩へ
            self._sessions += 1
            self._on_break = True
            self._total_seconds = self.settings.break_minutes * 60
        else:
            # 休憩終了 → 作業へ
            self._on_break = False
            self._total_seconds = self.settings.work_minutes * 60

        self._remaining = self._total_seconds
        self._refresh_display()

    # ------------------------------------------------------------------
    # 設定変更コールバック
    # ------------------------------------------------------------------
    def _on_work_time_change(self) -> None:
        self.settings.work_minutes = self._work_var.get()
        if not self._running and not self._on_break:
            self._total_seconds = self.settings.work_minutes * 60
            self._remaining = self._total_seconds
            self._refresh_display()

    def _on_break_time_change(self) -> None:
        self.settings.break_minutes = self._break_var.get()
        if not self._running and self._on_break:
            self._total_seconds = self.settings.break_minutes * 60
            self._remaining = self._total_seconds
            self._refresh_display()

    def _on_theme_change(self) -> None:
        self.settings.theme = self._theme_var.get()
        self._apply_theme()

    def _on_sound_change(self) -> None:
        self.settings.sound_start = self._sound_start_var.get()
        self.settings.sound_end = self._sound_end_var.get()
        self.settings.sound_tick = self._sound_tick_var.get()


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------
def main() -> None:
    root = tk.Tk()
    root.geometry("480x600")
    app = PomodoroApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
