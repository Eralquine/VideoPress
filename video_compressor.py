#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, threading, os, sys, json
from pathlib import Path
from datetime import datetime

def _get_bin(name):
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, name)

FFMPEG_BIN  = _get_bin("ffmpeg.exe")
FFPROBE_BIN = _get_bin("ffprobe.exe")

BG_DARK="#0d0f14"; BG_CARD="#161921"; BG_INPUT="#1e2230"
ACCENT="#00d4aa"; ACCENT_DIM="#00a882"; TEXT_PRIMARY="#e8eaf0"
TEXT_MUTED="#6b7280"; TEXT_SUCCESS="#4ade80"; TEXT_ERROR="#f87171"
TEXT_WARN="#fbbf24"; BORDER="#2a2f3d"

NO_WIN = subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0

class VideoCompressor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VideoPress — Compresor MP4")
        self.geometry("820x700"); self.minsize(700,620)
        self.configure(bg=BG_DARK); self.resizable(True,True)
        self.files=[]; self.is_running=False; self.current_proc=None
        self.output_dir=tk.StringVar(); self.crf_var=tk.IntVar(value=28)
        self.preset_var=tk.StringVar(value="medium")
        self.overwrite_var=tk.BooleanVar(value=False)
        self.suffix_var=tk.StringVar(value="_compressed")
        self._check_ffmpeg(); self._build_ui()

    def _check_ffmpeg(self):
        try: subprocess.run([FFMPEG_BIN,"-version"],capture_output=True,check=True); self.ffmpeg_ok=True
        except: self.ffmpeg_ok=False

    def _build_ui(self):
        hdr=tk.Frame(self,bg=BG_DARK,pady=18); hdr.pack(fill="x",padx=24)
        tk.Label(hdr,text="▶ VideoPress",font=("Courier New",22,"bold"),bg=BG_DARK,fg=ACCENT).pack(side="left")
        tk.Label(hdr,text="compresor MP4 con ffmpeg",font=("Courier New",10),bg=BG_DARK,fg=TEXT_MUTED).pack(side="left",padx=12,pady=6)
        if not self.ffmpeg_ok:
            tk.Label(hdr,text="⚠ ffmpeg no encontrado",font=("Courier New",10,"bold"),bg=BG_DARK,fg=TEXT_ERROR).pack(side="right")
        tk.Label(hdr,text="by Ernesto Quintanilla",font=("Courier New",8),bg=BG_DARK,fg=TEXT_MUTED).pack(side="right",padx=12)
        ttk.Separator(self,orient="horizontal").pack(fill="x",padx=24)
        main=tk.Frame(self,bg=BG_DARK); main.pack(fill="both",expand=True,padx=24,pady=12)
        main.columnconfigure(0,weight=3); main.columnconfigure(1,weight=2); main.rowconfigure(0,weight=1)
        self._build_left(main); self._build_right(main); self._build_log(); self._build_bottom()

    def _card(self,parent,title,**kw):
        f=tk.Frame(parent,bg=BG_CARD,highlightbackground=BORDER,highlightthickness=1)
        f.grid(**kw,sticky="nsew",padx=(0,6),pady=4)
        tk.Label(f,text=title,font=("Courier New",9,"bold"),bg=BG_CARD,fg=ACCENT).pack(anchor="w",padx=12,pady=(10,4))
        ttk.Separator(f,orient="horizontal").pack(fill="x",padx=8)
        return f

    def _build_left(self,parent):
        card=self._card(parent,"📁  ARCHIVOS",row=0,column=0)
        br=tk.Frame(card,bg=BG_CARD); br.pack(fill="x",padx=10,pady=8)
        self._btn(br,"+ Archivo",self._add_file).pack(side="left",padx=(0,6))
        self._btn(br,"+ Carpeta",self._add_folder).pack(side="left",padx=(0,6))
        self._btn(br,"✕ Limpiar",self._clear_files,danger=True).pack(side="right")
        lf=tk.Frame(card,bg=BG_CARD); lf.pack(fill="both",expand=True,padx=10,pady=(0,8))
        cols=("archivo","tamaño","estado")
        self.tree=ttk.Treeview(lf,columns=cols,show="headings",height=10,selectmode="extended")
        self.tree.heading("archivo",text="Archivo"); self.tree.heading("tamaño",text="Tamaño"); self.tree.heading("estado",text="Estado")
        self.tree.column("archivo",width=200,stretch=True); self.tree.column("tamaño",width=80,stretch=False,anchor="e"); self.tree.column("estado",width=100,stretch=False,anchor="center")
        sb=ttk.Scrollbar(lf,orient="vertical",command=self.tree.yview); self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")
        self._style_tree(); self.tree.bind("<Delete>",self._remove_selected)
        of=tk.Frame(card,bg=BG_CARD); of.pack(fill="x",padx=10,pady=(0,10))
        tk.Label(of,text="Carpeta de salida:",font=("Courier New",9),bg=BG_CARD,fg=TEXT_MUTED).pack(anchor="w")
        r2=tk.Frame(of,bg=BG_CARD); r2.pack(fill="x",pady=4)
        tk.Entry(r2,textvariable=self.output_dir,bg=BG_INPUT,fg=TEXT_PRIMARY,insertbackground=ACCENT,relief="flat",font=("Courier New",9),highlightbackground=BORDER,highlightthickness=1).pack(side="left",fill="x",expand=True)
        self._btn(r2,"…",self._choose_out,small=True).pack(side="left",padx=(4,0))

    def _build_right(self,parent):
        card=self._card(parent,"⚙  CONFIGURACIÓN",row=0,column=1)
        inn=tk.Frame(card,bg=BG_CARD); inn.pack(fill="both",expand=True,padx=12,pady=8)
        tk.Label(inn,text="Calidad CRF  (18=alta · 28=media · 40=baja)",font=("Courier New",8),bg=BG_CARD,fg=TEXT_MUTED).pack(anchor="w",pady=(4,0))
        cr=tk.Frame(inn,bg=BG_CARD); cr.pack(fill="x",pady=4)
        self.crf_lbl=tk.Label(cr,text="28",font=("Courier New",18,"bold"),bg=BG_CARD,fg=ACCENT,width=3); self.crf_lbl.pack(side="left")
        tk.Scale(cr,from_=18,to=51,orient="horizontal",variable=self.crf_var,bg=BG_CARD,fg=TEXT_PRIMARY,troughcolor=BG_INPUT,activebackground=ACCENT,highlightthickness=0,bd=0,showvalue=False,command=lambda v:self.crf_lbl.config(text=str(int(float(v))))).pack(side="left",fill="x",expand=True,padx=8)
        tk.Label(inn,text="Velocidad de codificación",font=("Courier New",8),bg=BG_CARD,fg=TEXT_MUTED).pack(anchor="w",pady=(10,0))
        ttk.Combobox(inn,textvariable=self.preset_var,values=["ultrafast","superfast","veryfast","faster","fast","medium","slow","slower","veryslow"],state="readonly",font=("Courier New",9)).pack(fill="x",pady=4)
        tk.Label(inn,text="Sufijo del archivo de salida",font=("Courier New",8),bg=BG_CARD,fg=TEXT_MUTED).pack(anchor="w",pady=(10,0))
        tk.Entry(inn,textvariable=self.suffix_var,bg=BG_INPUT,fg=TEXT_PRIMARY,insertbackground=ACCENT,relief="flat",font=("Courier New",9),highlightbackground=BORDER,highlightthickness=1).pack(fill="x",pady=4)
        tk.Label(inn,text="Opciones",font=("Courier New",8),bg=BG_CARD,fg=TEXT_MUTED).pack(anchor="w",pady=(10,0))
        tk.Checkbutton(inn,text="Sobrescribir si existe",variable=self.overwrite_var,bg=BG_CARD,fg=TEXT_PRIMARY,selectcolor=BG_INPUT,activebackground=BG_CARD,font=("Courier New",9),cursor="hand2").pack(anchor="w",pady=2)
        ttk.Separator(inn,orient="horizontal").pack(fill="x",pady=10)
        tk.Label(inn,text="Reducción estimada según CRF:",font=("Courier New",8),bg=BG_CARD,fg=TEXT_MUTED).pack(anchor="w")
        self.est_lbl=tk.Label(inn,text="~40–60%",font=("Courier New",14,"bold"),bg=BG_CARD,fg=TEXT_WARN); self.est_lbl.pack(anchor="w",pady=4)
        self.crf_var.trace_add("write",self._upd_est)

    def _build_log(self):
        lc=tk.Frame(self,bg=BG_CARD,highlightbackground=BORDER,highlightthickness=1); lc.pack(fill="x",padx=24,pady=(0,4))
        tk.Label(lc,text="📋  LOG",font=("Courier New",9,"bold"),bg=BG_CARD,fg=ACCENT).pack(anchor="w",padx=12,pady=(8,2))
        ttk.Separator(lc,orient="horizontal").pack(fill="x",padx=8)
        self.log=tk.Text(lc,height=6,bg=BG_DARK,fg=TEXT_MUTED,font=("Courier New",8),relief="flat",state="disabled",wrap="word")
        sb=ttk.Scrollbar(lc,orient="vertical",command=self.log.yview); self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left",fill="x",expand=True,padx=8,pady=6); sb.pack(side="right",fill="y",pady=6)
        self.log.tag_config("ok",foreground=TEXT_SUCCESS); self.log.tag_config("err",foreground=TEXT_ERROR)
        self.log.tag_config("info",foreground=ACCENT); self.log.tag_config("warn",foreground=TEXT_WARN)

    def _build_bottom(self):
        bot=tk.Frame(self,bg=BG_DARK); bot.pack(fill="x",padx=24,pady=(4,16))
        pf=tk.Frame(bot,bg=BG_DARK); pf.pack(fill="x",pady=(0,8))
        self.pvar=tk.DoubleVar()
        ttk.Progressbar(pf,variable=self.pvar,maximum=100,mode="determinate").pack(fill="x")
        self.plbl=tk.Label(pf,text="Listo",font=("Courier New",8),bg=BG_DARK,fg=TEXT_MUTED); self.plbl.pack(anchor="w")
        br=tk.Frame(bot,bg=BG_DARK); br.pack(fill="x")
        self.start_btn=self._btn(br,"▶  INICIAR COMPRESIÓN",self._start,primary=True); self.start_btn.pack(side="left")
        self.stop_btn=self._btn(br,"■  DETENER",self._stop,danger=True); self.stop_btn.pack(side="left",padx=8); self.stop_btn.config(state="disabled")
        self.stat_lbl=tk.Label(br,text="",font=("Courier New",9,"bold"),bg=BG_DARK,fg=TEXT_SUCCESS); self.stat_lbl.pack(side="right")

    def _btn(self,parent,text,cmd,primary=False,danger=False,small=False):
        bg=ACCENT if primary else("#3d1a1a"if danger else BG_INPUT)
        fg=BG_DARK if primary else(TEXT_ERROR if danger else TEXT_PRIMARY)
        abg=ACCENT_DIM if primary else("#5a2020"if danger else BORDER)
        return tk.Button(parent,text=text,command=cmd,bg=bg,fg=fg,activebackground=abg,activeforeground=fg,font=("Courier New",8 if small else 9,"bold"if primary else"normal"),relief="flat",cursor="hand2",padx=8 if small else 14,pady=3 if small else 7,bd=0)

    def _style_tree(self):
        s=ttk.Style(self); s.theme_use("clam")
        s.configure("Treeview",background=BG_INPUT,foreground=TEXT_PRIMARY,rowheight=24,fieldbackground=BG_INPUT,font=("Courier New",8),borderwidth=0)
        s.configure("Treeview.Heading",background=BG_CARD,foreground=ACCENT,font=("Courier New",8,"bold"),relief="flat")
        s.map("Treeview",background=[("selected",ACCENT_DIM)])
        s.configure("TProgressbar",troughcolor=BG_INPUT,background=ACCENT,borderwidth=0,thickness=8)
        s.configure("TCombobox",fieldbackground=BG_INPUT,background=BG_INPUT,foreground=TEXT_PRIMARY)
        s.map("TCombobox",fieldbackground=[("readonly",BG_INPUT)])

    def _add_file(self):
        for p in filedialog.askopenfilenames(title="Seleccionar MP4",filetypes=[("MP4","*.mp4"),("Video","*.mp4 *.mkv *.mov *.avi")]):
            self._add_path(p)

    def _add_folder(self):
        d=filedialog.askdirectory(title="Seleccionar carpeta")
        if d:
            for f in Path(d).rglob("*.mp4"): self._add_path(str(f))

    def _add_path(self,path):
        if any(f["path"]==path for f in self.files): return
        sz=os.path.getsize(path)
        self.files.append({"path":path,"status":"pendiente","size_orig":sz,"size_out":0})
        self.tree.insert("","end",values=(Path(path).name,self._fs(sz),"⏳ pendiente"),iid=path)

    def _remove_selected(self,_=None):
        for iid in self.tree.selection(): self.tree.delete(iid); self.files=[f for f in self.files if f["path"]!=iid]

    def _clear_files(self): self.tree.delete(*self.tree.get_children()); self.files.clear()

    def _choose_out(self):
        d=filedialog.askdirectory()
        if d: self.output_dir.set(d)

    def _upd_est(self,*_):
        c=self.crf_var.get()
        self.est_lbl.config(text="~10–25%"if c<=22 else"~30–55%"if c<=28 else"~55–75%"if c<=35 else"~70–85%")

    def _log(self,msg,tag="info"):
        ts=datetime.now().strftime("%H:%M:%S")
        self.log.config(state="normal"); self.log.insert("end",f"[{ts}] {msg}\n",tag); self.log.see("end"); self.log.config(state="disabled")

    def _start(self):
        if not self.ffmpeg_ok:
            messagebox.showerror("Error","ffmpeg.exe no encontrado junto a la app."); return
        pending=[f for f in self.files if f["status"]=="pendiente"]
        if not pending: messagebox.showinfo("Sin archivos","Agrega archivos MP4 primero."); return
        self.is_running=True; self.start_btn.config(state="disabled"); self.stop_btn.config(state="normal"); self.stat_lbl.config(text="")
        threading.Thread(target=self._batch,args=(pending,),daemon=True).start()

    def _stop(self):
        self.is_running=False
        if self.current_proc: self.current_proc.terminate()
        self._log("Detenido por el usuario.","warn")

    def _batch(self,files):
        total=len(files); done=0; saved=0
        for e in files:
            if not self.is_running: break
            self._log(f"Procesando: {Path(e['path']).name}","info")
            self._upd_row(e["path"],"⚙ procesando...")
            out=self._out_path(e["path"])
            ok,_=self._compress(e["path"],out)
            done+=1
            if ok and os.path.exists(out):
                e["status"]="listo"; e["size_out"]=os.path.getsize(out)
                pct=(1-e["size_out"]/e["size_orig"])*100; saved+=e["size_orig"]-e["size_out"]
                self._upd_row(e["path"],f"✅ -{pct:.0f}%",f"{self._fs(e['size_orig'])} → {self._fs(e['size_out'])}")
                self._log(f"✓ {Path(e['path']).name}  {self._fs(e['size_orig'])} → {self._fs(e['size_out'])}  (-{pct:.0f}%)","ok")
            else:
                e["status"]="error"; self._upd_row(e["path"],"❌ error"); self._log(f"✗ Error: {Path(e['path']).name}","err")
            self.pvar.set(done/total*100); self.plbl.config(text=f"{done}/{total} archivos  •  Ahorrado: {self._fs(saved)}")
        self.is_running=False; self.after(0,self._finish,done,total,saved)

    def _compress(self,src,dst):
        import re, time
        cmd=[FFMPEG_BIN,"-y"if self.overwrite_var.get()else"-n","-i",src,
             "-c:v","libx264","-crf",str(self.crf_var.get()),
             "-preset",self.preset_var.get(),
             "-c:a","aac","-b:a","128k","-movflags","+faststart",
             "-stats_period","2",dst]
        try:
            self.current_proc=subprocess.Popen(
                cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,
                universal_newlines=True,creationflags=NO_WIN)
            dur=self._dur(src)
            self.after(0,self._log,f"Duracion total: {int(dur//60)}m {int(dur%60)}s","info")
            self.after(0,self._log,f"Guardando en: {dst}","info")
            pat=re.compile(r"frame=\s*(\d+).*?fps=\s*([\d.]+).*?time=([\d:]+\.[\d]+).*?speed=\s*([\d.]+)x")
            last_log=0.0
            for line in self.current_proc.stderr:
                if not self.is_running: break
                m=pat.search(line.strip())
                if m:
                    frame,fps,tstr,speed=m.group(1),m.group(2),m.group(3),m.group(4)
                    try:
                        p=tstr.split(":")
                        secs=int(p[0])*3600+int(p[1])*60+float(p[2])
                        pct=min(secs/dur*100,99) if dur>0 else 0
                        self.after(0,self.pvar.set,pct)
                        sp=float(speed)
                        rem_s=int((dur-secs)/sp) if sp>0 and dur>0 else 0
                        rem=f"{rem_s//60}m{rem_s%60:02d}s"
                        self.after(0,self.plbl.config,{"text":f"Progreso: {pct:.0f}%  |  frame={frame}  fps={fps}  speed={speed}x  |  restante ~{rem}"})
                        now=time.time()
                        if now-last_log>=5:
                            self.after(0,self._log,f"⏱ {pct:.0f}%  tiempo={tstr}  fps={fps}  speed={speed}x  ~{rem} restante","info")
                            last_log=now
                    except:
                        pass
            self.current_proc.wait()
            rc=self.current_proc.returncode
            if rc!=0:
                self.after(0,self._log,f"ffmpeg termino con codigo: {rc}","err")
            return rc==0,0
        except Exception as ex:
            self.after(0,self._log,str(ex),"err")
            return False,0


    def _dur(self,path):
        try:
            r=subprocess.run([FFPROBE_BIN,"-v","quiet","-print_format","json","-show_format",path],capture_output=True,text=True,creationflags=NO_WIN)
            return float(json.loads(r.stdout)["format"]["duration"])
        except: return 0.0

    def _out_path(self,src):
        p=Path(src); suf=self.suffix_var.get()or"_compressed"; od=self.output_dir.get()or str(p.parent)
        return str(Path(od)/f"{p.stem}{suf}{p.suffix}")

    def _upd_row(self,path,status,size=""):
        try:
            v=list(self.tree.item(path,"values")); v[2]=status
            if size: v[1]=size
            self.tree.item(path,values=v)
        except: pass

    def _finish(self,done,total,saved):
        self.start_btn.config(state="normal"); self.stop_btn.config(state="disabled")
        self.pvar.set(100); self.plbl.config(text=f"Completado: {done}/{total}")
        self.stat_lbl.config(text=f"💾 Ahorrado: {self._fs(saved)}")
        self._log(f"═══ Terminado: {done}/{total} · Ahorrado: {self._fs(saved)} ═══","ok")

    @staticmethod
    def _fs(b):
        for u in("B","KB","MB","GB"):
            if b<1024: return f"{b:.1f} {u}"
            b/=1024
        return f"{b:.1f} TB"

if __name__=="__main__":
    VideoCompressor().mainloop()
