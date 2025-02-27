import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

VersionCode = "0.0.2"

class PasswordManager:
    def __init__(self, master):
        self.master = master
        master.title("密码管理系统")
        master.geometry("900x500")
        master.resizable(False, False)  # 禁用最大化
        
        # 将窗口居中显示
        self.center_window(master)
        
        # 数据库初始化
        self.conn = sqlite3.connect('passwords.db')
        self.create_table()
        # 样式配置
        self.style = ttk.Style()
        self.style.configure("Treeview", rowheight=25)
        self.style.configure("TButton", padding=6, font=('微软雅黑', 10))
        
        # GUI组件
        self.create_widgets()
        self.load_data()
        
        # 添加版本号显示
        self.version_label = tk.Label(master, text=f"Disigned By MikuFans.Pro | Version: {VersionCode}", anchor='w')
        self.version_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
    def center_window(self, window):
        """将窗口居中显示"""
        window.update_idletasks()  # 确保窗口尺寸和位置信息已更新
        width = window.winfo_width()
        height = window.winfo_height()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"+{x}+{y}")

    def create_table(self):
        """创建数据库表"""
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS passwords
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT NOT NULL,
                     domain TEXT NOT NULL,
                     username TEXT NOT NULL,
                     password TEXT NOT NULL,
                     notes TEXT)''')
        self.conn.commit()

    def create_widgets(self):
        """创建界面组件"""
        # 搜索区域
        search_frame = ttk.Frame(self.master)
        search_frame.pack(pady=10, padx=10, fill=tk.X)
        
        # 左侧搜索组件
        left_search = ttk.Frame(search_frame)
        left_search.pack(side=tk.LEFT, expand=True)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(left_search, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(left_search, text="搜索", command=self.search).pack(side=tk.LEFT)
        
        # 右侧操作按钮
        right_buttons = ttk.Frame(search_frame)
        right_buttons.pack(side=tk.RIGHT)
        
        ttk.Button(right_buttons, text="新增", command=self.add_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(right_buttons, text="编辑", command=self.edit_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(right_buttons, text="删除", command=self.delete).pack(side=tk.LEFT, padx=5)
        
        # 数据表格
        self.tree = ttk.Treeview(self.master, 
                               columns=('ID','服务','域名','账号','密码','备注'), 
                               show='headings', 
                               selectmode='browse')
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10)

        self.style.configure('Treeview', rowheight=25, background='white', fieldbackground='white')
        self.style.map('Treeview', background=[('selected', '#0078D7')])  # 选中行颜色
        
        # 配置交替行颜色
        self.tree.tag_configure('evenrow', background='white')    # 偶数行
        self.tree.tag_configure('oddrow', background='#F0F8FF')   # 奇数行（淡蓝色）
        # 事件绑定
        self.tree.bind('<Double-1>', self.on_double_click)  # 双击事件
        self.tree.bind('<Button-3>', self.on_right_click)   # 右键事件
        
        # 列配置
        columns = [
            ('ID', 60), 
            ('服务', 150),
            ('域名', 200),
            ('账号', 120),
            ('密码', 150),
            ('备注', 120)
        ]
        for col, width in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor='w')

    def load_data(self, search_query=None):
        """加载数据到表格"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        c = self.conn.cursor()
        if search_query:
            like = f'%{search_query}%'
            c.execute("SELECT * FROM passwords WHERE name LIKE ? OR domain LIKE ?", (like, like))
        else:
            c.execute("SELECT * FROM passwords")
        
        # 处理查询结果
        rows = c.fetchall()
        for index, row in enumerate(rows):
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            self.tree.insert('', 'end', values=row, tags=(tag,))

    def search(self):
        """执行搜索"""
        self.load_data(self.search_var.get())
        
    def add_dialog(self):
        """新增记录对话框"""
        self.input_dialog("新增记录", self.save_record)
        
    def edit_dialog(self):
        """编辑记录对话框"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要编辑的记录")
            return
        self.input_dialog("编辑记录", self.update_record, selected[0])
        
    def input_dialog(self, title, callback, item=None):
        """通用输入对话框"""
        dialog = tk.Toplevel(self.master)
        dialog.title(title)
        dialog.resizable(False, False)  # 禁用最大化
        dialog.transient(self.master)  # 设为子窗口
        dialog.grab_set()
        
        fields = ['服务', '域名', '账号', '密码', '备注']
        entries = {}
        default_values = self.tree.item(item, 'values')[1:] if item else ['']*5
        
        for idx, field in enumerate(fields):
            ttk.Label(dialog, text=field+":").grid(row=idx, column=0, padx=5, pady=5, sticky='e')
            entry = ttk.Entry(dialog, width=40)
            entry.grid(row=idx, column=1, padx=5, pady=5)
            entry.insert(0, default_values[idx])
            entries[field] = entry
            
        ttk.Button(dialog, text="保存", command=lambda: self.validate_and_save(dialog, entries, callback, item)
                  ).grid(row=5, columnspan=2, pady=10)
        
        # 对话框居中显示
        self.center_window(dialog)

    def validate_and_save(self, dialog, entries, callback, item=None):
        """验证并保存数据"""
        data = {k: v.get().strip() for k, v in entries.items()}
        if not all([data['服务'], data['域名'], data['账号'], data['密码']]):
            messagebox.showerror("错误", "服务、域名、账号和密码为必填项")
            return
        callback(dialog, data, item)
        
    def save_record(self, dialog, data, _):
        """保存新记录"""
        c = self.conn.cursor()
        c.execute('INSERT INTO passwords (name, domain, username, password, notes) VALUES (?, ?, ?, ?, ?)',
                 (data['服务'], data['域名'], data['账号'], data['密码'], data['备注']))
        self.conn.commit()
        dialog.destroy()
        self.load_data()
        
    def update_record(self, dialog, data, item):
        """更新记录"""
        record_id = self.tree.item(item, 'values')[0]
        c = self.conn.cursor()
        c.execute('''UPDATE passwords SET 
                    name=?, domain=?, username=?, password=?, notes=?
                    WHERE id=?''',
                 (data['服务'], data['域名'], data['账号'], data['密码'], data['备注'], record_id))
        self.conn.commit()
        dialog.destroy()
        self.load_data()
        
    def delete(self):
        """删除记录"""
        selected = self.tree.selection()
        if not selected:
            return
        
        # 获取选中的记录信息
        record_values = self.tree.item(selected[0], 'values')
        name = record_values[1]  # 服务名称
        domain = record_values[2]  # 域名
        username = record_values[3]  # 账号
        
        # 弹出确认对话框，显示服务、域名和账号信息
        confirm_message = (
            "您正在执行记录删除操作\n\n"
            f"服务：{name}\n"
            f"域名：{domain}\n"
            f"账号：{username}\n\n"
            "确认要删除此条记录吗？"
        )
        
        if messagebox.askyesno("警告", confirm_message):
            record_id = record_values[0]
            c = self.conn.cursor()
            c.execute("DELETE FROM passwords WHERE id=?", (record_id,))
            self.conn.commit()
            self.load_data()

    def on_double_click(self, event):
        """处理双击事件"""
        item = self.tree.identify_row(event.y)
        if item:
            self.edit_dialog()

    def on_right_click(self, event):
        """处理右键事件"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        # 创建上下文菜单
        menu = tk.Menu(self.master, tearoff=0)
        menu.add_command(label="复制域名", command=lambda: self.copy_field(item, 2))
        menu.add_command(label="复制账号", command=lambda: self.copy_field(item, 3))
        menu.add_command(label="复制密码", command=lambda: self.copy_field(item, 4))
        menu.tk_popup(event.x_root, event.y_root)

    def copy_field(self, item, column_index):
        """复制指定字段"""
        value = self.tree.item(item, 'values')[column_index]
        self.master.clipboard_clear()
        self.master.clipboard_append(value)
        self.master.update()  # 确保剪贴板更新

if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordManager(root)
    root.mainloop()
