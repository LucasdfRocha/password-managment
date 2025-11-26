import customtkinter as ctk
import requests
import json
from tkinter import messagebox, scrolledtext
import pyperclip
from datetime import datetime
import threading

# Configuração da API
API_BASE_URL = "http://localhost:8000/api"

# Configuração do tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class PasswordManagerGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Password Manager")
        self.root.geometry("1000x700")

        self.session_token = None
        self.current_passwords = []

        # Criar tela de login
        self.create_login_screen()

    def create_login_screen(self):
        """Cria a tela de login"""
        # Limpar janela
        for widget in self.root.winfo_children():
            widget.destroy()

        # Frame central
        login_frame = ctk.CTkFrame(self.root, width=400, height=300)
        login_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Título
        title = ctk.CTkLabel(
            login_frame,
            text="🔐 Password Manager",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title.pack(pady=30)

        # Subtítulo
        subtitle = ctk.CTkLabel(
            login_frame,
            text="Insira sua senha mestra para continuar",
            font=ctk.CTkFont(size=14),
        )
        subtitle.pack(pady=10)

        # Campo de senha
        self.master_password_entry = ctk.CTkEntry(
            login_frame, placeholder_text="Senha Mestra", show="*", width=300, height=40
        )
        self.master_password_entry.pack(pady=20)
        self.master_password_entry.bind("<Return>", lambda e: self.login())

        # Botão de login
        login_button = ctk.CTkButton(
            login_frame,
            text="Entrar",
            command=self.login,
            width=300,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        login_button.pack(pady=10)

        # Status
        self.login_status = ctk.CTkLabel(
            login_frame, text="", font=ctk.CTkFont(size=12)
        )
        self.login_status.pack(pady=10)

    def login(self):
        """Realiza o login na API"""
        master_password = self.master_password_entry.get()

        if not master_password:
            self.login_status.configure(
                text="❌ Digite a senha mestra", text_color="red"
            )
            return

        self.login_status.configure(text="🔄 Autenticando...", text_color="yellow")
        self.root.update()

        try:
            response = requests.post(
                f"{API_BASE_URL}/auth/login",
                json={"master_password": master_password},
                timeout=5,
            )

            if response.status_code == 200:
                data = response.json()
                self.session_token = data.get("token")
                self.login_status.configure(
                    text="✅ Login realizado!", text_color="green"
                )
                self.root.after(500, self.create_main_screen)
            else:
                self.login_status.configure(text="❌ Senha incorreta", text_color="red")
        except requests.exceptions.ConnectionError:
            self.login_status.configure(
                text="❌ Erro: API não está rodando!\nInicie com: python3 api.py",
                text_color="red",
            )
        except Exception as e:
            self.login_status.configure(text=f"❌ Erro: {str(e)}", text_color="red")

    def create_main_screen(self):
        """Cria a tela principal após login"""
        # Limpar janela
        for widget in self.root.winfo_children():
            widget.destroy()

        # Layout principal com 2 colunas
        self.root.grid_columnconfigure(0, weight=0)  # Sidebar
        self.root.grid_columnconfigure(1, weight=1)  # Conteúdo
        self.root.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.create_sidebar()

        # Área de conteúdo
        self.content_frame = ctk.CTkFrame(self.root)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Mostrar lista de senhas por padrão
        self.show_passwords_list()

    def create_sidebar(self):
        """Cria a barra lateral com menu"""
        sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # Título
        title = ctk.CTkLabel(
            sidebar, text="Password Manager", font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=20)

        # Botões do menu
        btn_list = ctk.CTkButton(
            sidebar,
            text="📋 Listar Senhas",
            command=self.show_passwords_list,
            height=40,
        )
        btn_list.pack(pady=10, padx=20, fill="x")

        btn_new = ctk.CTkButton(
            sidebar,
            text="➕ Nova Senha",
            command=self.show_new_password_form,
            height=40,
        )
        btn_new.pack(pady=10, padx=20, fill="x")

        btn_generate = ctk.CTkButton(
            sidebar,
            text="🎲 Gerar Senha",
            command=self.show_generate_password,
            height=40,
        )
        btn_generate.pack(pady=10, padx=20, fill="x")

        btn_export = ctk.CTkButton(
            sidebar, text="💾 Exportar Wallet", command=self.export_wallet, height=40
        )
        btn_export.pack(pady=10, padx=20, fill="x")

        # Espaçador
        spacer = ctk.CTkFrame(sidebar, fg_color="transparent")
        spacer.pack(expand=True)

        # Botão de logout
        btn_logout = ctk.CTkButton(
            sidebar,
            text="🚪 Sair",
            command=self.logout,
            height=40,
            fg_color="red",
            hover_color="darkred",
        )
        btn_logout.pack(pady=20, padx=20, fill="x")

    def clear_content(self):
        """Limpa a área de conteúdo"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_passwords_list(self):
        """Mostra a lista de senhas"""
        self.clear_content()

        # Título
        title = ctk.CTkLabel(
            self.content_frame,
            text="📋 Minhas Senhas",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(pady=20)

        # Botão de refresh
        btn_refresh = ctk.CTkButton(
            self.content_frame,
            text="🔄 Atualizar",
            command=self.refresh_passwords_list,
            width=120,
        )
        btn_refresh.pack(pady=10)

        # Frame scrollável para a lista
        self.passwords_scroll = ctk.CTkScrollableFrame(
            self.content_frame, width=700, height=500
        )
        self.passwords_scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # Carregar senhas
        self.refresh_passwords_list()

    def refresh_passwords_list(self):
        """Atualiza a lista de senhas"""
        # Limpar lista atual
        for widget in self.passwords_scroll.winfo_children():
            widget.destroy()

        # Loading
        loading = ctk.CTkLabel(
            self.passwords_scroll,
            text="🔄 Carregando senhas...",
            font=ctk.CTkFont(size=14),
        )
        loading.pack(pady=20)

        # Carregar senhas em thread separada
        def load_passwords():
            try:
                response = requests.get(
                    f"{API_BASE_URL}/passwords",
                    headers={"X-Session-Token": self.session_token},
                    timeout=5,
                )

                if response.status_code == 200:
                    self.current_passwords = response.json()
                    self.root.after(0, self.display_passwords)
                else:
                    self.root.after(
                        0, lambda: self.show_error("Erro ao carregar senhas")
                    )
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Erro: {str(e)}"))

        thread = threading.Thread(target=load_passwords)
        thread.daemon = True
        thread.start()

    def display_passwords(self):
        """Exibe as senhas carregadas"""
        # Limpar loading
        for widget in self.passwords_scroll.winfo_children():
            widget.destroy()

        if not self.current_passwords:
            no_passwords = ctk.CTkLabel(
                self.passwords_scroll,
                text="Nenhuma senha cadastrada.\nClique em 'Nova Senha' para adicionar.",
                font=ctk.CTkFont(size=14),
            )
            no_passwords.pack(pady=50)
            return

        # Exibir cada senha
        for password in self.current_passwords:
            self.create_password_card(password)

    def create_password_card(self, password):
        """Cria um card para exibir uma senha"""
        # Frame do card
        card = ctk.CTkFrame(self.passwords_scroll)
        card.pack(fill="x", pady=5, padx=10)

        # Grid layout
        card.grid_columnconfigure(0, weight=1)

        # Título e site
        title_label = ctk.CTkLabel(
            card,
            text=f"🔑 {password['title']}",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        if password.get("site"):
            site_label = ctk.CTkLabel(
                card,
                text=f"🌐 {password['site']}",
                font=ctk.CTkFont(size=12),
                anchor="w",
            )
            site_label.grid(row=1, column=0, sticky="w", padx=15, pady=(0, 5))

        # Informações adicionais
        info_text = f"📊 Segurança: {password.get('security_level', 'N/A')}"
        if password.get("expiration_date"):
            info_text += f" | 📅 Expira: {password['expiration_date']}"

        info_label = ctk.CTkLabel(
            card, text=info_text, font=ctk.CTkFont(size=11), anchor="w"
        )
        info_label.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 10))

        # Botões de ação
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=0, column=1, rowspan=3, padx=10, pady=10)

        btn_view = ctk.CTkButton(
            btn_frame,
            text="👁️ Ver",
            command=lambda p=password: self.view_password(p),
            width=80,
            height=30,
        )
        btn_view.pack(side="left", padx=5)

        btn_copy = ctk.CTkButton(
            btn_frame,
            text="📋 Copiar",
            command=lambda p=password: self.copy_password(p),
            width=80,
            height=30,
        )
        btn_copy.pack(side="left", padx=5)

        btn_delete = ctk.CTkButton(
            btn_frame,
            text="🗑️ Deletar",
            command=lambda p=password: self.delete_password(p),
            width=80,
            height=30,
            fg_color="red",
            hover_color="darkred",
        )
        btn_delete.pack(side="left", padx=5)

    def view_password(self, password):
        """Visualiza uma senha específica"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/passwords/{password['id']}",
                headers={"X-Session-Token": self.session_token},
                timeout=5,
            )

            if response.status_code == 200:
                data = response.json()

                # Criar janela de diálogo
                dialog = ctk.CTkToplevel(self.root)
                dialog.title(f"🔑 {password['title']}")
                dialog.geometry("500x400")
                dialog.transient(self.root)
                dialog.grab_set()

                # Conteúdo
                content = ctk.CTkFrame(dialog)
                content.pack(fill="both", expand=True, padx=20, pady=20)

                # Título
                title_label = ctk.CTkLabel(
                    content,
                    text=password["title"],
                    font=ctk.CTkFont(size=20, weight="bold"),
                )
                title_label.pack(pady=10)

                # Informações
                info_frame = ctk.CTkFrame(content)
                info_frame.pack(fill="both", expand=True, pady=10)

                fields = [
                    ("Site:", data.get("site", "N/A")),
                    ("Usuário:", data.get("username", "N/A")),
                    ("Senha:", data.get("password", "N/A")),
                    ("Segurança:", data.get("security_level", "N/A")),
                    ("Entropia:", f"{data.get('entropy', 0):.2f} bits"),
                    ("Expira em:", data.get("expiration_date", "Nunca")),
                ]

                for label, value in fields:
                    row = ctk.CTkFrame(info_frame, fg_color="transparent")
                    row.pack(fill="x", pady=5, padx=10)

                    ctk.CTkLabel(
                        row,
                        text=label,
                        font=ctk.CTkFont(size=12, weight="bold"),
                        width=120,
                        anchor="w",
                    ).pack(side="left")

                    value_label = ctk.CTkLabel(
                        row, text=value, font=ctk.CTkFont(size=12), anchor="w"
                    )
                    value_label.pack(side="left", fill="x", expand=True)

                # Botão de copiar
                btn_copy = ctk.CTkButton(
                    content,
                    text="📋 Copiar Senha",
                    command=lambda: self.copy_to_clipboard(data.get("password", "")),
                    height=40,
                )
                btn_copy.pack(pady=10)

                # Botão de fechar
                btn_close = ctk.CTkButton(
                    content, text="Fechar", command=dialog.destroy, height=40
                )
                btn_close.pack(pady=10)

            else:
                messagebox.showerror("Erro", "Não foi possível carregar a senha")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao visualizar senha: {str(e)}")

    def copy_password(self, password):
        """Copia a senha para a área de transferência"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/passwords/{password['id']}",
                headers={"X-Session-Token": self.session_token},
                timeout=5,
            )

            if response.status_code == 200:
                data = response.json()
                pwd = data.get("password", "")
                self.copy_to_clipboard(pwd)
            else:
                messagebox.showerror("Erro", "Não foi possível copiar a senha")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao copiar senha: {str(e)}")

    def copy_to_clipboard(self, text):
        """Copia texto para a área de transferência"""
        try:
            pyperclip.copy(text)
            messagebox.showinfo(
                "✅ Sucesso", "Senha copiada para a área de transferência!"
            )
        except:
            # Fallback para clipboard nativo do tkinter
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("✅ Sucesso", "Senha copiada!")

    def delete_password(self, password):
        """Deleta uma senha"""
        result = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja deletar a senha '{password['title']}'?",
        )

        if result:
            try:
                response = requests.delete(
                    f"{API_BASE_URL}/passwords/{password['id']}",
                    headers={"X-Session-Token": self.session_token},
                    timeout=5,
                )

                if response.status_code == 200:
                    messagebox.showinfo("✅ Sucesso", "Senha deletada com sucesso!")
                    self.refresh_passwords_list()
                else:
                    messagebox.showerror("Erro", "Não foi possível deletar a senha")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao deletar senha: {str(e)}")

    def show_new_password_form(self):
        """Mostra o formulário de nova senha"""
        self.clear_content()

        # Título
        title = ctk.CTkLabel(
            self.content_frame,
            text="➕ Nova Senha",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(pady=20)

        # Frame do formulário
        form_frame = ctk.CTkFrame(self.content_frame, width=600)
        form_frame.pack(pady=20, padx=50, fill="both", expand=True)

        # Campos do formulário
        fields_frame = ctk.CTkFrame(form_frame)
        fields_frame.pack(pady=20, padx=20, fill="x")

        # Título da senha
        ctk.CTkLabel(
            fields_frame, text="Título:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        title_entry = ctk.CTkEntry(
            fields_frame, placeholder_text="Ex: Gmail, Facebook, etc."
        )
        title_entry.pack(fill="x", pady=(0, 10))

        # Site
        ctk.CTkLabel(
            fields_frame,
            text="Site (opcional):",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))
        site_entry = ctk.CTkEntry(fields_frame, placeholder_text="Ex: gmail.com")
        site_entry.pack(fill="x", pady=(0, 10))

        # Username
        ctk.CTkLabel(
            fields_frame,
            text="Usuário (opcional):",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))
        username_entry = ctk.CTkEntry(
            fields_frame, placeholder_text="Ex: usuario@email.com"
        )
        username_entry.pack(fill="x", pady=(0, 10))

        # Configurações da senha
        config_frame = ctk.CTkFrame(fields_frame)
        config_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            config_frame,
            text="Configurações da Senha:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", pady=10)

        # Tamanho
        length_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        length_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(length_frame, text="Tamanho:").pack(side="left", padx=(0, 10))
        length_slider = ctk.CTkSlider(length_frame, from_=8, to=32, number_of_steps=24)
        length_slider.set(16)
        length_slider.pack(side="left", fill="x", expand=True)
        length_value = ctk.CTkLabel(length_frame, text="16")
        length_value.pack(side="left", padx=10)

        def update_length(value):
            length_value.configure(text=str(int(value)))

        length_slider.configure(command=update_length)

        # Checkboxes
        uppercase_var = ctk.BooleanVar(value=True)
        lowercase_var = ctk.BooleanVar(value=True)
        digits_var = ctk.BooleanVar(value=True)
        special_var = ctk.BooleanVar(value=True)

        ctk.CTkCheckBox(
            config_frame, text="Letras Maiúsculas (A-Z)", variable=uppercase_var
        ).pack(anchor="w", pady=5)
        ctk.CTkCheckBox(
            config_frame, text="Letras Minúsculas (a-z)", variable=lowercase_var
        ).pack(anchor="w", pady=5)
        ctk.CTkCheckBox(config_frame, text="Números (0-9)", variable=digits_var).pack(
            anchor="w", pady=5
        )
        ctk.CTkCheckBox(
            config_frame, text="Caracteres Especiais (!@#$...)", variable=special_var
        ).pack(anchor="w", pady=5)

        # Data de expiração (opcional)
        ctk.CTkLabel(
            fields_frame,
            text="Data de Expiração (opcional):",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))
        expiration_entry = ctk.CTkEntry(
            fields_frame, placeholder_text="YYYY-MM-DD (Ex: 2025-12-31)"
        )
        expiration_entry.pack(fill="x", pady=(0, 10))

        # Botões
        buttons_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        buttons_frame.pack(pady=20)

        def create_password():
            title = title_entry.get()
            if not title:
                messagebox.showerror("Erro", "O título é obrigatório!")
                return

            password_data = {
                "title": title,
                "site": site_entry.get() or None,
                "username": username_entry.get() or None,
                "length": int(length_slider.get()),
                "use_uppercase": uppercase_var.get(),
                "use_lowercase": lowercase_var.get(),
                "use_digits": digits_var.get(),
                "use_special": special_var.get(),
                "expiration_date": expiration_entry.get() or None,
            }

            try:
                response = requests.post(
                    f"{API_BASE_URL}/passwords",
                    json=password_data,
                    headers={"X-Session-Token": self.session_token},
                    timeout=5,
                )

                if response.status_code == 200:
                    messagebox.showinfo("Sucesso", "Senha criada com sucesso!")
                    self.show_passwords_list()
                else:
                    messagebox.showerror(
                        "Erro", f"Erro ao criar senha: {response.text}"
                    )
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao criar senha: {str(e)}")

        btn_create = ctk.CTkButton(
            buttons_frame,
            text="Criar Senha",
            command=create_password,
            width=150,
            height=40,
        )
        btn_create.pack(side="left", padx=10)

        btn_cancel = ctk.CTkButton(
            buttons_frame,
            text="❌ Cancelar",
            command=self.show_passwords_list,
            width=150,
            height=40,
            fg_color="gray",
            hover_color="darkgray",
        )
        btn_cancel.pack(side="left", padx=10)

    def show_generate_password(self):
        """Mostra a tela de geração de senha de teste"""
        self.clear_content()

        # Título
        title = ctk.CTkLabel(
            self.content_frame,
            text="🎲 Gerar Senha de Teste",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(pady=20)

        # Frame do formulário
        form_frame = ctk.CTkFrame(self.content_frame, width=600)
        form_frame.pack(pady=20, padx=50)

        config_frame = ctk.CTkFrame(form_frame)
        config_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Tamanho
        length_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        length_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(
            length_frame, text="Tamanho:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 10))
        length_slider = ctk.CTkSlider(length_frame, from_=8, to=32, number_of_steps=24)
        length_slider.set(16)
        length_slider.pack(side="left", fill="x", expand=True)
        length_value = ctk.CTkLabel(length_frame, text="16")
        length_value.pack(side="left", padx=10)

        def update_length(value):
            length_value.configure(text=str(int(value)))

        length_slider.configure(command=update_length)

        # Checkboxes
        uppercase_var = ctk.BooleanVar(value=True)
        lowercase_var = ctk.BooleanVar(value=True)
        digits_var = ctk.BooleanVar(value=True)
        special_var = ctk.BooleanVar(value=True)

        ctk.CTkCheckBox(
            config_frame, text="Letras Maiúsculas (A-Z)", variable=uppercase_var
        ).pack(anchor="w", pady=5)
        ctk.CTkCheckBox(
            config_frame, text="Letras Minúsculas (a-z)", variable=lowercase_var
        ).pack(anchor="w", pady=5)
        ctk.CTkCheckBox(config_frame, text="Números (0-9)", variable=digits_var).pack(
            anchor="w", pady=5
        )
        ctk.CTkCheckBox(
            config_frame, text="Caracteres Especiais (!@#$...)", variable=special_var
        ).pack(anchor="w", pady=5)

        # Área para mostrar a senha gerada
        result_frame = ctk.CTkFrame(form_frame)
        result_frame.pack(pady=20, padx=20, fill="x")

        ctk.CTkLabel(
            result_frame, text="Senha Gerada:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=5)

        password_display = ctk.CTkTextbox(
            result_frame, height=80, font=ctk.CTkFont(size=14)
        )
        password_display.pack(fill="x", pady=5)

        # Botões
        buttons_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)

        def generate():
            data = {
                "length": int(length_slider.get()),
                "use_uppercase": uppercase_var.get(),
                "use_lowercase": lowercase_var.get(),
                "use_digits": digits_var.get(),
                "use_special": special_var.get(),
            }

            try:
                response = requests.post(
                    f"{API_BASE_URL}/passwords/generate",
                    json=data,
                    headers={"X-Session-Token": self.session_token},
                    timeout=5,
                )

                if response.status_code == 200:
                    result = response.json()
                    password_display.delete("1.0", "end")
                    password_display.insert(
                        "1.0",
                        f"Senha: {result['password']}\n"
                        f"Segurança: {result['security_level']}\n"
                        f"Entropia: {result['entropy']:.2f} bits",
                    )
                else:
                    messagebox.showerror("Erro", "Erro ao gerar senha")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao gerar senha: {str(e)}")

        def copy_generated():
            text = password_display.get("1.0", "end").strip()
            if text and "Senha:" in text:
                password = text.split("Senha:")[1].split("\n")[0].strip()
                self.copy_to_clipboard(password)

        btn_generate = ctk.CTkButton(
            buttons_frame, text="Gerar", command=generate, width=150, height=40
        )
        btn_generate.pack(side="left", padx=10)

        btn_copy = ctk.CTkButton(
            buttons_frame,
            text="📋 Copiar",
            command=copy_generated,
            width=150,
            height=40,
        )
        btn_copy.pack(side="left", padx=10)

    def export_wallet(self):
        """Exporta o wallet"""
        messagebox.showinfo(
            "Exportar Wallet",
            "Esta funcionalidade ainda não foi implementada na GUI.\n"
            "Use a API diretamente ou a interface CLI para exportar o wallet.",
        )

    def logout(self):
        """Realiza logout"""
        result = messagebox.askyesno("Logout", "Tem certeza que deseja sair?")
        if result:
            try:
                requests.post(
                    f"{API_BASE_URL}/auth/logout",
                    headers={"X-Session-Token": self.session_token},
                    timeout=5,
                )
            except:
                pass

            self.session_token = None
            self.create_login_screen()

    def show_error(self, message):
        """Mostra mensagem de erro"""
        messagebox.showerror("Erro", message)

    def run(self):
        """Inicia a aplicação"""
        self.root.mainloop()


if __name__ == "__main__":
    app = PasswordManagerGUI()
    app.run()
