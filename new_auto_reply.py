import tkinter as tk
from tkinter import ttk, scrolledtext
import pyperclip
import time
import threading
import random
from openai import OpenAI
import json
import os

class AutoReplyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI自动回复助手")
        self.root.geometry("800x800")
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="15")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 让主窗口可以随着调整大小
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=3)  # 让右侧面板占更多空间
        self.main_frame.rowconfigure(0, weight=1)
        
        # 监控状态
        self.monitoring = False
        
        # 添加默认提示词
        self.prompt_template = "请你扮演一个专业的助手。"
        try:
            with open('prompt_template.txt', 'r', encoding='utf-8') as f:
                self.prompt_template = f.read().strip()
        except:
            self.save_prompt_template()
        
        # UI组件
        self.create_widgets()  # 先创建UI组件
        
        # 设置OpenAI API密钥
        self.client = None
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.client = OpenAI(api_key=config.get('openai_api_key'))
        except Exception as e:
            self.create_default_config()
        
        # 剪贴板上一次的内容
        self.last_clipboard = ""
        
    def create_default_config(self):
        default_config = {
            "openai_api_key": "<Your OpenAI API Key>",
            "model": "gpt-4o-mini",
            "temperature": 0.7
        }
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        
        # 立即使用新配置初始化客户端
        self.client = OpenAI(api_key=default_config["openai_api_key"])
        
        if hasattr(self, 'log_area'):
            self.log_message("[系统] 已创建并加载默认配置")

    def save_prompt_template(self):
        with open('prompt_template.txt', 'w', encoding='utf-8') as f:
            f.write(self.prompt_template)

    def create_widgets(self):
        # === 左侧面板 ===
        left_frame = ttk.Frame(self.main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # 让日志区域可以随窗口调整
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(2, weight=1)
        
        # 状态标签
        self.status_label = ttk.Label(left_frame, text="状态: 未启动")
        self.status_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # 启动/停止按钮
        self.toggle_button = ttk.Button(left_frame, text="启动监控", command=self.toggle_monitoring)
        self.toggle_button.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # 日志显示区域
        self.log_area = scrolledtext.ScrolledText(left_frame, width=35, height=20)
        self.log_area.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # === 右侧面板 ===
        right_frame = ttk.Frame(self.main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # 让右侧面板可以随窗口调整
        right_frame.columnconfigure(1, weight=1)
        right_frame.rowconfigure(8, weight=1)
        
        # 提示词设置区域
        ttk.Label(right_frame, text="智能提示词系统").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # 受众身份选择
        ttk.Label(right_frame, text="受众身份:").grid(row=1, column=0, sticky=tk.W)
        self.audience_var = tk.StringVar()
        self.audience_combo = ttk.Combobox(right_frame, textvariable=self.audience_var, width=25)
        self.audience_combo['values'] = ['程序员', '长辈', '朋友同学', '工作伙伴', '客户', '领导']
        self.audience_combo.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # 祝福核心
        ttk.Label(right_frame, text="祝福核心:").grid(row=2, column=0, sticky=tk.W)
        self.core_var = tk.StringVar()
        self.core_combo = ttk.Combobox(right_frame, textvariable=self.core_var, width=25)
        self.core_combo['values'] = ['健康长寿', '事业有成', '财运亨通', '阖家幸福', '技术进步']
        self.core_combo.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # 风格选择
        ttk.Label(right_frame, text="风格偏好:").grid(row=3, column=0, sticky=tk.W)
        self.style_var = tk.StringVar()
        styles = ttk.Frame(right_frame)
        styles.grid(row=3, column=1, sticky=tk.W)
        ttk.Radiobutton(styles, text="传统典雅", variable=self.style_var, value="traditional").pack(side=tk.LEFT)
        ttk.Radiobutton(styles, text="科技未来", variable=self.style_var, value="tech").pack(side=tk.LEFT)
        ttk.Radiobutton(styles, text="幽默诙谐", variable=self.style_var, value="humor").pack(side=tk.LEFT)
        ttk.Radiobutton(styles, text="国际混搭", variable=self.style_var, value="international").pack(side=tk.LEFT)
        
        # 字数选择
        ttk.Label(right_frame, text="字数要求:").grid(row=4, column=0, sticky=tk.W)
        self.length_var = tk.StringVar()
        lengths = ttk.Frame(right_frame)
        lengths.grid(row=4, column=1, sticky=tk.W)
        ttk.Radiobutton(lengths, text="50字快闪", variable=self.length_var, value="short").pack(side=tk.LEFT)
        ttk.Radiobutton(lengths, text="150字标准", variable=self.length_var, value="medium").pack(side=tk.LEFT)
        ttk.Radiobutton(lengths, text="300字深度", variable=self.length_var, value="long").pack(side=tk.LEFT)
        
        # 情感浓度
        ttk.Label(right_frame, text="情感浓度:").grid(row=5, column=0, sticky=tk.W)
        self.emotion_scale = ttk.Scale(right_frame, from_=1, to=5, orient=tk.HORIZONTAL)
        self.emotion_scale.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 在右侧面板添加自定义需求输入区域
        ttk.Label(right_frame, text="自定义需求:").grid(row=6, column=0, sticky=tk.W)
        self.custom_requirements = scrolledtext.ScrolledText(right_frame, width=45, height=4)
        self.custom_requirements.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 生成提示词按钮移到后面
        ttk.Button(right_frame, text="生成提示词", command=self.generate_prompt).grid(row=7, column=0, columnspan=2, pady=10)
        
        # 预览提示词标签和区域也相应后移
        ttk.Label(right_frame, text="当前提示词:").grid(row=8, column=0, columnspan=2, sticky=tk.W)
        self.prompt_preview = scrolledtext.ScrolledText(right_frame, width=45, height=8)
        self.prompt_preview.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 更新右侧面板的行权重
        right_frame.rowconfigure(9, weight=1)
        
        # === 底部面板 ===
        bottom_frame = ttk.Frame(self.main_frame)
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # 让底部面板可以随窗口调整
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.rowconfigure(1, weight=1)
        
        # 生成的回复显示区域
        ttk.Label(bottom_frame, text="生成的回复:").grid(row=0, column=0, sticky=tk.W)
        self.reply_area = scrolledtext.ScrolledText(bottom_frame, width=80, height=10)
        self.reply_area.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(bottom_frame)
        button_frame.grid(row=2, column=0, sticky=tk.W)
        
        ttk.Button(button_frame, text="复制回复", command=self.copy_reply).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="重新生成", command=self.regenerate_reply).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="API设置", command=self.show_settings).pack(side=tk.LEFT, padx=5)

    def toggle_monitoring(self):
        if not self.monitoring:
            self.monitoring = True
            self.toggle_button.config(text="停止监控")
            self.status_label.config(text="状态: 监控中")
            self.monitor_thread = threading.Thread(target=self.monitor_clipboard)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
        else:
            self.monitoring = False
            self.toggle_button.config(text="启动监控")
            self.status_label.config(text="状态: 已停止")
    
    def monitor_clipboard(self):
        while self.monitoring:
            try:
                current_clipboard = pyperclip.paste()
                if current_clipboard != self.last_clipboard:
                    self.last_clipboard = current_clipboard
                    self.log_message(f"[系统] 检测到新的剪贴板内容: {current_clipboard[:50]}...")
                    self.current_input = current_clipboard  # 保存当前输入以供重新生成使用
                    reply = self.generate_reply(current_clipboard)
                    self.update_reply(reply)
                    self.log_message(f"[系统] 已生成回复: {reply}")
            except Exception as e:
                self.log_message(f"[错误] 监控剪贴板时发生错误: {str(e)}")
            time.sleep(0.5)
    
    def generate_reply(self, text):
        try:
            if not self.client:
                self.log_message("[错误] 请先设置OpenAI API密钥")
                return "请先在设置中配置OpenAI API密钥"

            # 构建消息列表，使用自定义提示词
            messages = [
                {"role": "system", "content": self.prompt_template},
                {"role": "user", "content": f"对以下消息生成回复: {text}"}
            ]

            # 使用新的API调用
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7
            )
            
            reply = completion.choices[0].message.content.strip()
            self.log_message(f"[系统] AI成功生成回复")
            return reply

        except Exception as e:
            self.log_message(f"[错误] AI生成回复时发生错误: {str(e)}")
            return "抱歉，生成回复时出现错误，请检查API设置或网络连接"
    
    def regenerate_reply(self):
        try:
            if hasattr(self, 'current_input') and self.current_input:
                reply = self.generate_reply(self.current_input)
                self.update_reply(reply)
                self.log_message(f"[系统] 已重新生成回复: {reply}")
            else:
                self.log_message("[警告] 没有可用的输入内容来重新生成回复")
        except Exception as e:
            self.log_message(f"[错误] 重新生成回复时发生错误: {str(e)}")
    
    def update_reply(self, reply):
        self.reply_area.delete(1.0, tk.END)
        self.reply_area.insert(tk.END, reply)
    
    def log_message(self, message):
        self.log_area.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_area.see(tk.END)
    
    def copy_reply(self):
        try:
            reply = self.reply_area.get(1.0, tk.END).strip()
            if reply:
                pyperclip.copy(reply)
                self.log_message("[系统] 已复制回复到剪贴板")
            else:
                self.log_message("[警告] 没有可用的回复内容可复制")
        except Exception as e:
            self.log_message(f"[错误] 复制回复时发生错误: {str(e)}")

    def show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("300x200")
        
        ttk.Label(settings_window, text="OpenAI API Key:").pack(pady=5)
        api_key_entry = ttk.Entry(settings_window, width=40)
        api_key_entry.pack(pady=5)
        api_key_entry.insert(0, self.client.api_key if self.client else "")
        
        def save_settings():
            config = {
                "openai_api_key": api_key_entry.get(),
                "model": "gpt-4o-mini",
                "temperature": 0.7
            }
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            self.client = OpenAI(api_key=config["openai_api_key"])
            self.log_message("[系统] 设置已保存")
            settings_window.destroy()
        
        ttk.Button(settings_window, text="保存", command=save_settings).pack(pady=10)

    def generate_prompt(self):
        audience = self.audience_var.get()
        core = self.core_var.get()
        style = self.style_var.get()
        length = self.length_var.get()
        emotion = self.emotion_scale.get()
        
        # 基于选择生成提示词
        prompt = self.build_smart_prompt(audience, core, style, length, emotion)
        
        # 更新提示词预览和模板
        self.prompt_preview.delete(1.0, tk.END)
        self.prompt_preview.insert(tk.END, prompt)
        self.prompt_template = prompt
        self.save_prompt_template()
        
        # 生成提示词后清空自定义需求
        self.custom_requirements.delete(1.0, tk.END)
        
        self.log_message("[系统] 已更新提示词模板")

    def build_smart_prompt(self, audience, core, style, length, emotion):
        # 基础提示词结构
        base_prompt = """请你扮演一个专业的新年祝福生成助手。
需要满足以下要求：
1. 融合【传统吉祥话+现代生活元素】的创意混搭
2. 使用【动态动词+五感描写】增强感染力
3. 植入与受众相关的【文化符号/行业黑话】
4. 按指定情感浓度调整用词风格
5. 使用「痛点转化法」将负面场景转为祝福
6. 至少包含1个数据化比喻
7. 添加可触发联动的动作指引"""
        
        # 受众特征
        audience_prompts = {
            "程序员": "对方是技术从业者，可以使用适量技术术语和程序员梗。将Bug、加班等痛点转化为创新机遇，用算法、代码等元素构建祝福。",
            "长辈": "对方是长辈，需要体现尊重和孝心，语言要温暖亲切。融入传统技艺元素和家族记忆，避免晦涩难懂的现代词汇。",
            "朋友同学": "对方是朋友/同学，语气可以轻松活泼，可以带些玩笑。可以用当下流行梗，但注意尺度。",
            "工作伙伴": "对方是工作伙伴，要保持专业但不失人情味。可以用行业术语，但要注意平衡正式与亲和。",
            "客户": "对方是重要客户，要体现重视和感激之情。措辞要专业得体，传达诚意和尊重。",
            "领导": "对方是领导，要得体大方，措辞要专业稳重。避免过于随意或娱乐化的表达。",
            "爱人": "对方是恋人/配偶，语言要充满爱意和浪漫。可以使用甜蜜的昵称，融入两人间的专属记忆。"
        }
        
        # 核心祝福主题
        core_prompts = {
            "健康长寿": "重点祝愿健康长寿，家庭幸福。用五感描写来表达对健康的祝愿。",
            "事业有成": "重点祝愿事业发展，目标达成。用具体的成就指标来量化祝福。",
            "财运亨通": "重点祝愿财运亨通，收获满满。用数据化比喻来形容财富增长。",
            "阖家幸福": "重点祝愿阖家幸福，和睦美满。融入家庭场景和温馨细节。",
            "技术进步": "重点祝愿技术进步，创新不断。用行业发展趋势来构建愿景。",
            "浪漫甜蜜": "重点祝愿爱情甜蜜，感情升温。用浪漫意象和情感细节来表达。"
        }
        
        # 风格定制
        style_prompts = {
            "traditional": "要用优雅典雅的传统方式表达，可以适当引用古诗词。注重文化传承，融入传统节气、习俗等元素。",
            "tech": "要用现代科技感的方式表达，可以融入当下流行的科技元素。用数据可视化、算法等概念构建未来感。",
            "humor": "要用轻松幽默的方式表达，可以适当加入俏皮话。将严肃话题用轻松方式表达，但注意分寸。",
            "international": "要用国际化视角表达，混搭中外文化元素。可以使用多语言、时区概念等跨文化符号。"
        }
        
        # 字数控制
        length_prompts = {
            "short": "回复控制在50字以内，要简短有力。",
            "medium": "回复控制在150字以内，要内容丰富。",
            "long": "回复控制在300字以内，可以展开详细描述。"
        }
        
        # 情感浓度
        emotion_levels = {
            1: "语气要平和客观，保持适度距离。",
            2: "语气要友善温和，体现一般关心。",
            3: "语气要热情真诚，展现明显情感。",
            4: "语气要热烈深情，强调特殊情谊。",
            5: "语气要极度热忱，展现最深厚感情。"
        }
        emotion_prompt = emotion_levels.get(int(emotion), "语气要真诚自然。")
        
        # 获取自定义需求
        custom_req = self.custom_requirements.get(1.0, tk.END).strip()
        
        # 组合提示词
        prompt = (f"{base_prompt}\n\n"
                 f"【受众特征】{audience_prompts.get(audience, '')}\n\n"
                 f"【核心主题】{core_prompts.get(core, '')}\n\n"
                 f"【表达风格】{style_prompts.get(style, '')}\n\n"
                 f"【字数要求】{length_prompts.get(length, '')}\n\n"
                 f"【情感程度】{emotion_prompt}\n\n"
                 f"【自定义需求】{custom_req if custom_req else '无特殊要求'}\n\n"
                 "【注意事项】\n"
                 "1. 确保祝福语言真诚自然，避免过于生硬或公式化\n"
                 "2. 根据受众特征调整专业术语和流行语的使用比例\n"
                 "3. 注意避免宗教敏感、年龄焦虑、收入对比等内容\n"
                 "4. 禁用过时网络用语，保持表达的时效性\n"
                 "5. 根据受众身份和场合调整幽默元素的使用")
        
        return prompt

def main():
    root = tk.Tk()
    app = AutoReplyApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
