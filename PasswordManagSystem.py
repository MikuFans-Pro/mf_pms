import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

class PasswordManager:
    def __init__(self, master):
        self.master = master
        master.title("密码管理系统")
        master.geometry("900x500")
        
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
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search).pack(side=tk.LEFT)
        
        # 数据表格
        self.tree = ttk.Treeview(self.master, 
                               columns=('ID','名称','域名','用户名','密码','备注'), 
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
            ('名称', 150),
            ('域名', 200),
            ('用户名', 120),
            ('密码', 150),
            ('备注', 120)
        ]
        for col, width in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor='w')
        
        # 操作按钮
        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="新增", command=self.add_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="编辑", command=self.edit_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除", command=self.delete).pack(side=tk.LEFT, padx=5)

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
        dialog = tk.Toplevel()
        dialog.title(title)
        dialog.grab_set()
        
        fields = ['名称', '域名', '用户名', '密码', '备注']
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

    def validate_and_save(self, dialog, entries, callback, item=None):
        """验证并保存数据"""
        data = {k: v.get().strip() for k, v in entries.items()}
        if not all([data['名称'], data['域名'], data['用户名'], data['密码']]):
            messagebox.showerror("错误", "名称、域名、用户名和密码为必填项")
            return
        callback(dialog, data, item)
        
    def save_record(self, dialog, data, _):
        """保存新记录"""
        c = self.conn.cursor()
        c.execute('INSERT INTO passwords (name, domain, username, password, notes) VALUES (?, ?, ?, ?, ?)',
                 (data['名称'], data['域名'], data['用户名'], data['密码'], data['备注']))
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
                 (data['名称'], data['域名'], data['用户名'], data['密码'], data['备注'], record_id))
        self.conn.commit()
        dialog.destroy()
        self.load_data()
        
    def delete(self):
        """删除记录"""
        selected = self.tree.selection()
        if not selected:
            return
        if messagebox.askyesno("确认", "确定要删除这条记录吗？"):
            record_id = self.tree.item(selected[0], 'values')[0]
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
        menu.add_command(label="复制用户名", command=lambda: self.copy_field(item, 3))
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