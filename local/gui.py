"""
Aplicativo Desktop para Gerenciador de Senhas
Interface gráfica usando Tkinter
"""
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
from typing import Optional, Tuple
import importlib.util


backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, backend_dir)
from password_generator import PasswordGenerator


sys.path.remove(backend_dir)


local_dir = os.path.dirname(os.path.abspath(__file__))
local_password_manager_path = os.path.join(local_dir, 'password_manager.py')

spec = importlib.util.spec_from_file_location("local_password_manager", local_password_manager_path)
local_password_manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local_password_manager)

JSONPasswordManager = local_password_manager.JSONPasswordManager
PasswordEntry = local_password_manager.PasswordEntry


class PasswordManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Senhas")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        
        self.pm: Optional[JSONPasswordManager] = None
        self.current_entries = []
        
        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        self.show_login_screen()
    
    def show_login_screen(self):
        """Mostra a tela de login/autenticação"""
        # Limpa a janela
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            main_frame, 
            text="🔐 Gerenciador de Senhas", 
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=20)
        
        # Verifica se existe arquivo
        json_file = "passwords.json"
        file_exists = os.path.exists(json_file)
        
        if not file_exists:
            # Frame para importar ou criar novo
            choice_frame = ttk.Frame(main_frame)
            choice_frame.pack(pady=20)
            
            ttk.Label(
                choice_frame,
                text="Nenhum arquivo de senhas encontrado.",
                font=("Arial", 12)
            ).pack(pady=10)
            
            button_frame = ttk.Frame(choice_frame)
            button_frame.pack(pady=10)
            
            ttk.Button(
                button_frame,
                text="Importar Wallet",
                command=self.import_wallet,
                width=20
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                button_frame,
                text="Criar Novo",
                command=self.create_new_wallet,
                width=20
            ).pack(side=tk.LEFT, padx=5)
        else:
            # Frame de login
            login_frame = ttk.LabelFrame(main_frame, text="Login", padding="20")
            login_frame.pack(pady=20)
            
            ttk.Label(login_frame, text="Senha Mestra:", font=("Arial", 11)).pack(anchor=tk.W, pady=5)
            self.password_entry = ttk.Entry(login_frame, show="•", width=30, font=("Arial", 11))
            self.password_entry.pack(pady=5)
            self.password_entry.bind('<Return>', lambda e: self.login())
            
            button_frame = ttk.Frame(login_frame)
            button_frame.pack(pady=10)
            
            ttk.Button(
                button_frame,
                text="Entrar",
                command=self.login,
                width=15
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                button_frame,
                text="Importar Wallet",
                command=self.import_wallet,
                width=15
            ).pack(side=tk.LEFT, padx=5)
    
    def import_wallet(self):
        """Importa uma wallet de um arquivo JSON"""
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo wallet para importar",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Solicita senha mestra do arquivo importado
        password = simpledialog.askstring(
            "Senha Mestra",
            "Digite a senha mestra do arquivo a ser importado:",
            show="•"
        )
        
        if not password:
            return
        
        try:
            imported_entries = JSONPasswordManager.import_from_json(file_path, password)
            
            if imported_entries:
                # Cria o gerenciador com a senha do import
                self.pm = JSONPasswordManager(password)
                self.pm.import_entries(imported_entries)
                messagebox.showinfo(
                    "Sucesso",
                    f"{len(imported_entries)} senha(s) importada(s) com sucesso!"
                )
                self.show_main_screen()
            else:
                messagebox.showwarning("Aviso", "Nenhuma senha encontrada no arquivo.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao importar: {str(e)}")
    
    def create_new_wallet(self):
        """Cria uma nova wallet"""
        password = simpledialog.askstring(
            "Nova Senha Mestra",
            "Digite uma senha mestra para criar o arquivo:",
            show="•"
        )
        
        if not password:
            return
        
        try:
            self.pm = JSONPasswordManager(password)
            messagebox.showinfo("Sucesso", "Arquivo criado com sucesso!")
            self.show_main_screen()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar arquivo: {str(e)}")
    
    def login(self):
        """Faz login com a senha mestra"""
        password = self.password_entry.get()
        
        if not password:
            messagebox.showwarning("Aviso", "Digite a senha mestra.")
            return
        
        try:
            self.pm = JSONPasswordManager(password)
            self.show_main_screen()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao fazer login: {str(e)}")
            self.password_entry.delete(0, tk.END)
    
    def show_main_screen(self):
        """Mostra a tela principal com a lista de senhas"""
        # Limpa a janela
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Importar Wallet", command=self.import_wallet)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)
        
        # Menu Senhas
        password_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Senhas", menu=password_menu)
        password_menu.add_command(label="Nova Senha", command=self.create_password_dialog)
        password_menu.add_command(label="Gerar Senha de Teste", command=self.generate_test_password)
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Barra de ferramentas
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar, text="➕ Nova Senha", command=self.create_password_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="👁️ Ver Senha", command=self.view_password_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Editar", command=self.edit_password_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Deletar", command=self.delete_password_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 Atualizar", command=self.refresh_list).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🚪 Sair", command=self.logout).pack(side=tk.RIGHT, padx=2)
        
        # Frame para lista
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview para lista de senhas
        columns = ("ID", "Título", "Site", "Tamanho", "Entropia", "Nível", "Expiração")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # Configura colunas
        self.tree.heading("ID", text="ID")
        self.tree.heading("Título", text="Título")
        self.tree.heading("Site", text="Site")
        self.tree.heading("Tamanho", text="Tamanho")
        self.tree.heading("Entropia", text="Entropia")
        self.tree.heading("Nível", text="Nível")
        self.tree.heading("Expiração", text="Expiração")
        
        self.tree.column("ID", width=50, anchor=tk.CENTER)
        self.tree.column("Título", width=150)
        self.tree.column("Site", width=200)
        self.tree.column("Tamanho", width=80, anchor=tk.CENTER)
        self.tree.column("Entropia", width=100, anchor=tk.CENTER)
        self.tree.column("Nível", width=120)
        self.tree.column("Expiração", width=120, anchor=tk.CENTER)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind duplo clique
        self.tree.bind('<Double-1>', lambda e: self.view_password_dialog())
        
        # Atualiza lista
        self.refresh_list()
    
    def refresh_list(self):
        """Atualiza a lista de senhas"""
        # Limpa a árvore
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.pm:
            return
        
        # Carrega senhas
        self.current_entries = self.pm.get_all_passwords()
        
        # Adiciona à árvore
        for entry in self.current_entries:
            entropy_level = PasswordGenerator.get_entropy_level(entry.entropy)
            expiration = entry.expiration_date.strftime("%Y-%m-%d") if entry.expiration_date else "N/A"
            
            self.tree.insert(
                "",
                tk.END,
                values=(
                    entry.id,
                    entry.title,
                    entry.site,
                    entry.length,
                    f"{entry.entropy:.2f}",
                    entropy_level,
                    expiration
                )
            )
    
    def get_selected_entry(self) -> Optional[PasswordEntry]:
        """Retorna a entrada selecionada"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma senha da lista.")
            return None
        
        item = self.tree.item(selection[0])
        entry_id = item['values'][0]
        
        result = self.pm.get_password(entry_id)
        if result:
            return result[0]
        return None
    
    def create_password_dialog(self):
        """Diálogo para criar nova senha"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Nova Senha")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(frame, text="Título:", font=("Arial", 11)).pack(anchor=tk.W, pady=5)
        title_entry = ttk.Entry(frame, width=40, font=("Arial", 11))
        title_entry.pack(fill=tk.X, pady=5)
        
        # Site
        ttk.Label(frame, text="Site:", font=("Arial", 11)).pack(anchor=tk.W, pady=5)
        site_entry = ttk.Entry(frame, width=40, font=("Arial", 11))
        site_entry.pack(fill=tk.X, pady=5)
        
        # Opções de senha
        password_frame = ttk.LabelFrame(frame, text="Opções de Senha", padding="10")
        password_frame.pack(fill=tk.X, pady=10)
        
        use_custom = tk.BooleanVar()
        ttk.Checkbutton(
            password_frame,
            text="Usar senha customizada",
            variable=use_custom
        ).pack(anchor=tk.W, pady=5)
        
        ttk.Label(password_frame, text="Senha customizada:", font=("Arial", 10)).pack(anchor=tk.W, pady=5)
        custom_password_entry = ttk.Entry(password_frame, show="•", width=40, font=("Arial", 11))
        custom_password_entry.pack(fill=tk.X, pady=5)
        
        # Opções de geração
        gen_frame = ttk.LabelFrame(password_frame, text="Geração Automática", padding="10")
        gen_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(gen_frame, text="Tamanho:", font=("Arial", 10)).pack(anchor=tk.W, pady=2)
        length_var = tk.StringVar(value="16")
        length_spin = ttk.Spinbox(gen_frame, from_=8, to=128, textvariable=length_var, width=10)
        length_spin.pack(anchor=tk.W, pady=2)
        
        use_uppercase = tk.BooleanVar(value=True)
        use_lowercase = tk.BooleanVar(value=True)
        use_digits = tk.BooleanVar(value=True)
        use_special = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(gen_frame, text="Maiúsculas", variable=use_uppercase).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(gen_frame, text="Minúsculas", variable=use_lowercase).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(gen_frame, text="Dígitos", variable=use_digits).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(gen_frame, text="Especiais", variable=use_special).pack(anchor=tk.W, pady=2)
        
        # Data de expiração
        ttk.Label(frame, text="Data de expiração (YYYY-MM-DD, opcional):", font=("Arial", 10)).pack(anchor=tk.W, pady=5)
        expiration_entry = ttk.Entry(frame, width=40, font=("Arial", 11))
        expiration_entry.pack(fill=tk.X, pady=5)
        
        def create():
            title = title_entry.get().strip()
            site = site_entry.get().strip()
            
            if not title or not site:
                messagebox.showwarning("Aviso", "Preencha título e site.")
                return
            
            expiration_date = None
            expiration_str = expiration_entry.get().strip()
            if expiration_str:
                try:
                    expiration_date = datetime.strptime(expiration_str, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Erro", "Data inválida. Use o formato YYYY-MM-DD.")
                    return
            
            try:
                if use_custom.get():
                    custom_password = custom_password_entry.get()
                    if not custom_password:
                        messagebox.showwarning("Aviso", "Digite a senha customizada.")
                        return
                    
                    entry_id = self.pm.create_password(
                        title, site,
                        length=len(custom_password),
                        use_uppercase=any(c.isupper() for c in custom_password),
                        use_lowercase=any(c.islower() for c in custom_password),
                        use_digits=any(c.isdigit() for c in custom_password),
                        use_special=any(not c.isalnum() for c in custom_password),
                        expiration_date=expiration_date,
                        custom_password=custom_password
                    )
                else:
                    length = int(length_var.get())
                    entry_id = self.pm.create_password(
                        title, site,
                        length=length,
                        use_uppercase=use_uppercase.get(),
                        use_lowercase=use_lowercase.get(),
                        use_digits=use_digits.get(),
                        use_special=use_special.get(),
                        expiration_date=expiration_date
                    )
                
                messagebox.showinfo("Sucesso", f"Senha criada com sucesso! ID: {entry_id}")
                dialog.destroy()
                self.refresh_list()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao criar senha: {str(e)}")
        
        # Botões
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="Criar", command=create).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def view_password_dialog(self):
        """Diálogo para ver senha descriptografada"""
        entry = self.get_selected_entry()
        if not entry:
            return
        
        result = self.pm.get_password(entry.id)
        if not result:
            messagebox.showerror("Erro", "Senha não encontrada.")
            return
        
        entry_obj, password = result
        entropy_level = PasswordGenerator.get_entropy_level(entry_obj.entropy)
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Senha: {entry_obj.title}")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Informações
        info_text = f"""
Título: {entry_obj.title}
Site: {entry_obj.site}
Senha: {password}
Tamanho: {entry_obj.length}
Entropia: {entry_obj.entropy} bits ({entropy_level})
Caracteres: Maiúsculas={entry_obj.use_uppercase}, Minúsculas={entry_obj.use_lowercase}, 
Dígitos={entry_obj.use_digits}, Especiais={entry_obj.use_special}
Criado em: {entry_obj.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Atualizado em: {entry_obj.updated_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
        if entry_obj.expiration_date:
            info_text += f"Expira em: {entry_obj.expiration_date.strftime('%Y-%m-%d')}"
        
        text_widget = tk.Text(frame, wrap=tk.WORD, font=("Arial", 11), height=15)
        text_widget.insert("1.0", info_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Botão copiar
        def copy_password():
            self.root.clipboard_clear()
            self.root.clipboard_append(password)
            messagebox.showinfo("Sucesso", "Senha copiada para a área de transferência!")
        
        ttk.Button(frame, text="Copiar Senha", command=copy_password).pack(pady=5)
        ttk.Button(frame, text="Fechar", command=dialog.destroy).pack(pady=5)
    
    def edit_password_dialog(self):
        """Diálogo para editar senha"""
        entry = self.get_selected_entry()
        if not entry:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Editar: {entry.title}")
        dialog.geometry("500x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(frame, text="Título:", font=("Arial", 11)).pack(anchor=tk.W, pady=5)
        title_entry = ttk.Entry(frame, width=40, font=("Arial", 11))
        title_entry.insert(0, entry.title)
        title_entry.pack(fill=tk.X, pady=5)
        
        # Site
        ttk.Label(frame, text="Site:", font=("Arial", 11)).pack(anchor=tk.W, pady=5)
        site_entry = ttk.Entry(frame, width=40, font=("Arial", 11))
        site_entry.insert(0, entry.site)
        site_entry.pack(fill=tk.X, pady=5)
        
        # Regenerar senha
        regenerate = tk.BooleanVar()
        ttk.Checkbutton(
            frame,
            text="Regenerar senha",
            variable=regenerate
        ).pack(anchor=tk.W, pady=10)
        
        # Opções de regeneração
        regen_frame = ttk.LabelFrame(frame, text="Opções de Regeneração", padding="10")
        regen_frame.pack(fill=tk.X, pady=10)
        
        use_custom = tk.BooleanVar()
        ttk.Checkbutton(regen_frame, text="Usar senha customizada", variable=use_custom).pack(anchor=tk.W, pady=5)
        
        custom_password_entry = ttk.Entry(regen_frame, show="•", width=40, font=("Arial", 11))
        custom_password_entry.pack(fill=tk.X, pady=5)
        
        length_var = tk.StringVar(value=str(entry.length))
        ttk.Label(regen_frame, text="Tamanho:", font=("Arial", 10)).pack(anchor=tk.W, pady=2)
        length_spin = ttk.Spinbox(regen_frame, from_=8, to=128, textvariable=length_var, width=10)
        length_spin.pack(anchor=tk.W, pady=2)
        
        use_uppercase = tk.BooleanVar(value=entry.use_uppercase)
        use_lowercase = tk.BooleanVar(value=entry.use_lowercase)
        use_digits = tk.BooleanVar(value=entry.use_digits)
        use_special = tk.BooleanVar(value=entry.use_special)
        
        ttk.Checkbutton(regen_frame, text="Maiúsculas", variable=use_uppercase).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(regen_frame, text="Minúsculas", variable=use_lowercase).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(regen_frame, text="Dígitos", variable=use_digits).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(regen_frame, text="Especiais", variable=use_special).pack(anchor=tk.W, pady=2)
        
        # Data de expiração
        ttk.Label(frame, text="Data de expiração (YYYY-MM-DD, opcional):", font=("Arial", 10)).pack(anchor=tk.W, pady=5)
        expiration_entry = ttk.Entry(frame, width=40, font=("Arial", 11))
        if entry.expiration_date:
            expiration_entry.insert(0, entry.expiration_date.strftime("%Y-%m-%d"))
        expiration_entry.pack(fill=tk.X, pady=5)
        
        def save():
            title = title_entry.get().strip()
            site = site_entry.get().strip()
            
            if not title or not site:
                messagebox.showwarning("Aviso", "Preencha título e site.")
                return
            
            expiration_date = None
            expiration_str = expiration_entry.get().strip()
            if expiration_str:
                try:
                    expiration_date = datetime.strptime(expiration_str, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Erro", "Data inválida. Use o formato YYYY-MM-DD.")
                    return
            
            try:
                custom_password = None
                length = None
                
                if regenerate.get():
                    if use_custom.get():
                        custom_password = custom_password_entry.get()
                        if not custom_password:
                            messagebox.showwarning("Aviso", "Digite a senha customizada.")
                            return
                    else:
                        length = int(length_var.get())
                
                success = self.pm.update_password(
                    entry.id,
                    title=title,
                    site=site,
                    length=length,
                    use_uppercase=use_uppercase.get() if regenerate.get() else None,
                    use_lowercase=use_lowercase.get() if regenerate.get() else None,
                    use_digits=use_digits.get() if regenerate.get() else None,
                    use_special=use_special.get() if regenerate.get() else None,
                    expiration_date=expiration_date,
                    regenerate=regenerate.get(),
                    custom_password=custom_password
                )
                
                if success:
                    messagebox.showinfo("Sucesso", "Senha atualizada com sucesso!")
                    dialog.destroy()
                    self.refresh_list()
                else:
                    messagebox.showerror("Erro", "Erro ao atualizar senha.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao atualizar senha: {str(e)}")
        
        # Botões
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="Salvar", command=save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def delete_password_dialog(self):
        """Diálogo para deletar senha"""
        entry = self.get_selected_entry()
        if not entry:
            return
        
        if messagebox.askyesno(
            "Confirmar",
            f"Tem certeza que deseja deletar '{entry.title}' ({entry.site})?"
        ):
            try:
                success = self.pm.delete_password(entry.id)
                if success:
                    messagebox.showinfo("Sucesso", "Senha deletada com sucesso!")
                    self.refresh_list()
                else:
                    messagebox.showerror("Erro", "Erro ao deletar senha.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao deletar senha: {str(e)}")
    
    def generate_test_password(self):
        """Gera uma senha de teste sem salvar"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Gerar Senha de Teste")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Tamanho:", font=("Arial", 11)).pack(anchor=tk.W, pady=5)
        length_var = tk.StringVar(value="16")
        length_spin = ttk.Spinbox(frame, from_=8, to=128, textvariable=length_var, width=10)
        length_spin.pack(anchor=tk.W, pady=5)
        
        use_uppercase = tk.BooleanVar(value=True)
        use_lowercase = tk.BooleanVar(value=True)
        use_digits = tk.BooleanVar(value=True)
        use_special = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(frame, text="Maiúsculas", variable=use_uppercase).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(frame, text="Minúsculas", variable=use_lowercase).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(frame, text="Dígitos", variable=use_digits).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(frame, text="Especiais", variable=use_special).pack(anchor=tk.W, pady=2)
        
        password_var = tk.StringVar()
        entropy_var = tk.StringVar()
        
        def generate():
            try:
                length = int(length_var.get())
                password = PasswordGenerator.generate(
                    length,
                    use_uppercase.get(),
                    use_lowercase.get(),
                    use_digits.get(),
                    use_special.get()
                )
                entropy = PasswordGenerator.calculate_entropy(
                    length,
                    use_uppercase.get(),
                    use_lowercase.get(),
                    use_digits.get(),
                    use_special.get()
                )
                entropy_level = PasswordGenerator.get_entropy_level(entropy)
                
                password_var.set(password)
                entropy_var.set(f"{entropy} bits ({entropy_level})")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao gerar senha: {str(e)}")
        
        ttk.Button(frame, text="Gerar", command=generate).pack(pady=10)
        
        ttk.Label(frame, text="Senha gerada:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=5)
        password_entry = ttk.Entry(frame, textvariable=password_var, width=40, font=("Arial", 11))
        password_entry.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame, text="Entropia:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=5)
        entropy_label = ttk.Label(frame, textvariable=entropy_var, font=("Arial", 11))
        entropy_label.pack(anchor=tk.W, pady=5)
        
        def copy_password():
            if password_var.get():
                self.root.clipboard_clear()
                self.root.clipboard_append(password_var.get())
                messagebox.showinfo("Sucesso", "Senha copiada para a área de transferência!")
        
        ttk.Button(frame, text="Copiar", command=copy_password).pack(pady=10)
        ttk.Button(frame, text="Fechar", command=dialog.destroy).pack(pady=5)
    
    def logout(self):
        """Faz logout e volta para a tela de login"""
        self.pm = None
        self.current_entries = []
        self.show_login_screen()


def main():
    root = tk.Tk()
    app = PasswordManagerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

