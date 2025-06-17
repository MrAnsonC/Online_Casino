import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk, ImageColor
from pygame import mixer
import random
import json
import os
import time

def get_data_file_path():
    # 用于获取保存数据的文件路径
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '../saving_data.json')

# 保存用户数据
def save_user_data(users):
    file_path = get_data_file_path()
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

# 读取用户数据
def load_user_data():
    file_path = get_data_file_path()
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def update_balance_in_json(username, new_balance):
    users = load_user_data()  # 先加载现有用户数据
    for user in users:
        if user['user_name'] == username:  # 查找当前用户
            user['cash'] = f"{new_balance:.2f}"  # 更新余额
            break
    save_user_data(users)  # 保存更新后的数据

class Baccarat:
    def __init__(self, decks=8):
        self.deck = self.create_deck(decks)
        random.shuffle(self.deck)
        self.player_hand = []
        self.banker_hand = []
        self.player_score = 0
        self.banker_score = 0
        self.winner = None
        self.cut_position = 0
        self.used_cards = 0
        self.total_cards = 0
        self.create_deck(decks)
        random.shuffle(self.deck)
        
    def create_deck(self, decks=8):
        suits = ['Club', 'Diamond', 'Heart', 'Spade']
        ranks = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
        self.deck = [(suit, rank) for _ in range(decks) for suit in suits for rank in ranks]
        random.shuffle(self.deck)
        self.total_cards = len(self.deck)
        return self.deck

    def advanced_shuffle(self, cut_pos):
        self.deck = self.deck[cut_pos:] + self.deck[:cut_pos]
        first_card = self.deck[0]
        
        # 修复的扣除值计算逻辑
        deduct_map = {
            'A': 1, 'J': 10, 'Q': 10, 'K': 10, 
            '10': 10, '2':2, '3':3, '4':4, '5':5,
            '6':6, '7':7, '8':8, '9':9
        }
        
        # 安全获取扣除值
        deduct = deduct_map.get(first_card[1], 0)  # 默认扣除0张
        
        end_pos = (1 + deduct) % self.total_cards
        self.deck = self.deck[end_pos:] + self.deck[:end_pos]
        self.used_cards = random.randint(28, 48)
        self.cut_position = 0

    def card_value(self, card):
        rank = card[1]
        if rank in ['J','Q','K']: return 0
        if rank == 'A': return 1
        try:
            return int(rank)
        except:
            return 0

    def deal_initial(self):
        indices = [(self.cut_position + i) % self.total_cards for i in range(4)]
        self.player_hand = [self.deck[indices[0]], self.deck[indices[2]]]
        self.banker_hand = [self.deck[indices[1]], self.deck[indices[3]]]
        self.cut_position = (self.cut_position + 4) % self.total_cards

    def calculate_score(self, hand):
        return sum(self.card_value(c) for c in hand) % 10

    def play_game(self):
        self.deal_initial()
        p_initial = self.calculate_score(self.player_hand[:2])
        b_initial = self.calculate_score(self.banker_hand[:2])

        if p_initial >= 8 or b_initial >= 8:
            self.player_score = p_initial
            self.banker_score = b_initial
        else:
            if p_initial <= 5:
                self.player_hand.append(self.deck.pop())
            self._banker_draw_logic()

        self._determine_winner()

    def _banker_draw_logic(self):
        b_score = self.calculate_score(self.banker_hand[:2])
        if len(self.player_hand) == 2:
            if b_score <= 5:
                self.banker_hand.append(self.deck.pop())
        else:
            third_val = self.card_value(self.player_hand[2])
            if b_score <= 2:
                self.banker_hand.append(self.deck.pop())
            elif b_score == 3 and third_val != 8:
                self.banker_hand.append(self.deck.pop())
            elif b_score == 4 and 2 <= third_val <= 7:
                self.banker_hand.append(self.deck.pop())
            elif b_score == 5 and 4 <= third_val <= 7:
                self.banker_hand.append(self.deck.pop())
            elif b_score == 6 and 6 <= third_val <= 7:
                self.banker_hand.append(self.deck.pop())

    def _determine_winner(self):
        self.player_score = self.calculate_score(self.player_hand)
        self.banker_score = self.calculate_score(self.banker_hand)
        if self.player_score > self.banker_score:
            self.winner = 'Player'
        elif self.banker_score > self.player_score:
            self.winner = 'Banker'
        else:
            self.winner = 'Tie'

class BaccaratGUI(tk.Tk):
    def __init__(self, initial_balance, username):
        super().__init__()
        self.title("Baccarat")
        self.geometry("1350x720")
        self.configure(bg='#35654d')
        mixer.init()  # 初始化音频模块
        self.sound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Baccarant')
        self.is_muted = False

        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Baccarant')
        self.data_file = os.path.join(self.data_dir, 'Baccarant_data.json')
        self._ensure_data_file()
        
        self.bet_buttons = []
        self.selected_chip = None
        self.chip_buttons = []
        self.result_text_id = None
        self.result_bg_id = None

        self.game_mode = "classic"
        self.game = Baccarat()
        self.balance = initial_balance
        self.current_bets = {}
        self.card_images = {}

        # 新增連勝記錄追蹤屬性
        self.current_streak = 0
        self.current_streak_type = None
        self.longest_streaks = {
            'Player': 0,
            'Tie': 0,
            'Banker': 0
        }
        
        # 加載最長連勝記錄
        self._load_longest_streaks()

        # 新增珠路图相关属性
        self.marker_results = []  # 存储每局结果
        self.marker_counts = {
            'Player': 0,
            'Banker': 0,
            'Tie': 0,
            'Small Tiger': 0,
            'Tiger Tie': 0,
            'Big Tiger': 0,
            'Panda 8': 0,
            'Divine 9': 0,
            'Dragon 7': 0,
            'P Fabulous 4': 0,
            'B Fabulous 4': 0
        }

        self.max_marker_rows = 6  # 最大行数
        self.max_marker_cols = 11  # 最大列数
        self.view_mode = "betting"
        self.bigroad_results = []
        self._max_rows = 6
        self._max_cols = 50
        self._bigroad_occupancy = [[False]*self._max_cols for _ in range(self._max_rows)]
        
        self._load_assets()
        self._create_widgets()
        self._setup_bindings()
        self.point_labels = {}
        self._player_area = (200, 200, 400, 400)
        self._banker_area = (600, 200, 800, 400)
        self.selected_bet_amount = 1000
        self.current_bet = 0
        self.last_win = 0
        self._draw_table_labels()
        self.game = None
        self._initialize_game(False)
        self.username = username
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def on_close(self):
        self.destroy()
        self.quit()

    def show_game_instructions(self):
        if self.game_mode == "classic":
            instructions = """
            🎮 Classic Baccarat game rules 🎮

            [Basic gameplay]
            1. Players bet on the Player, Tie, Banker
            2. Both sides are dealt 2-3 cards, and the one with the closest to 9 wins
            3. Point calculation: A=1, 10/J/Q/K=0, others are calculated at face value
            4. Only the single digit value is taken (such as 7+8=15→5)

            💰 Odds table 💰
            Player                           1:1
            Tie                                 8:1
            Banker                          0.95:1
            == Side bet == 
            Player pair                   11:1
            Any pair#                     5:1
            Banker pair                  11:1
            Dragon P(Player)        1-30:1
            Quik^                           1-30:1
            Dragon B(Banker)       1-30:1*

            📌 Special Rules 📌
            # Any pair means rather Player or Banker is pair

            *Dragon bet:
            Win more than other side 9 points  30:1
            Win more than other side 8 points  10:1
            Win more than other side 7 points  6:1
            Win more than other side 6 points  4:1
            Win more than other side 5 points  2:1
            Win more than other side 4 points  1:1
            Win in natural (Tie Push)                     1:1

            ^Quik:
            Combined final Player and Banker points. (such as 7+8=15)
            combine number is 0                                        50:1
            combine number is 18                                      25:1
            combine number is 1, 2, 3, 15, 16, 17            1:1
            """
        elif self.game_mode == "tiger":
            instructions = """
            🎮 Tiger Baccarat game rules 🎮

            [Basic gameplay]
            1. Players bet on the Player, Tie, Banker
            2. Both sides are dealt 2-3 cards, and the one with the closest to 9 wins
            3. Point calculation: A=1, 10/J/Q/K=0, others are calculated at face value
            4. Only the single digit value is taken (such as 7+8=15→5)

            ⚡ Special card types ⚡
            ▪ Small Tiger: Banker has a winning two-card total of 6.
            ▪ Big Tiger: Banker has a winning three-card total of 6.

            💰 Odds table 💰
            Player           1:1
            Tie                 8:1
            Banker          1:1*
            == Side bet ==
            Tiger pair     4-100:1#
            Tiger             12/20:1^
            Small Tiger   22:1
            Big Tiger       50:1
            Tiger Tie       35:1

            📌 Special Rules 📌
            * Banker's has a winning card of 6 are reduced to 0.5:1

            # 4:1 for single pair
            # 20:1 for double pairs
            # 100:1 for twins pairs

            ^ 12:1 for Small Tiger and 20:1 for Big Tiger
            """
        elif self.game_mode == "ez":
            instructions = """
            🎮 EZ Baccarat game rules 🎮

            [Basic gameplay]
            1. Players bet on the Player, Tie, Banker
            2. Both sides are dealt 2-3 cards, and the one with the closest to 9 wins
            3. Point calculation: A=1, 10/J/Q/K=0, others are calculated at face value
            4. Only the single digit value is taken (such as 7+8=15→5)

            ⚡ Special card types ⚡
            ▪ Panda 8: Player has a winning three-card total of 8.
            ▪ Dragon 7: Banker has a winning three-card total of 7.

            💰 Odds table 💰
            Player                  1:1
            Tie                        8:1
            Banker                 1:1*
            == Side bet ==
            Monkey 6          12:1△
            Monkey Tie       150:1△
            Big Monkey       5000:1△
            Panda 8              25:1^
            Divine 9             10/75:1#^
            Dragon 7           40:1^

            📌 Special Rules 📌
            * Banker PUSH when Banker winning three-card total of 7.

            △ Monkey means 'J' 'Q' 'K' only.
            Requirment to win Monkey 6: 
                - Player draw a non-monkey card.
                - Banker draw a monkey card.
                - Result of this round is NOT Tie.
            Requirment to win Monkey 6 Tie: 
                - Player draw a non-monkey card.
                - Banker draw a monkey card.
                - Result of this round is Tie.
            Requirment to win Monkey 6: 
                - 6 monkey cards.

            # 10:1 for either side winning three-card total of 9.
            # 75:1 for both side winning three-card total of 9.

            ^ Must be winning three-card.
            """
        elif self.game_mode == "2to1":
            instructions = """
            🎮 2 To 1 Baccarat game rules 🎮

            [Basic gameplay]
            1. Players bet on the Player, Tie, Banker
            2. Both sides are dealt 2-3 cards, and the one with the closest to 9 wins
            3. Point calculation: A=1, 10/J/Q/K=0, others are calculated at face value
            4. Only the single digit value is taken (such as 7+8=15→5)

            💰 Odds table 💰
            Player           1:1 (or 2:1 if win with 3-card 8/9)
            Tie              8:1 (Lose)
            Banker          1:1 (or 2:1 if win with 3-card 8/9)

            == Side bet == 
            Dragon P(Player)        1-30:1
            Quik^                   1-50:1
            Dragon B(Banker)        1-30:1*
            Pair Player             11:1
            Any pair#               5:1
            Pair Banker             11:1

            📌 Special Rules 📌
            * 2:1 payout for Player or Banker winning with 3-card 8 or 9.
            * Tie is considered lose (no push).

            # Any pair means rather Player or Banker is pair

            *Dragon bet:
            Win more than other side 9 points  30:1
            Win more than other side 8 points  10:1
            Win more than other side 7 points  6:1
            Win more than other side 6 points  4:1
            Win more than other side 5 points  2:1
            Win more than other side 4 points  1:1
            Win in natural (Tie Push)                     1:1

            ^Quik:
            Combined final Player and Banker points. (such as 7+8=15)
            combine number is 0                                        50:1
            combine number is 18                                      25:1
            combine number is 1, 2, 3, 15, 16, 17            1:1
            """
        elif self.game_mode == "fabulous4":
            instructions = """
            🎮 神奇4點百家樂遊戲規則 🎮

            [基本玩法]
            1. 玩家押注莊家、閒家或和局
            2. 雙方發2-3張牌，點數最接近9者勝
            3. 點數計算：A=1, 10/J/Q/K=0, 其他按面值計算
            4. 只取個位數值(如7+8=15→5)

            [主注賠率]
            莊家(Banker):
              • 以1點勝出：2:1
              • 以4點勝出：平手(Push)
              • 其他點數勝出：1:1

            閒家(Player):
              • 以1點勝出：2:1
              • 以4點勝出：0.5:1
              • 其他點數勝出：1:1

            和局(Tie): 8:1

            [邊注]
            1. 閒家神奇對子(Player Fab Pair):
              • 同花對子：7:1
              • 非同花對子：4:1
              • 同花非對子：1:1
              • 輸牌：失去下注

            2. 莊家神奇對子(Banker Fab Pair):
              • 同花對子：7:1
              • 非同花對子：4:1
              • 同花非對子：1:1
              • 輸牌：失去下注

            3. 閒家神奇4點(P Fabulous 4):
              • 閒家以4點勝出：50:1

            4. 莊家神奇4點(B Fabulous 4):
              • 莊家以4點勝出：25:1
            """

        # 创建自定义弹窗
        win = tk.Toplevel(self)
        win.title("Menu")
        win.geometry("700x650")
        win.resizable(False, False)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(win)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 使用Text组件支持格式
        text_area = tk.Text(
            win, 
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            font=('微软雅黑', 11),
            padx=15,
            pady=15,
            bg='#F0F0F0'
        )
        text_area.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_area.yview)

        # 插入带格式的文本
        text_area.insert(tk.END, instructions)

        # 禁用编辑
        text_area.config(state=tk.DISABLED)

        # 添加关闭按钮
        close_btn = ttk.Button(
            win,
            text="Close",
            command=win.destroy
        )
        close_btn.pack(pady=10)

    def _load_longest_streaks(self):
        """加載最長連勝記錄"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                try:
                    data = json.load(f)
                    # 兼容舊數據格式
                    if isinstance(data, list) and len(data) > 0:
                        data = data[0]
                    
                    # 讀取最長連勝記錄
                    self.longest_streaks['Player'] = data.get('L_Player', 0)
                    self.longest_streaks['Tie'] = data.get('L_Tie', 0)
                    self.longest_streaks['Banker'] = data.get('L_Banker', 0)
                except json.JSONDecodeError:
                    # 文件格式錯誤時使用默認值
                    pass

    def play_sound(self, filename):
        if self.is_muted:
            return
        path = os.path.join(self.sound_path, filename)
        if os.path.exists(path):
            mixer.Sound(path).play()

    def _ensure_data_file(self):
        """确保数据目录和文件存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if not os.path.exists(self.data_file):
            # 创建初始JSON结构 - 直接是一个字典，不是数组
            initial_data = {"Player": 0, "Tie": 0, "Banker": 0}
            with open(self.data_file, 'w') as f:
                json.dump(initial_data, f)

    def save_game_result(self, result):
        """保存遊戲結果到數據文件"""
        # 讀取現有數據
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                try:
                    data = json.load(f)
                    # 如果讀取到的是數組（舊格式），轉換為字典
                    if isinstance(data, list) and len(data) > 0:
                        data = data[0]
                except json.JSONDecodeError:
                    data = {
                        "Player": 0, "Tie": 0, "Banker": 0,
                        "L_Player": 0, "L_Tie": 0, "L_Banker": 0
                    }
        else:
            data = {
                "Player": 0, "Tie": 0, "Banker": 0,
                "L_Player": 0, "L_Tie": 0, "L_Banker": 0
            }
        
        # 更新對應結果
        if result == 'P':
            data["Player"] = int(data.get("Player", 0)) + 1
        elif result == 'T':
            data["Tie"] = int(data.get("Tie", 0)) + 1
        elif result == 'B':
            data["Banker"] = int(data.get("Banker", 0)) + 1
        
        # 更新最長連勝記錄
        data["L_Player"] = self.longest_streaks['Player']
        data["L_Tie"] = self.longest_streaks['Tie']
        data["L_Banker"] = self.longest_streaks['Banker']
        
        # 寫回文件 - 直接保存字典
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

        self.update_pie_chart()

    # 修改 calculate_probabilities 方法
    def calculate_probabilities(self):
        """计算并返回各结果的概率"""
        if not os.path.exists(self.data_file):
            return {'Player': 0, 'Banker': 0, 'Tie': 0}
        
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                # 如果读取到的是数组（旧格式），转换为字典
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]
        except (json.JSONDecodeError, FileNotFoundError):
            return {'Player': 0, 'Banker': 0, 'Tie': 0}
        
        # 确保值是整数
        player_count = int(data.get("Player", 0))
        tie_count = int(data.get("Tie", 0))
        banker_count = int(data.get("Banker", 0))
        
        total = player_count + tie_count + banker_count
        if total == 0:
            return {'Player': 0, 'Banker': 0, 'Tie': 0}
        
        return {
            'Player': player_count / total * 100,
            'Banker': banker_count / total * 100,
            'Tie': tie_count / total * 100
        }
    def update_streak_labels(self):
        """更新最长连胜记录标签"""
        if hasattr(self, 'longest_player_label'):
            self.longest_player_label.config(text=str(self.longest_streaks['Player']))
            self.longest_tie_label.config(text=str(self.longest_streaks['Tie']))
            self.longest_banker_label.config(text=str(self.longest_streaks['Banker']))

    def _load_assets(self):
        card_size = (100, 140)
        suits = ['Club', 'Diamond', 'Heart', 'Spade']
        ranks = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']

        base_dir = os.path.dirname(os.path.abspath(__file__))
        card_dir = os.path.join(base_dir, 'Card')
        
        for suit in suits:
            for rank in ranks:
                # 构建完整文件路径
                filename = f"{suit}{rank}.png"
                path = os.path.join(card_dir, filename)
                try:
                    img = Image.open(path).resize(card_size)
                    self.card_images[(suit, rank)] = ImageTk.PhotoImage(img)
                except Exception as e:
                    print(f"Error loading {path}: {e}")

        back_path = os.path.join(card_dir, 'Background.png')
        try:
            self.back_image = ImageTk.PhotoImage(Image.open(back_path).resize(card_size))
        except Exception as e:
            print(f"Error loading back image: {e}")

    def _initialize_game(self, second):
        # 创建自定义对话框
        dialog = tk.Toplevel(self)
        dialog.title("Cut Card")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.transient(self)  # 设置为主窗口的子窗口
        dialog.grab_set()  # 模态对话框
        
        # 添加标签
        if second:
            tk.Label(dialog, text="Deck finish. \nShuffle and cut the card from 103 to 299", 
                    font=('Arial', 10)).pack(pady=10)
        else:
            tk.Label(dialog, text="Please cut the card from 103 to 299", 
                font=('Arial', 10)).pack(pady=10)
        
        # 添加输入框
        entry = tk.Entry(dialog, font=('Arial', 12), width=10)
        entry.pack(pady=5)
        entry.focus_set()  # 自动聚焦
        
        # 存储结果
        result = [None]  # 使用列表以便在闭包中修改
        self.bigroad_results = []
        
        # 确定按钮回调
        def on_ok():
            try:
                value = entry.get()
                if not value:  # 空输入
                    result[0] = random.randint(103, 299)
                else:
                    value = int(value)
                    if 103 <= value <= 299:
                        result[0] = value
                    else:
                        result[0] = random.randint(103, 299)
                dialog.destroy()
            except ValueError:
                # 非整数输入
                result[0] = random.randint(103, 299)
                dialog.destroy()
        
        # 取消按钮回调
        def on_cancel():
            result[0] = random.randint(103, 299)
            dialog.destroy()
        
        # 添加按钮
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="OK", width=8, command=on_ok).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cancel", width=8, command=on_cancel).pack(side=tk.LEFT, padx=10)
        
        # 绑定Enter键
        dialog.bind('<Return>', lambda e: on_ok())
        
        # 等待对话框关闭
        self.wait_window(dialog)
        
        # 如果用户直接关闭窗口，视为取消
        if result[0] is None:
            result[0] = random.randint(103, 299)
        
        # 初始化游戏
        self.game = Baccarat()
        self.game.create_deck()
        self.game.advanced_shuffle(result[0])
        
        # 重新洗牌时重置
        self.marker_results = []
        self.marker_counts = {
            'Player': 0, 'Banker': 0, 'Tie': 0,
            'Small Tiger': 0, 'Tiger Tie': 0, 'Big Tiger': 0,
            'Panda 8': 0, 'Divine 9': 0, 'Dragon 7': 0,
        }
        self.reset_marker_road()
        self.reset_bigroad()

    def reset_bigroad(self):
        """重置大路数据与视图"""
        self.bigroad_results.clear()
        self.bigroad_results = []
        self._bigroad_occupancy = [
            [False] * self._max_cols for _ in range(self._max_rows)
        ]
        if hasattr(self, 'bigroad_canvas'):
            self.bigroad_canvas.delete('data')

    def reset_marker_road(self):
        """重置珠路图数据"""
        # 清空所有结果
        self.marker_results = []

        # 重置所有统计键（Tiger + EZ 两套都要清零）
        self.marker_counts = {
            'Player': 0,
            'Banker': 0,
            'Tie': 0,
            'Small Tiger': 0,
            'Tiger Tie': 0,
            'Big Tiger': 0,
            'Panda 8': 0,
            'Divine 9': 0,
            'Dragon 7': 0,
            'P Fabulous 4': 0,
            'B Fabulous 4': 0
        }

        # 更新统计标签，如果对应标签存在就把它清为 0
        if hasattr(self, 'player_count_label') and self.player_count_label.winfo_exists():
            # 基本三项
            self.player_count_label.config(text="0")
            self.banker_count_label.config(text="0")
            self.tie_count_label.config(text="0")
            # Tiger 相关
            if hasattr(self, 'stiger_count_label') and self.stiger_count_label.winfo_exists():
                self.stiger_count_label.config(text="0")
                self.ttiger_count_label.config(text="0")
                self.btiger_count_label.config(text="0")
            # EZ 相关
            if hasattr(self, 'panda_count_label') and self.panda_count_label.winfo_exists():
                self.panda_count_label.config(text="0")
                self.divine_count_label.config(text="0")
                self.dragon_count_label.config(text="0")
            # Fabulous 4
            if hasattr(self, 'fab4p_count_label') and self.fab4p_count_label.winfo_exists():
                self.fab4p_count_label.config(text="0")
                self.fab4b_count_label.config(text="0")
            
            # 总计标签
            self.basic_total_label.config(text="0")
            if hasattr(self, 'tiger_total_label' ) and self.tiger_total_label.winfo_exists():
                self.tiger_total_label.config(text="0")
            elif hasattr(self, 'ez_total_label') and self.ez_total_label.winfo_exists():
                self.ez_total_label.config(text="0")
            elif hasattr(self, 'fab4_total_label') and self.fab4_total_label.winfo_exists():
                self.fab4_total_label.config(text="0")
        
        # 重新绘制珠路图网格
        self._draw_marker_grid()

    def _create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame, width=800)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(main_frame, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self._create_control_panel(right_frame)

        self.table_canvas = tk.Canvas(left_frame, bg='#35654d', highlightthickness=0)
        self.table_canvas.pack(fill=tk.BOTH, expand=True)
        self._draw_table_labels()

    def _draw_table_labels(self):
        self.table_canvas.create_line(500, 50, 500, 550, width=3, fill='white', tags='divider')
        self.table_canvas.create_text(250, 30, text="PLAYER", font=('Arial', 24, 'bold'), fill='white')
        self.table_canvas.create_text(750, 30, text="BANKER", font=('Arial', 24, 'bold'), fill='white')

    def _get_card_positions(self, hand_type):
        area = self._player_area if hand_type == "player" else self._banker_area
        hand = self.game.player_hand if hand_type == "player" else self.game.banker_hand
        card_count = len(hand)
        base_x = area[0] + (area[2]-area[0]-100)/2
        positions = []
        for i in range(card_count):
            x = base_x + i*110
            y = area[1]
            if i == 2:
                x = (positions[0][0] + positions[1][0]) / 2
                y = area[1] + 70
            positions.append((x, y))
        return positions
    
    def _create_chip_button(self, parent, text, bg_color):
        size = 60
        canvas = tk.Canvas(parent, width=size, height=size, 
                        highlightthickness=0, background='#D0E7FF')
        
        # 绘制带发光效果的圆形
        chip_id = canvas.create_oval(2, 2, size-2, size-2, 
                                   fill=bg_color, outline='#D0E7FF', width=6)
        
        # 文字颜色计算（保持不变）
        rgb = ImageColor.getrgb(bg_color)
        luminance = 0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]
        text_color = 'white' if luminance < 140 else 'black'
        
        # 添加文字
        canvas.create_text(size/2, size/2, text=text, 
                         fill=text_color, font=('Arial', 12, 'bold'))
        
        # 绑定点击事件
        canvas.bind('<Button-1>', lambda e, t=text: self._set_bet_amount(t, canvas))
        
        # 存储按钮信息
        self.chip_buttons.append({
            'canvas': canvas,
            'chip_id': chip_id,
            'text': text
        })
        return canvas

    def _set_bet_amount(self, chip_text, clicked_canvas):
        # 清除之前选中的发光效果
        if self.selected_chip:
            self.selected_canvas.itemconfig(self.selected_id, outline='#D0E7FF')
        
        # 设置新选中效果
        for chip in self.chip_buttons:
            if chip['canvas'] == clicked_canvas:
                self.selected_canvas = chip['canvas']
                self.selected_id = chip['chip_id']
                chip['canvas'].itemconfig(chip['chip_id'], outline='gold')
                self.selected_chip = chip
                break
        
        # 金额转换逻辑（保持原样）
        if 'K' in chip_text:
            amount = int(chip_text.replace('K', '')) * 1000
        else:
            amount = int(chip_text)
        
        self.selected_bet_amount = amount
        self.current_chip_label.config(text=f"Chips amount: ${amount:,}")

    def _animate_chip_glow(self):
        if not self.selected_chip:
            return
        
        current_outline = self.selected_canvas.itemcget(self.selected_id, 'outline')
        new_color = '#FFD700' if current_outline == 'gold' else 'gold'
        self.selected_canvas.itemconfig(self.selected_id, outline=new_color)
        self.after(500, self._animate_chip_glow)

    def reset_bets(self):
        # Give all current bets back to the balance
        for bet_type, amt in self.current_bets.items():
            self.balance += amt
        # Clear the current bets
        self.current_bets.clear()
        self.current_bet = 0

        # Update all the UI elements
        self.update_balance()                            # refresh balance label
        self.current_bet_label.config(text=f"${0:,}")    # reset bet display

        for btn in self.bet_buttons:
            if hasattr(btn, 'bet_type'):
                original_text = btn.cget("text").split('\n')
                # 恢复初始文本格式（最后一行显示~~）
                new_text = f"{original_text[0]}\n{original_text[1]}\n~~"
                btn.config(text=new_text)

    def update_mode_display(self):
        """更新组合框显示文本"""
        current_value = self.mode_var.get()
        display_text = self.mode_display_map.get(current_value, current_value)
        self.mode_combo.set(display_text)

    # 添加新方法：处理组合框弹出事件
    def on_combobox_popup(self, event):
        """当组合框弹出时更新选项显示文本"""
        # 获取当前值
        current_value = self.mode_var.get()
        
        # 更新下拉列表选项
        self.mode_combo['values'] = [
            self.mode_display_map.get("tiger", "Tiger Baccarat"),
            self.mode_display_map.get("ez", "EZ Baccarat")
        ]
        
        # 设置当前显示文本
        self.mode_combo.set(self.mode_display_map.get(current_value, current_value))

    def _create_control_panel(self, parent):
        # main panel with light-blue background
        control_frame = tk.Frame(parent, bg='#D0E7FF')
        control_frame.pack(pady=20, padx=10, fill=tk.X)

        style = ttk.Style()
        style.configure('Bold.TCombobox', font=('Arial', 15, 'bold'))

        # 余额行 - 保持不变
        balance_frame = tk.Frame(control_frame, bg='#D0E7FF')
        balance_frame.pack(fill=tk.X, pady=10)
        self.balance_label = tk.Label(
            balance_frame,
            text=f"Balance: ${self.balance:,}",
            font=('Arial', 14),
            fg='black',
            bg='#D0E7FF'
        )
        self.balance_label.pack(side=tk.LEFT)
        self.info_button = tk.Button(
            balance_frame,
            text="ℹ️",
            command=self.show_game_instructions,
            bg='#4B8BBE',
            fg='white',
            font=('Arial', 12)
        )
        self.info_button.pack(side=tk.RIGHT, padx=5)
        self.mute_button = tk.Button(
            balance_frame,
            text="🔇 Mute" if not self.is_muted else "🔊 Unmute",
            command=self.toggle_mute,
            bg='#ff6666' if not self.is_muted else '#66ff66',
            font=('Arial', 12),
            width=8
        )
        self.mute_button.pack(side=tk.RIGHT, padx=5)
        
        # ===== 新增：游戏模式切换 =====
        mode_frame = tk.Frame(control_frame, bg='#D0E7FF')
        mode_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            mode_frame, 
            text="Game Mode:", 
            font=('Arial', 15, 'bold'),
            bg='#D0E7FF'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.mode_var = tk.StringVar(value=self.game_mode)
        
        # 定义显示文本和内部值的映射
        self.mode_display_map = {
            "tiger": "Tiger Baccarat",
            "2to1": "2 To 1 Baccarat",
            "ez": "EZ Baccarat",
            "classic": "Classic Baccarat",
            "fabulous4": "Fabulous 4"
        }
        
        # 使用显示文本作为组合框的值
        display_values = [self.mode_display_map["classic"], 
                          self.mode_display_map["2to1"], 
                          self.mode_display_map["tiger"], 
                          self.mode_display_map["ez"],
                          self.mode_display_map["fabulous4"]
                        ]
        
        # 创建组合框 - 使用显示文本作为选项
        self.mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.mode_var,
            values=display_values,
            state='readonly',
            font=('Arial', 15, 'bold'),
            width=15
        )
        self.mode_combo.pack(side=tk.LEFT)
        
        # 设置当前显示文本
        self.mode_combo.set(self.mode_display_map.get(self.game_mode, self.game_mode))
        
        # 绑定选择事件
        self.mode_combo.bind("<<ComboboxSelected>>", self.change_game_mode)

        # ===== 新增部分：视图切换按钮 =====
        view_frame = tk.Frame(control_frame, bg='#D0E7FF')
        view_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.betting_view_btn = tk.Button(
            view_frame, 
            text="Betting", 
            command=self.show_betting_view,
            bg='#4B8BBE',  # 蓝色背景
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.RAISED,
            width=10
        )
        self.betting_view_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.bigroad_view_btn = tk.Button(
            view_frame, text="Static", command=self.show_bigroad_view,
            bg='#888888', fg='white', font=('Arial',10,'bold'),
            relief=tk.FLAT, width=10
        )
        
        self.marker_view_btn = tk.Button(
            view_frame, 
            text="Road", 
            command=self.show_marker_view,
            bg='#888888',  # 灰色背景
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.FLAT,
            width=10
        )
        self.marker_view_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.bigroad_view_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 创建一个统一大小的 view_container
        self.view_container = tk.Frame(control_frame, bg='#D0E7FF')
        self.view_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 1) betting_view
        self.betting_view = tk.Frame(self.view_container, bg='#D0E7FF', width=350)

        # 2) bigroad_view
        self.bigroad_view = tk.Frame(self.view_container, bg='#D0E7FF', width=350)

        # 3) marker_view
        self.marker_view = tk.Frame(self.view_container, bg='#D0E7FF', width=350)

        # 之后调用生成大路和珠路图等方法
        self._populate_betting_view()
        self._create_marker_road()

        # 默认显示下注视图
        self.show_betting_view()

    def change_game_mode(self, event=None):
        """切换游戏模式后，立即重绘并刷新静态统计面板"""
        selected_display = self.mode_combo.get()
        # 将显示文本映射到真实模式值
        real_mode = {
            self.mode_display_map["classic"]: "classic",
            self.mode_display_map["2to1"]: "2to1",
            self.mode_display_map["tiger"]: "tiger",
            self.mode_display_map["ez"]: "ez",
            self.mode_display_map["fabulous4"]: "fabulous4"
        }.get(selected_display, "classic")

        if real_mode != self.game_mode:
            # 只重置下注，不重置珠路图统计
            self.reset_bets()
            self.game_mode = real_mode
            # 重新加载下注按钮布局（注意加上括号）
            self._reload_betting_buttons()

        # —— 立刻销毁旧的静态统计面板并重建 —— #
        for widget in self.bigroad_view.winfo_children():
            widget.destroy()
        self._create_stats_panel(self.bigroad_view)

        # —— 切换模式后，立刻根据现有的 marker_counts 把所有标签刷新一次 —— #
        # 基本三项
        self.player_count_label.config(text=str(self.marker_counts.get('Player', 0)))
        self.banker_count_label.config(text=str(self.marker_counts.get('Banker', 0)))
        self.tie_count_label.config(text=str(self.marker_counts.get('Tie', 0)))

        # 根据当前模式，刷新右侧对应的三行和总计
        if self.game_mode == "tiger":
            # Tiger 模式下显示 Small Tiger / Tiger Tie / Big Tiger
            # 确保对应标签都已经在 _create_stats_panel 中创建
            self.stiger_count_label.config(text=str(self.marker_counts.get('Small Tiger', 0)))
            self.ttiger_count_label.config(text=str(self.marker_counts.get('Tiger Tie', 0)))
            self.btiger_count_label.config(text=str(self.marker_counts.get('Big Tiger', 0)))

            # 更新总计
            basic_total = (
                self.marker_counts.get('Player', 0)
                + self.marker_counts.get('Tie', 0)
                + self.marker_counts.get('Banker', 0)
            )
            tiger_total = (
                self.marker_counts.get('Small Tiger', 0)
                + self.marker_counts.get('Tiger Tie', 0)
                + self.marker_counts.get('Big Tiger', 0)
            )
            self.basic_total_label.config(text=str(basic_total))
            self.tiger_total_label.config(text=str(tiger_total))

        elif self.game_mode == "ez":  # EZ 模式
            # EZ 模式下显示 Panda 8 / Divine 9 / Dragon 7
            self.panda_count_label.config(text=str(self.marker_counts.get('Panda 8', 0)))
            self.divine_count_label.config(text=str(self.marker_counts.get('Divine 9', 0)))
            self.dragon_count_label.config(text=str(self.marker_counts.get('Dragon 7', 0)))

            # 更新总计
            basic_total = (
                self.marker_counts.get('Player', 0)
                + self.marker_counts.get('Tie', 0)
                + self.marker_counts.get('Banker', 0)
            )
            ez_total = (
                self.marker_counts.get('Panda 8', 0)
                + self.marker_counts.get('Divine 9', 0)
                + self.marker_counts.get('Dragon 7', 0)
            )
            self.basic_total_label.config(text=str(basic_total))
            self.ez_total_label.config(text=str(ez_total))  

        elif self.game_mode == "fabulous4":
            if hasattr(self, 'fab4p_count_label'):
                self.fab4p_count_label.config(text=str(self.marker_counts.get('P Fabulous 4', 0)))
                self.fab4b_count_label.config(text=str(self.marker_counts.get('B Fabulous 4', 0)))
            fab4_total = (
                self.marker_counts.get('P Fabulous 4', 0) +
                self.marker_counts.get('B Fabulous 4', 0)
            )
            self.fab4_total_label.config(text=str(fab4_total))

        self._update_marker_road()


    def _reload_betting_buttons(self):
        """根据当前模式重新加载下注按钮"""
        # 清除所有按钮和状态
        self.selected_chip = None
        self.chip_buttons = []
        self.bet_buttons = []
        
        # 销毁 betting_view 中的所有组件
        for widget in self.betting_view.winfo_children():
            widget.destroy()
        
        # 重新创建下注视图
        self._populate_betting_view()
        
        # 确保视图正确显示
        if self.view_mode == "betting":
            self.show_betting_view()
        
        # 重新绑定回车键
        self.bind('<Return>', lambda e: self.start_game())

    def show_betting_view(self):
        """显示下注区域视图"""
        # 切换按钮样式
        self.betting_view_btn.config(relief=tk.RAISED, bg='#4B8BBE')
        self.bigroad_view_btn.config(relief=tk.RAISED, bg='#888888')
        self.marker_view_btn.config(relief=tk.FLAT, bg='#888888')
        
        # 隐藏珠路图视图，显示下注视图
        self.marker_view.pack_forget()
        self.bigroad_view.pack_forget()
        self.betting_view.pack(fill=tk.BOTH, expand=True)
        self.view_mode = "betting"

    def show_bigroad_view(self):
        self.betting_view.pack_forget()
        self.marker_view.pack_forget()
        self.bigroad_view.pack(fill=tk.BOTH, expand=True)
        self.betting_view_btn.config(relief=tk.FLAT, bg='#888888')
        self.bigroad_view_btn.config(relief=tk.RAISED, bg='#4B8BBE')
        self.marker_view_btn.config(relief=tk.FLAT, bg='#888888')
        self.view_mode = "bigroad"

    def show_marker_view(self):
        """显示珠路图视图"""
        # 切换按钮样式
        self.betting_view_btn.config(relief=tk.FLAT, bg='#888888')
        self.bigroad_view_btn.config(relief=tk.RAISED, bg='#888888')
        self.marker_view_btn.config(relief=tk.RAISED, bg='#4B8BBE')
        
        # 隐藏下注视图，显示珠路图视图
        self.betting_view.pack_forget()
        self.bigroad_view.pack_forget()
        self.marker_view.pack(fill=tk.BOTH, expand=True)
        self.view_mode = "marker"

    def _create_marker_road(self):
        """创建包含 Big Road + Marker Road + 统计面板的复合视图"""
        # ↓↓↓ ① 整合 Big Road 部分 ↓↓↓
        # （原本在 _create_bigroad_view 中的代码，现在搬到这里；parent 改为 marker_frame）
        # 初始化 bigroad 数据
        self.bigroad_results.clear
        self.bigroad_results = []
        self._max_rows = 6
        self._max_cols = 50
        self._bigroad_occupancy = [
            [False] * self._max_cols for _ in range(self._max_rows)
        ]

        # 基本尺寸
        cell    = 25    # 每个格子内部大小
        pad     = 2     # 格子间距
        label_w = 30    # 左侧行号列宽
        label_h = 20    # 顶部列号行高

        # 计算总尺寸
        total_w = label_w + self._max_cols * (cell + pad) + pad
        total_h = label_h + self._max_rows * (cell + pad) + pad

        # 创建 Big Road 的容器——使用同一个 marker_frame 作为父级
        marker_frame = tk.Frame(self.marker_view, bg='#D0E7FF')
        marker_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ──【Big Road 标题】（可选，如果想给 Big Road 单独一个标题，可以加上）
        big_title = tk.Label(
            marker_frame,
            text="Big Road",
            font=('Arial', 14, 'bold'),
            bg='#D0E7FF'
        )
        big_title.pack(pady=(0, 10))  # 与上方留一些空隙

        # ──【Big Road 画布及滚动条】
        big_frame = tk.Frame(marker_frame, bg='#D0E7FF')
        big_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)

        hbar = tk.Scrollbar(big_frame, orient=tk.HORIZONTAL)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.bigroad_canvas = tk.Canvas(
            big_frame,
            bg='#FFFFFF',
            width=290,   # 初始可见宽度，可根据窗口调整
            height=total_h,
            xscrollcommand=hbar.set,
            scrollregion=(0, 0, total_w, total_h),
            highlightthickness=0
        )
        self.bigroad_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        hbar.config(command=self.bigroad_canvas.xview)

        # 画 Big Road 顶部列号
        for c in range(self._max_cols):
            x = label_w + pad + c * (cell + pad) + cell / 2
            y = label_h / 2
            self.bigroad_canvas.create_text(
                x, y,
                text=str(c + 1),
                font=('Arial', 8),
                tags=('grid',)
            )

        # 画 Big Road 左侧行号
        for r in range(self._max_rows):
            x = label_w / 2
            y = label_h + pad + r * (cell + pad) + cell / 2
            self.bigroad_canvas.create_text(
                x, y,
                text=str(r + 1),
                font=('Arial', 8),
                tags=('grid',)
            )

        # 画 Big Road 网格
        for c in range(self._max_cols):
            for r in range(self._max_rows):
                x1 = label_w + pad + c * (cell + pad)
                y1 = label_h + pad + r * (cell + pad)
                x2 = x1 + cell
                y2 = y1 + cell
                self.bigroad_canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline='#888888', fill='#FFFFFF',
                    tags=('grid',)
                )

        # ↓↓↓ ② 紧接着绘制 Marker Road ↓↓↓
        # 添加 Marker Road 的标题
        marker_title = tk.Label(
            marker_frame, 
            text="Marker Road", 
            font=('Arial', 14, 'bold'),
            bg='#D0E7FF'
        )
        marker_title.pack(pady=(20, 10))  # 与 Big Road 画布之间留出一些空间
        
        # 创建 Marker Road 画布
        self.marker_canvas = tk.Canvas(
            marker_frame, 
            bg='#D0E7FF',
            highlightthickness=0
        )
        self.marker_canvas.pack(fill=tk.BOTH, expand=True)

        # ↓↓↓ ③ 最后再绘制“统计面板”↓↓↓
        # 注意：这里调用依然是 self._create_stats_panel(self.bigroad_view)
        #      但将它放在 Marker Road 视图的逻辑末尾，也就是 Big Road + Marker Road 画布 之后。
        self._create_stats_panel(self.bigroad_view)

    def _create_stats_panel(self, parent):
        """创建统计信息面板 - 使用网格布局实现表格效果"""
        # 主框架
        stats_frame = tk.Frame(parent, bg='#D0E7FF')
        stats_frame.pack(fill=tk.X, pady=(10, 0), padx=10)
        
        # 创建表格样式的框架
        table_frame = tk.Frame(stats_frame, bg='#D0E7FF')
        table_frame.pack(fill=tk.X)
        
        # ===== 表头 =====
        # 左侧永远显示 BASIC 列
        basic_label = tk.Label(
            table_frame, text="BASIC",
            font=('Arial', 13, 'bold'),
            bg='#D0E7FF', width=12
        )

        if self.game_mode == "classic" or self.game_mode == "2to1":
            # 如果是 classic 模式，让 BASIC 占满所有列并水平居中
            basic_label.grid(row=0, column=0, columnspan=3, sticky='ew')
            ttk.Separator(table_frame, orient=tk.HORIZONTAL).grid(
                row=5, column=0, columnspan=1, sticky='ew', pady=2
            )
            tk.Label(
                table_frame, text="Total:",
                font=('Arial', 13, 'bold'), bg='#D0E7FF', anchor='w'
            ).grid(row=6, column=0, sticky='w', pady=(2, 5))
            
            self.basic_total_label = tk.Label(
                table_frame, text="0",
                font=('Arial', 13, 'bold'), bg='#D0E7FF', width=5, anchor='e'
            )
            self.basic_total_label.grid(row=6, column=0, sticky='e', pady=(2, 5))
        else:
            # 非 classic 时，保持原来的左对齐和内边距
            basic_label.grid(row=0, column=0, sticky='w', padx=(0, 10))

        # 右侧列要根据当前模式决定标题：Tiger 模式下显示 "TIGER"，EZ 模式下显示 "EZ"
        if self.game_mode == "tiger":
            right_header = "TIGER"
        elif self.game_mode == "ez":
            right_header = "EZ"
        elif self.game_mode == "fabulous4":
            right_header = "Fabulous 4"
        else:
            right_header = None

        if right_header:
            tk.Label(
                table_frame, text=right_header,
                font=('Arial', 13, 'bold'),
                bg='#D0E7FF', width=12
            ).grid(row=0, column=2, sticky='w')  # 放在第 2 列
        
        # 表头分隔线
        ttk.Separator(table_frame, orient=tk.HORIZONTAL).grid(
            row=1, column=0, columnspan=3, sticky='ew', pady=2  # 改为跨越3列
        )
        
        # ===== 内容区域 =====
        # 在BASIC和Tiger之间添加垂直分隔线（贯穿整个内容区域）
        vertical_separator = ttk.Separator(table_frame, orient=tk.VERTICAL)
        vertical_separator.grid(
            row=2, column=1, rowspan=5, sticky='ns', padx=5, pady=2
        )

        # ── 左侧 BASIC 列（不变） ── #
        # Player
        tk.Label(
            table_frame, text="Player:",
            font=('Arial', 12), bg='#D0E7FF', anchor='w'
        ).grid(row=2, column=0, sticky='w', pady=2)
        self.player_count_label = tk.Label(
            table_frame, text="0",
            font=('Arial', 12), bg='#D0E7FF', width=5, anchor='e'
        )
        self.player_count_label.grid(row=2, column=0, sticky='e')

        # Tie
        tk.Label(
            table_frame, text="Tie:",
            font=('Arial', 12), bg='#D0E7FF', anchor='w'
        ).grid(row=3, column=0, sticky='w', pady=2)
        self.tie_count_label = tk.Label(
            table_frame, text="0",
            font=('Arial', 12), bg='#D0E7FF', width=5, anchor='e'
        )
        self.tie_count_label.grid(row=3, column=0, sticky='e')

        # Banker
        tk.Label(
            table_frame, text="Banker:",
            font=('Arial', 12), bg='#D0E7FF', anchor='w'
        ).grid(row=4, column=0, sticky='w', pady=2)
        self.banker_count_label = tk.Label(
            table_frame, text="0",
            font=('Arial', 12), bg='#D0E7FF', width=5, anchor='e'
        )
        self.banker_count_label.grid(row=4, column=0, sticky='e')

        # ── 右侧 列，根据模式分开布局 ── #
        if self.game_mode == "tiger":
            # Tiger 模式：显示 Small Tiger、Tiger Tie、Big Tiger 三行
            tk.Label(
                table_frame, text="Small Tiger:",
                font=('Arial', 12), bg='#D0E7FF', anchor='w'
            ).grid(row=2, column=2, sticky='w', pady=2)
            self.stiger_count_label = tk.Label(
                table_frame, text="0",
                font=('Arial', 12), bg='#D0E7FF', width=5, anchor='e'
            )
            self.stiger_count_label.grid(row=2, column=2, sticky='e')

            tk.Label(
                table_frame, text="Tiger Tie:",
                font=('Arial', 12), bg='#D0E7FF', anchor='w'
            ).grid(row=3, column=2, sticky='w', pady=2)
            self.ttiger_count_label = tk.Label(
                table_frame, text="0",
                font=('Arial', 12), bg='#D0E7FF', width=5, anchor='e'
            )
            self.ttiger_count_label.grid(row=3, column=2, sticky='e')
            tk.Label(
                table_frame, text="Big Tiger:",
                font=('Arial', 12), bg='#D0E7FF', anchor='w'
            ).grid(row=4, column=2, sticky='w', pady=2)
            self.btiger_count_label = tk.Label(
                table_frame, text="0",
                font=('Arial', 12), bg='#D0E7FF', width=5, anchor='e'
            )
            self.btiger_count_label.grid(row=4, column=2, sticky='e')
        elif self.game_mode == "ez":  # EZ 模式：显示 Panda 8、Divine 9、Dragon 7 三行
            tk.Label(
                table_frame, text="Panda 8:",
                font=('Arial', 12), bg='#D0E7FF', anchor='w'
            ).grid(row=2, column=2, sticky='w', pady=2)
            self.panda_count_label = tk.Label(
                table_frame, text="0",
                font=('Arial', 12), bg='#D0E7FF', width=5, anchor='e'
            )
            self.panda_count_label.grid(row=2, column=2, sticky='e')

            tk.Label(
                table_frame, text="Divine 9:",
                font=('Arial', 12), bg='#D0E7FF', anchor='w'
            ).grid(row=3, column=2, sticky='w', pady=2)
            self.divine_count_label = tk.Label(
                table_frame, text="0",
                font=('Arial', 12), bg='#D0E7FF', width=5, anchor='e'
            )
            self.divine_count_label.grid(row=3, column=2, sticky='e')

            tk.Label(
                table_frame, text="Dragon 7:",
                font=('Arial', 12), bg='#D0E7FF', anchor='w'
            ).grid(row=4, column=2, sticky='w', pady=2)
            self.dragon_count_label = tk.Label(
                table_frame, text="0",
                font=('Arial', 12), bg='#D0E7FF', width=5, anchor='e'
            )
            self.dragon_count_label.grid(row=4, column=2, sticky='e')

        elif self.game_mode == "fabulous4":  # 添加这个分支
            # P Fabulous 4
            tk.Label(
                table_frame, text="P Fabulous 4:",
                font=('Arial', 12), bg='#D0E7FF', anchor='w'
            ).grid(row=2, column=2, sticky='w', pady=2)
            self.fab4p_count_label = tk.Label(
                table_frame, text="0",
                font=('Arial', 12), bg='#D0E7FF', width=5, anchor='e'
            )
            self.fab4p_count_label.grid(row=2, column=2, sticky='e')
            
            # B Fabulous 4
            tk.Label(
                table_frame, text="B Fabulous 4:",
                font=('Arial', 12), bg='#D0E7FF', anchor='w'
            ).grid(row=3, column=2, sticky='w', pady=2)
            self.fab4b_count_label = tk.Label(
                table_frame, text="0",
                font=('Arial', 12), bg='#D0E7FF', width=5, anchor='e'
            )
            self.fab4b_count_label.grid(row=3, column=2, sticky='e')
            
            # 不需要第三行，留空
            ttk.Separator(table_frame, orient=tk.HORIZONTAL).grid(
                row=5, column=0, columnspan=3, sticky='ew', pady=2  # 跨越3列
            )
        
        # ===== 总计行 =====
        # BASIC 总计
        ttk.Separator(table_frame, orient=tk.HORIZONTAL).grid(
            row=5, column=0, columnspan=3, sticky='ew', pady=2
        )

        # BASIC 总计（所有模式都需要）
        tk.Label(
            table_frame, text="Total:",
            font=('Arial', 13, 'bold'), bg='#D0E7FF', anchor='w'
        ).grid(row=6, column=0, sticky='w', pady=(2, 5))
        self.basic_total_label = tk.Label(
            table_frame, text="0",
            font=('Arial', 13, 'bold'), bg='#D0E7FF', width=5, anchor='e'
        )
        self.basic_total_label.grid(row=6, column=0, sticky='e', pady=(2, 5))

        # 右侧列总计：根据模式决定是 tiger_total_label 还是 ez_total_label
        if self.game_mode == "tiger" or self.game_mode == "ez" or self.game_mode == "fabulous4":
            tk.Label(
                table_frame, text="Total:",
                font=('Arial', 13, 'bold'), bg='#D0E7FF', anchor='w'
            ).grid(row=6, column=2, sticky='w', pady=(2, 5))

        if self.game_mode == "tiger":
            self.tiger_total_label = tk.Label(
                table_frame, text="0",
                font=('Arial', 13, 'bold'), bg='#D0E7FF', width=5, anchor='e'
            )
            self.tiger_total_label.grid(row=6, column=2, sticky='e', pady=(2, 5))
        elif self.game_mode == "ez":
            self.ez_total_label = tk.Label(
                table_frame, text="0",
                font=('Arial', 13, 'bold'), bg='#D0E7FF', width=5, anchor='e'
            )
            self.ez_total_label.grid(row=6, column=2, sticky='e', pady=(2, 5))
        elif self.game_mode == "fabulous4":  # 添加这个分支
            self.fab4_total_label = tk.Label(
                table_frame, text="0",
                font=('Arial', 13, 'bold'), bg='#D0E7FF', width=5, anchor='e'
            )
            self.fab4_total_label.grid(row=6, column=2, sticky='e', pady=(2, 5))
            
            # 现在安全更新值
            fab4_total = (
                self.marker_counts.get('P Fabulous 4', 0) +
                self.marker_counts.get('B Fabulous 4', 0)
            )
            self.fab4_total_label.config(text=str(fab4_total))
        
        # 配置列权重，使BASIC和Tiger列宽度相等，中间列固定宽度
        if self.game_mode == "classic" or self.game_mode == "2to1":
            table_frame.columnconfigure(0, weight=1, uniform="group")
        else:
            table_frame.columnconfigure(0, weight=1, uniform="group")
            table_frame.columnconfigure(1, weight=0, minsize=10)  # 中间列用于分隔线
            table_frame.columnconfigure(2, weight=1, uniform="group")
        
        # 添加外边框
        ttk.Separator(stats_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(10, 10))

        pie_frame = tk.Frame(stats_frame, bg='#D0E7FF')
        pie_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 标题
        tk.Label(
            pie_frame, text="History Distribution", 
            font=('Arial', 16, 'bold'), 
            bg='#D0E7FF'
        ).pack(pady=(0, 5))
        
        # 创建饼图画布
        self.pie_canvas = tk.Canvas(
            pie_frame, 
            width=150, 
            height=150,
            bg='#D0E7FF',
            highlightthickness=0
        )
        self.pie_canvas.pack(side=tk.LEFT, padx=(0, 10))

        # 创建一个空行（占位符） - 新增这行
        tk.Frame(pie_frame, height=30, bg='#D0E7FF').pack(side=tk.TOP, fill=tk.X)

        # 创建百分比标签框架 - 位置调整
        percent_frame = tk.Frame(pie_frame, bg='#D0E7FF')
        percent_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(10, 0))

        # 创建右侧百分比标签框架
        percent_frame = tk.Frame(pie_frame, bg='#D0E7FF')
        percent_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建三个百分比标签
        self.player_percent_label = tk.Label(
            percent_frame,
            text="PLAYER: 0.0%",
            font=('Arial', 12),
            bg='#D0E7FF',
            fg='#4444ff',  # 蓝色
            anchor='w'
        )
        self.player_percent_label.pack(fill=tk.X, pady=2)

        self.tie_percent_label = tk.Label(
            percent_frame,
            text="TIE: 0.0%",
            font=('Arial', 12),
            bg='#D0E7FF',
            fg="#00ff00",  # 绿色
            anchor='w'
        )
        self.tie_percent_label.pack(fill=tk.X, pady=2)

        self.banker_percent_label = tk.Label(
            percent_frame,
            text="BANKER: 0.0%",
            font=('Arial', 12),
            bg='#D0E7FF',
            fg='#ff4444',  # 红色
            anchor='w'
        )
        self.banker_percent_label.pack(fill=tk.X, pady=2)

        ttk.Separator(stats_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=2)

        # 在饼图下方添加最长连胜记录
        streak_frame = tk.Frame(stats_frame, bg='#D0E7FF')
        streak_frame.pack(fill=tk.X, pady=(15, 5))
        
        # 标题 - 居中显示
        tk.Label(
            streak_frame, text="Longest Winning Streak", 
            font=('Arial', 14, 'bold'), 
            bg='#D0E7FF'
        ).pack(fill=tk.X, pady=(5, 5))  # 使用fill=tk.X使标签占据整个宽度
        
        # 创建记录显示框架
        record_frame = tk.Frame(streak_frame, bg='#D0E7FF')
        record_frame.pack(fill=tk.X, padx=10)
        
        # 使用网格布局使三个记录水平居中
        # PLAYER 记录
        player_frame = tk.Frame(record_frame, bg='#D0E7FF')
        player_frame.grid(row=0, column=0, padx=10)
        tk.Label(
            player_frame, text="PLAYER:", 
            font=('Arial', 12), 
            bg='#D0E7FF', fg='#4444ff'
        ).pack(side=tk.LEFT)
        self.longest_player_label = tk.Label(
            player_frame, text=str(self.longest_streaks['Player']),
            font=('Arial', 12, 'bold'), 
            bg='#D0E7FF'
        )
        self.longest_player_label.pack(side=tk.LEFT)
        
        # TIE 记录
        tie_frame = tk.Frame(record_frame, bg='#D0E7FF')
        tie_frame.grid(row=0, column=1, padx=10)
        tk.Label(
            tie_frame, text="TIE:", 
            font=('Arial', 12), 
            bg='#D0E7FF', fg='#00ff00'
        ).pack(side=tk.LEFT)
        self.longest_tie_label = tk.Label(
            tie_frame, text=str(self.longest_streaks['Tie']),
            font=('Arial', 12, 'bold'), 
            bg='#D0E7FF'
        )
        self.longest_tie_label.pack(side=tk.LEFT)
        
        # BANKER 记录
        banker_frame = tk.Frame(record_frame, bg='#D0E7FF')
        banker_frame.grid(row=0, column=2, padx=10)
        tk.Label(
            banker_frame, text="BANKER:", 
            font=('Arial', 12), 
            bg='#D0E7FF', fg='#ff4444'
        ).pack(side=tk.LEFT)
        self.longest_banker_label = tk.Label(
            banker_frame, text=str(self.longest_streaks['Banker']),
            font=('Arial', 12, 'bold'), 
            bg='#D0E7FF'
        )
        self.longest_banker_label.pack(side=tk.LEFT)
        
        # 配置网格列权重使内容居中
        record_frame.columnconfigure(0, weight=1)
        record_frame.columnconfigure(1, weight=1)
        record_frame.columnconfigure(2, weight=1)
        
        # 添加外边框
        ttk.Separator(stats_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=2)
        
        # 初始绘制饼图
        self.update_pie_chart()
        
    def update_pie_chart(self):
        # 清除现有内容
        self.pie_canvas.delete('all')
        
        # 计算概率
        probabilities = self.calculate_probabilities()
        
        # 更新百分比标签
        self.player_percent_label.config(text=f"PLAYER: {probabilities['Player']:.2f}%")
        self.tie_percent_label.config(text=f"TIE: {probabilities['Tie']:.2f}%")
        self.banker_percent_label.config(text=f"BANKER: {probabilities['Banker']:.2f}%")
        
        # 饼图参数 - 中心点调整到新画布中心
        center_x, center_y = 75, 75  # 因为画布宽度从200改为150
        radius = 50
        
        # 如果没有数据，显示空饼图
        if sum(probabilities.values()) == 0:
            self.pie_canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                fill='#888888',
                outline=''
            )
            self.pie_canvas.create_text(
                center_x, center_y,
                text="No Data",
                font=('Arial', 10)
            )
            return
        
        # 初始化起始角度
        start_angle = 0  # 添加这行初始化变量
        
        # 绘制饼图
        # Player 部分
        player_angle = 360 * probabilities['Player'] / 100
        self.pie_canvas.create_arc(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            start=start_angle,
            extent=player_angle,
            fill='#4444ff',
            outline=''
        )
        start_angle += player_angle
        
        # Banker 部分
        banker_angle = 360 * probabilities['Banker'] / 100
        self.pie_canvas.create_arc(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            start=start_angle,
            extent=banker_angle,
            fill='#ff4444',
            outline=''
        )
        start_angle += banker_angle
        
        # Tie 部分
        tie_angle = 360 * probabilities['Tie'] / 100
        self.pie_canvas.create_arc(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            start=start_angle,
            extent=tie_angle,
            fill='#00ff00',
            outline=''
        )
        
        # 中心空白圆（甜甜圈效果）
        self.pie_canvas.create_oval(
            center_x - radius/2, center_y - radius/2,
            center_x + radius/2, center_y + radius/2,
            fill='#D0E7FF',
            outline=''
        )

    def _draw_marker_grid(self):
        """绘制珠路图网格"""
        # 清除现有内容
        self.marker_canvas.delete('all')
        
        # 网格参数
        rows, cols = 6, 11
        cell_size = 20
        padding = 5
        
        # 计算画布所需大小
        width = cols * (cell_size + padding) + padding
        height = rows * (cell_size + padding) + padding
        
        # 设置画布大小
        self.marker_canvas.config(width=width, height=height)
        
        # 绘制网格
        for col in range(cols):
            for row in range(rows):
                x1 = padding + col * (cell_size + padding)
                y1 = padding + row * (cell_size + padding)
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                
                self.marker_canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline='#888888',
                    fill='#D0E7FF'
                )

    def add_marker_result(self, winner, is_natural=False, is_stiger=False, is_btiger=False, 
                          player_hand_len=0, banker_hand_len=0, player_score=0, banker_score=0):
        """添加新的珠路图结果"""
        # 如果珠路图已满（72个点），移除最旧的一行数据
        if len(self.marker_results) >= self.max_marker_rows * self.max_marker_cols:
            # 移除最旧的一行（6个点）
            for _ in range(self.max_marker_rows):
                if self.marker_results:
                    self.marker_results.pop(0)
        
        # 先更新 Player/Tie/Banker 基本计数
        self.marker_counts[winner] += 1
        
        # 更新 Tiger 模式下的 stiger/btiger
        if winner == 'Banker' and (is_stiger or is_btiger):
            if is_stiger:
                self.marker_counts['Small Tiger'] += 1
            if is_btiger:
                self.marker_counts['Big Tiger'] += 1
        elif winner == 'Tie' and is_stiger:  # Tiger Tie
            self.marker_counts['Tiger Tie'] += 1
        
        # 存储结果到 marker_results
        self.marker_results.append((
            winner, is_natural, is_stiger, is_btiger,
            player_hand_len, banker_hand_len,
            player_score, banker_score
        ))
        
        # 如果触发 EZ 模式下的 Panda 8/Divine 9/Dragon 7，则累加对应键
        if winner == 'Player' and player_hand_len == 3 and player_score == 8 and banker_score < 8:
            self.marker_counts['Panda 8'] += 1

        if (player_score == 9 or banker_score == 9) and (player_hand_len == 3 or banker_hand_len == 3):
            self.marker_counts['Divine 9'] += 1

        if winner == 'Banker' and banker_hand_len == 3 and banker_score == 7 and player_score < 7:
            self.marker_counts['Dragon 7'] += 1

        if self.game_mode == "fabulous4":
            if winner == 'Player' and player_score == 4:
                self.marker_counts['P Fabulous 4'] += 1
            elif winner == 'Banker' and banker_score == 4:
                self.marker_counts['B Fabulous 4'] += 1
        
        # 更新顶部的 Player/Tie/Banker 标签
        self.player_count_label.config(text=str(self.marker_counts['Player']))
        self.banker_count_label.config(text=str(self.marker_counts['Banker']))
        self.tie_count_label.config(text=str(self.marker_counts['Tie']))

        # 根据当前模式，更新右侧统计面板对应的标签和值
        if self.game_mode == "tiger":
            if hasattr(self, 'stiger_count_label'):
                self.stiger_count_label.config(text=str(self.marker_counts['Small Tiger']))
                self.ttiger_count_label.config(text=str(self.marker_counts['Tiger Tie']))
                self.btiger_count_label.config(text=str(self.marker_counts['Big Tiger']))
            tiger_total = (
                self.marker_counts['Small Tiger'] +
                self.marker_counts['Tiger Tie'] +
                self.marker_counts['Big Tiger']
            )
            self.tiger_total_label.config(text=str(tiger_total))
        elif self.game_mode == "ez":
            if hasattr(self, 'panda_count_label'):
                self.panda_count_label.config(text=str(self.marker_counts['Panda 8']))
                self.divine_count_label.config(text=str(self.marker_counts['Divine 9']))
                self.dragon_count_label.config(text=str(self.marker_counts['Dragon 7']))
            ez_total = (
                self.marker_counts['Panda 8'] +
                self.marker_counts['Divine 9'] +
                self.marker_counts['Dragon 7']
            )
            self.ez_total_label.config(text=str(ez_total))
        elif self.game_mode == "fabulous4":
            if hasattr(self, 'fab4p_count_label') and self.fab4p_count_label.winfo_exists():
                self.fab4p_count_label.config(text=str(self.marker_counts['P Fabulous 4']))
                self.fab4b_count_label.config(text=str(self.marker_counts['B Fabulous 4']))
            fab4_total = (
                self.marker_counts['P Fabulous 4'] +
                self.marker_counts['B Fabulous 4']
            )
            self.fab4_total_label.config(text=str(fab4_total))
        
        # 计算并更新总计
        basic_total = (
            self.marker_counts['Player'] +
            self.marker_counts['Tie'] +
            self.marker_counts['Banker']
        )
        self.basic_total_label.config(text=str(basic_total))
        
        # 重新绘制珠路图
        self._update_marker_road()

    def _update_marker_road(self):
        """更新珠路图显示"""
        # 保留网格线，只删除圆点
        self.marker_canvas.delete('dot')  # 只删除圆点，保留网格
        
        # 网格参数
        rows, cols = self.max_marker_rows, self.max_marker_cols
        cell_size = 20
        padding = 5
        
        # 计算起始索引（如果结果超过72个，只显示最近的72个）
        start_idx = max(0, len(self.marker_results) - rows * cols)
        
        # 绘制圆点
        for idx, result in enumerate(self.marker_results[start_idx:]):
            if idx >= rows * cols:  # 超过网格容量
                break
                
            col = idx // rows
            row = idx % rows
            
            # 计算单元格位置
            x1 = padding + col * (cell_size + padding)
            y1 = padding + row * (cell_size + padding)
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            
            # 计算圆点位置
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            radius = cell_size * 0.4
            
            # 根据结果绘制圆点
            (winner, is_natural, is_stiger, is_btiger, player_hand_len, banker_hand_len, player_score, banker_score) = result
            
            outline_color = ''
            if self.game_mode == "classic" or self.game_mode == "2to1" or self.game_mode == "fabulous4":
                if winner == 'Player':
                    color = "#0091FF" if is_natural else '#0000FF'  # 浅蓝(例牌)或深蓝
                    text = "P"
                    text_color = 'white'
                    outline_color = '#0000FF'
                elif winner == 'Banker':
                    text = "B"
                    text_color = 'white'
                    color = "#E06800" if is_natural else '#FF0000'
                    outline_color = '#FF0000'
                else:  # Tie
                    color = '#00FF00'
                    text = "T"
                    text_color = 'black'
            elif self.game_mode == "tiger":
                if winner == 'Player':
                    color = "#0091FF" if is_natural else '#0000FF'  # 浅蓝(例牌)或深蓝
                    text = "P"
                    text_color = 'white'
                    outline_color = '#0000FF'
                elif winner == 'Banker':
                    if banker_score == 6:
                        if banker_hand_len == 2:
                            color = '#FF0000'
                            text_color = 'white'
                            text = "ST"
                        elif banker_hand_len == 3:
                            text = "BT"
                            color = '#FF0000'
                            text_color = 'white'
                    else:
                        text = "B"
                        text_color = 'white'
                        color = "#E06800" if is_natural else '#FF0000'
                        outline_color = '#FF0000'
                else:  # Tie
                    color = '#00FF00'
                    if is_stiger:
                        text = "TT"
                    else:
                        text = "T"
                    text_color = 'black'

            elif self.game_mode == "ez":
                if winner == 'Player':
                    if player_hand_len == 3 and player_score == 8:
                        color = "#FFFFFF"  # 浅蓝(例牌)或深蓝
                        text = "8"
                        text_color = 'black'
                    else:
                        color = "#0091FF" if is_natural else '#0000FF'  # 浅蓝(例牌)或深蓝
                        text = "P"
                        text_color = 'white'
                    outline_color = '#0000FF'
                elif winner == 'Banker':
                    if banker_hand_len == 3 and banker_score == 7:
                        text = "7"
                        color = '#FFFF00'
                        text_color = 'black'
                        outline_color = '#FF0000'
                    else:
                        text = "B"
                        text_color = 'white'
                        color = "#E06800" if is_natural else '#FF0000'
                        outline_color = '#FF0000'
                else:  # Tie
                    color = '#00FF00'
                    text = "T"
                    text_color = 'black'
                
            self.marker_canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                fill=color,
                outline=outline_color,
                width=0.1,  
                tags='dot'
            )

            if is_stiger or is_btiger and self.game_mode == "tiger":
                font_size = 7
            else:
                font_size = 8

            self.marker_canvas.create_text(
                center_x, center_y,
                text=text,
                fill=text_color,
                font=('Arial', font_size, 'bold'),
                tags='dot'
            )

    def read_data_file(self):
        """读取数据文件内容"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return f.read().strip()
        return ''
        
    def _populate_betting_view(self):
        """将所有的控制面板内容移动到betting_view中"""
        # 筹码区
        chips_frame = tk.Frame(self.betting_view, bg='#D0E7FF')
        chips_frame.pack(pady=5)
        row1 = tk.Frame(chips_frame, bg='#D0E7FF')
        row1.pack()
        for text, bg_color in [
            ('25', '#00ff00'),
            ('100', '#000000'),
            ('200', '#0000ff'),
            ('500', "#FF7DDA"),
            ('1K', '#ffffff')
        ]:
            btn = self._create_chip_button(row1, text, bg_color)
            btn.pack(side=tk.LEFT, padx=2)
        row2 = tk.Frame(chips_frame, bg='#D0E7FF')
        row2.pack(pady=3)
        for text, bg_color in [
            ('2K', '#0000ff'),
            ('5K', '#ff0000'),
            ('10K', '#800080'),
            ('20K', '#ffa500'),
            ('50K', '#006400')
        ]:
            btn = self._create_chip_button(row2, text, bg_color)
            btn.pack(side=tk.LEFT, padx=2)

        # pre-select default chip and start glow
        for chip in self.chip_buttons:
            if chip['text'] == '1K':
                self.selected_canvas = chip['canvas']
                self.selected_id = chip['chip_id']
                chip['canvas'].itemconfig(chip['chip_id'], outline='gold')
                self.selected_chip = chip
                # 确保设置了金额
                self.selected_bet_amount = 1000  # 明确设置金额
                break

        # 当前选中筹码显示
        self.current_chip_label = tk.Label(
            self.betting_view,
            text="Current Chip: $1,000",
            font=('Arial', 12),
            fg='black',
            bg='#D0E7FF'
        )
        self.current_chip_label.pack(pady=5)

        # 赔率按钮区
        if self.game_mode == "tiger":
            odds_map = {
                'Small Tiger': ('22:1', "#ff8ef6"),
                'Tiger Tie':   ('35:1', '#44ff44'),
                'Big Tiger':   ('50:1', '#44ffff'),
                'Tiger':       ('12/20:1', '#ffaa44'),
                'Tiger Pair':  ('4-100:1', '#ff44ff'),
                'Player':      ('1:1', '#4444ff'),
                'Tie':         ('8:1', '#44ff44'),
                'Banker':      ('1:1*', '#ff4444')
            }
        elif self.game_mode == "ez":
            odds_map = {
                'Monkey 6':    ('12:1', '#ff5f5f'),
                'Monkey Tie':  ('150:1', '#88ccff'),
                'Big Monkey':  ('5000:1', '#e4ff4b'),
                'Panda 8':     ('25:1', '#ffffff'),
                'Divine 9':    ('10:1/75:1', '#86ff94'),
                'Dragon 7':    ('40:1', '#ff8c00'),
                'Player':      ('1:1', '#4444ff'),
                'Tie':         ('8:1', '#44ff44'),
                'Banker':      ('1:1*', '#ff4444')
            }
        elif self.game_mode == "classic":
            odds_map = {
                'Dragon P': ('1-30:1', "#a08fff"),
                'Quik': ('1-50:1', "#ffab3e"),
                'Dragon B': ('1-30:1', "#ff7158"),
                'Pair Player': ('11:1', '#ff44ff'),
                'Any Pair':   ('5:1', '#44ffff'),
                'Pair Banker': ('11:1', '#ff44ff'),
                'Player':      ('1:1', '#4444ff'),
                'Tie':         ('8:1', '#44ff44'),
                'Banker':      ('0.95:1', '#ff4444')
            }
        elif self.game_mode == "2to1":
            odds_map = {
                'Dragon P': ('1-30:1', "#a08fff"),
                'Quik': ('1-50:1', "#ffab3e"),
                'Dragon B': ('1-30:1', "#ff7158"),
                'Pair Player': ('11:1', '#ff44ff'),
                'Any Pair':   ('5:1', '#44ffff'),
                'Pair Banker': ('11:1', '#ff44ff'),
                'Player':      ('1:1*', '#4444ff'),
                'Tie':         ('8:1', '#44ff44'),
                'Banker':      ('1:1*', '#ff4444')
            }
        elif self.game_mode == "fabulous4":
            odds_map = {
                'P Fab Pair': ('1-7:1', '#ff8ef6'),
                'B Fab Pair': ('1-7:1', '#44ff44'),
                'P Fabulous 4': ('50:1', '#44ffff'),
                'B Fabulous 4': ('25:1', '#ffaa44'),
                'Player': ('1:1*', '#4444ff'),
                'Tie': ('8:1', '#44ff44'),
                'Banker': ('1:1*', '#ff4444')
            }

        row1_frame = tk.Frame(self.betting_view, bg='#D0E7FF')
        row1_frame.pack(fill=tk.X, pady=3)

        # 根据模式选择要显示的按钮
        if self.game_mode == "tiger":
            buttons_to_show_1 = ['Small Tiger','Tiger Tie','Big Tiger']
        elif self.game_mode == "ez":
            buttons_to_show_1 = ['Monkey 6','Monkey Tie','Big Monkey']
        elif self.game_mode == "classic" or self.game_mode == "2to1":
            buttons_to_show_1 = ['Dragon P', 'Quik', 'Dragon B']
        elif self.game_mode == "fabulous4":
            buttons_to_show_1 = ['P Fab Pair', 'B Fab Pair']

        for bt in buttons_to_show_1:
            odds, color = odds_map[bt]
            btn = tk.Button(
                row1_frame,
                text=f"{odds}\n{bt}\n~~",
                bg=color,
                font=('Arial', 9, 'bold'),
                height=3,
                wraplength=80,
                command=lambda t=bt: self.place_bet(t)
            )
            btn.bet_type = bt
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
            self.bet_buttons.append(btn)

        row2_frame = tk.Frame(self.betting_view, bg='#D0E7FF')
        row2_frame.pack(fill=tk.X, pady=3)

        if self.game_mode == "tiger":
            buttons_to_show_2 = ['Tiger','Tiger Pair']
        elif self.game_mode == "ez":
            buttons_to_show_2 = ['Panda 8','Divine 9','Dragon 7']
        elif self.game_mode == "classic" or self.game_mode == "2to1":
            buttons_to_show_2 = ['Pair Player', 'Any Pair', 'Pair Banker']
        elif self.game_mode == "fabulous4":
            buttons_to_show_2 = ['P Fabulous 4', 'B Fabulous 4']

        for bt in buttons_to_show_2:
            odds, color = odds_map[bt]
            btn = tk.Button(
                row2_frame,
                text=f"{odds}\n{bt}\n~~",
                bg=color,
                font=('Arial', 9, 'bold'),
                height=3,
                wraplength=100,
                command=lambda t=bt: self.place_bet(t)
            )
            btn.bet_type = bt
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
            self.bet_buttons.append(btn)

        row3_frame = tk.Frame(self.betting_view, bg='#D0E7FF')
        row3_frame.pack(fill=tk.X, pady=3)
        for bt in ['Player','Tie','Banker']:
            odds, color = odds_map[bt]
            text_color = 'white' if bt in ['Player','Banker'] else 'black'
            disabled_color = 'white' if bt in ['Player','Banker'] else 'grey'
            btn = tk.Button(
                row3_frame,
                text=f"{odds}\n{bt}\n~~",
                bg=color,
                font=('Arial', 9, 'bold'),
                height=3,
                fg=text_color,
                disabledforeground=disabled_color,
                highlightthickness=0,
                highlightbackground='black',
                wraplength=60,
                command=lambda t=bt: self.place_bet(t)
            )
            btn.bet_type = bt
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
            self.bet_buttons.append(btn)

        # 说明 - 根据模式显示不同的说明
        if self.game_mode == "tiger":
            explanation = "*BANKER WIN ON 6 PAYS 50%"
        elif self.game_mode == "ez":
            explanation = "*BANKER WIN WITH 3-CARD 7 PUSH"
        elif self.game_mode == "classic":
            explanation = "BANKER PAYS 5% COMMISSION EVERY WIN"
        elif self.game_mode == "2to1":
            explanation = "*WIN WITH 3-CARD 8/9 PAYS 200%| TIE LOSE"
        elif self.game_mode == "fabulous4":
            explanation = "*WIN ON 1 PAYS 200% \nPLAYER(BANKER) WIN ON 4 PAYS 50%(PUSH)"
            
        tk.Label(
            self.betting_view,
            text=explanation,
            font=('Arial', 10),
            bg='#D0E7FF'
        ).pack(pady=2)

        # DEAL/RESET 按钮行
        btn_frame = tk.Frame(self.betting_view, bg='#D0E7FF')
        btn_frame.pack(fill=tk.X, pady=15)
        self.reset_button = tk.Button(
            btn_frame, text="RESET", command=self.reset_bets,
            bg='#ff4444', fg='white',
            font=('Arial', 14, 'bold')
        )
        self.reset_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)
        self.deal_button = tk.Button(
            btn_frame, text="DEAL (Enter)", command=self.start_game,
            bg='gold', fg='black',
            font=('Arial', 14, 'bold')
        )
        self.deal_button.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # 分隔线 + 当前/上次下注显示
        separator = ttk.Separator(self.betting_view, orient=tk.HORIZONTAL)
        separator.pack(fill=tk.X, pady=(5, 0), padx=5)

        current_bet_frame = tk.Frame(self.betting_view, bg='#D0E7FF')
        current_bet_frame.pack(pady=(0, 5))
        tk.Label(
            current_bet_frame, text="Current Bet:", width=12,
            font=('Arial', 14), bg='#D0E7FF'
        ).pack(side=tk.LEFT)
        self.current_bet_label = tk.Label(
            current_bet_frame, text="$0", width=10,
            font=('Arial', 14), bg='#D0E7FF'
        )
        self.current_bet_label.pack(side=tk.RIGHT)

        last_win_frame = tk.Frame(self.betting_view, bg='#D0E7FF')
        last_win_frame.pack(pady=5)
        tk.Label(
            last_win_frame, text="Last Win:", width=12,
            font=('Arial', 14), bg='#D0E7FF'
        ).pack(side=tk.LEFT)
        self.last_win_label = tk.Label(
            last_win_frame, text="$0", width=10,
            font=('Arial', 14), bg='#D0E7FF'
        )
        self.last_win_label.pack(side=tk.RIGHT)
        self._set_default_chip()

    def _set_default_chip(self):
        """设置默认选中的筹码（1K）"""
        # 清除之前选中的发光效果
        if self.selected_chip:
            self.selected_canvas.itemconfig(self.selected_id, outline='#D0E7FF')
        
        # 设置新选中的筹码（1K）
        for chip in self.chip_buttons:
            if chip['text'] == '1K':
                self.selected_canvas = chip['canvas']
                self.selected_id = chip['chip_id']
                chip['canvas'].itemconfig(chip['chip_id'], outline='gold')
                self.selected_chip = chip
                self.selected_bet_amount = 1000
                self.current_chip_label.config(text="Chips amount: $1,000")
                break

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        self.mute_button.config(
            text="🔊 Unmute" if self.is_muted else "🔇 Mute",
            bg='#66ff66' if self.is_muted else '#ff6666'
        )
        mixer.music.stop()

    def _setup_bindings(self):
        self.bind('<Return>', lambda e: self.start_game())

    def place_bet(self, bet_type):
        amount = self.selected_bet_amount
        if amount > self.balance:
            messagebox.showerror("Error", "Insufficient balance")
            return
        
        # 触发发光动画
        self._animate_chip_glow()
        
        self.balance -= amount
        self.current_bet += amount  # 累加当前回合下注总额
        self.current_bets[bet_type] = self.current_bets.get(bet_type, 0) + amount

        for btn in self.bet_buttons:
            if hasattr(btn, 'bet_type') and btn.bet_type == bet_type:
                current_amount = self.current_bets.get(bet_type, 0)
                original_text = btn.cget("text").split('\n')
                new_text = f"{original_text[0]}\n{original_text[1]}\n${current_amount}"
                btn.config(text=new_text)

        self.update_balance()
        self.current_bet_label.config(text=f"${self.current_bet:,}")

    def start_game(self):
        self.table_canvas.itemconfig(self.result_bg_id, fill='', outline='')
        self.table_canvas.itemconfig(self.result_text_id, text='')
        
        if len(self.game.deck) - self.game.cut_position < 60:
            self._initialize_game(True)

        # 禁用按钮
        for btn in self.bet_buttons:
            btn.config(state=tk.DISABLED)
        self.deal_button.config(state=tk.DISABLED)
        self.reset_button.config(state=tk.DISABLED)
        self.unbind('<Return>')
        self.mode_combo.config(state='disabled')

        self.play_sound("Stop_betting.mp3")        
        self.game.play_game()
        self.animate_dealing()

    def animate_dealing(self):
        self.table_canvas.delete('all')
        self.point_labels.clear()
        self._draw_table_labels()

        # ← NEW: create two "total" displays
        # positions chosen below the “PLAYER” and “BANKER” areas:
        self.player_total_id = self.table_canvas.create_text(
            250, 400, text="", font=('Arial', 50, 'bold'), fill='white')
        self.banker_total_id = self.table_canvas.create_text(
            750, 400, text="", font=('Arial', 50, 'bold'), fill='white')

        # track which cards we’ve flipped face‐up
        self.revealed_cards = {'player': [], 'banker': []}

        self._deal_initial_cards()
        self.after(1000, self._reveal_initial_phase1)

        self.result_text_id = self.table_canvas.create_text(
            500, 600, 
            text="", 
            font=('Arial', 34, 'bold'),
            fill='white',
            tags=('result_text')
        )
        self.result_bg_id = self.table_canvas.create_rectangle(
            0,0,0,0,  # 初始不可见
            fill='',
            outline='',
            tags=('result_bg')
        )

    def _deal_initial_cards(self):
        self.initial_card_ids = []
        # Player cards
        for i, pos in enumerate(self._get_card_positions("player")[:2]):
            self._animate_card_entrance("player", i, pos)
        # Banker cards
        for i, pos in enumerate(self._get_card_positions("banker")[:2]):
            self._animate_card_entrance("banker", i, pos)

    def _animate_card_entrance(self, hand_type, index, target_pos):
        start_x, start_y = (100, 50) if hand_type == "player" else (1100, 50)
        card_id = self.table_canvas.create_image(start_x, start_y, image=self.back_image)
        
        def move_step(step=0):
            if step <= 30:
                x = start_x + (target_pos[0]-start_x)*(step/30)
                y = start_y + (target_pos[1]-start_y)*(step/30)
                self.table_canvas.coords(card_id, x, y)
                self.after(10, move_step, step+1)
        
        move_step()
        self.initial_card_ids.append((hand_type, card_id))

    def _reveal_initial_phase1(self):
        card_info = self.initial_card_ids[0]
        real_card = self.game.player_hand[0]
        self._flip_card(card_info, real_card, 0)
        self.after(500, self._reveal_initial_phase3)

    def _reveal_initial_phase2(self):
        card_info = self.initial_card_ids[1]
        real_card = self.game.player_hand[1]
        self._flip_card(card_info, real_card, 1)
        self.after(1000, self._reveal_initial_phase4)

    def _reveal_initial_phase3(self):
        card_info = self.initial_card_ids[2]
        real_card = self.game.banker_hand[0]
        self._flip_card(card_info, real_card, 2)
        self.after(500, self._reveal_initial_phase2)

    def _reveal_initial_phase4(self):
        card_info = self.initial_card_ids[3]
        real_card = self.game.banker_hand[1]
        self._flip_card(card_info, real_card, 3)
        self.after(1000, self._process_extra_cards)

    def _process_extra_cards(self):
        if len(self.game.player_hand) > 2:
            self._deal_extra_card("player", 2)
            # 播放补牌后总分音效
            total = sum(self.game.card_value(c) for c in self.game.player_hand) % 10
            self.play_sound(f"Player_{total}.mp3")
            self.after(1500, self._process_banker_extra)
        else:
            self._process_banker_extra()

    def _process_banker_extra(self):
        if len(self.game.banker_hand) > 2:
            self._deal_extra_card("banker", 2)
            total = sum(self.game.card_value(c) for c in self.game.banker_hand) % 10
            self.play_sound(f"Banker_{total}.mp3")
            self.after(1500, self.resolve_bets)
        else:
            self.resolve_bets()

    def _flip_card(self, card_info, real_card, seq):
        hand_type, card_id = card_info
        steps = 10
        for i in range(steps):
            angle = 180 * (i/steps)
            img = self._create_flip_image(real_card, angle)
            self.table_canvas.itemconfig(card_id, image=img)
            self.update()
            self.after(30)
        self.table_canvas.itemconfig(card_id, image=self.card_images[real_card])
        self.revealed_cards[hand_type].append(real_card)

        # compute the mod-10 total of all face-up cards
        total = sum(self.game.card_value(c) for c in self.revealed_cards[hand_type]) % 10

        # update the appropriate “total” text item
        if hand_type == 'player':
            self.table_canvas.itemconfig(self.player_total_id, text=str(total))
        else:
            self.table_canvas.itemconfig(self.banker_total_id, text=str(total))

        # 在翻牌后添加音效逻辑
        if seq in [0, 1, 2, 3]:  # 只处理前4张初始牌
            hand_type = 'player' if hand_type == 'player' else 'banker'
            current_cards = self.revealed_cards[hand_type]
            if len(current_cards) == 2:
                score = sum(self.game.card_value(c) for c in current_cards) % 10
                prefix = 'Player' if hand_type == 'player' else 'Banker'
                self.play_sound(f"{prefix}_{score}.mp3")

    def _create_flip_image(self, card, angle):
        # 获取当前脚本所在目录的绝对路径
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        if angle < 90:
            # 修改为使用绝对路径
            bg_path = os.path.join(base_dir, 'Card', 'Background.png')
            img = Image.open(bg_path)
        else:
            # 修改为使用绝对路径
            card_path = os.path.join(base_dir, 'Card', f"{card[0]}{card[1]}.png")
            img = Image.open(card_path)
        
        img = img.resize((100, 140))
        return ImageTk.PhotoImage(img.rotate(angle if angle < 90 else 180-angle))

    def _deal_extra_card(self, hand_type, index):
        hand = self.game.player_hand if hand_type == "player" else self.game.banker_hand
        card = hand[index]
        target_pos = self._get_card_positions(hand_type)[index]
        card_id = self.table_canvas.create_image(100, 300, image=self.back_image)
        self.initial_card_ids.append((hand_type, card_id))
        for step in range(30):
            x = 100 + (target_pos[0]-100)*(step/30)
            y = 300 + (target_pos[1]-300)*(step/30)
            self.table_canvas.coords(card_id, x, y)
            self.update()
            self.after(10)
        self._flip_card((hand_type, card_id), card, index+4)

    def resolve_bets(self):
        is_natural = False
        is_stiger = False
        is_btiger = False

        p_bet = self.current_bets.get('Player', 0)
        b_bet = self.current_bets.get('Banker', 0)
        t_bet = self.current_bets.get('Tie', 0)
        payouts = 0

        if self.game.winner == 'Player':
            if self.game_mode == "2to1" and len(self.game.player_hand) == 3 and self.game.player_score in (8, 9):
                payouts += p_bet * 3
            elif self.game_mode == "fabulous4":
                if self.game.player_score == 1:
                    payouts += p_bet * 3
                elif self.game.player_score == 4:
                    payouts += p_bet * 1.5
                else:
                    payouts += p_bet * 2
            else:
                payouts += p_bet * 2
        elif self.game.winner == 'Banker':
            if self.game_mode == "tiger":
                # 老虎模式：庄家6点赔付50%
                if self.game.banker_score == 6:
                    payouts += b_bet * 1.5
                else:
                    payouts += b_bet * 2
            elif self.game_mode == "ez":
                # EZ模式：庄家三张牌7点视为和局
                if len(self.game.banker_hand) == 3 and self.game.banker_score == 7:
                    payouts += b_bet  # 退还本金
                else:
                    payouts += b_bet * 2
            elif self.game_mode == "classic":
                payouts += b_bet * 1.95
            elif self.game_mode == "2to1":
                if len(self.game.banker_hand) == 3 and self.game.banker_score in (8, 9):
                    payouts += b_bet * 3
                else:
                    payouts += b_bet * 2
            elif self.game_mode == "fabulous4":
                if self.game.banker_score == 1:
                    payouts += b_bet * 3
                elif self.game.banker_score == 4:
                    payouts += b_bet
                else:
                    payouts += b_bet * 2
        elif self.game.winner == 'Tie':
            if self.game_mode == "2to1":
                payouts += t_bet * 9
            else:
                payouts += t_bet * 9 + p_bet + b_bet  # Tie赔付+退还本金

        side_results = self._check_side_bets()

        if self.game_mode == "tiger":
            tiger_bet = self.current_bets.get('Tiger Pair', 0)
            if tiger_bet and 'Tiger Pair' in side_results:
                odds = side_results['Tiger Pair']
                # “Win X:1” means profit = bet * X, total returned = (X + 1) * bet
                payouts += tiger_bet * (odds + 1)

            # Small Tiger
            st_bet = self.current_bets.get('Small Tiger', 0)
            if st_bet and 'Small Tiger' in side_results:
                odds = side_results['Small Tiger']
                payouts += st_bet * (odds + 1)

            # Big Tiger
            bt_bet = self.current_bets.get('Big Tiger', 0)
            if bt_bet and 'Big Tiger' in side_results:
                odds = side_results['Big Tiger']
                payouts += bt_bet * (odds + 1)

            # Tiger赔付
            tigers_bet = self.current_bets.get('Tiger', 0)
            if 'Tiger' in side_results:
                odds = side_results['Tiger']
                payouts += tigers_bet * (odds + 1)

            tiger_tie_bet = self.current_bets.get('Tiger Tie', 0)
            if 'Tiger Tie' in side_results:
                payouts += tiger_tie_bet * 36

        if self.game_mode == "ez":
            # Dragon 7
            Dragon_bet = self.current_bets.get('Dragon 7', 0)
            if Dragon_bet and 'Dragon 7' in side_results:
                payouts += Dragon_bet * 41

            # Divine 9
            divine_bet = self.current_bets.get('Divine 9', 0)
            if divine_bet and 'Divine 9' in side_results:
                odds = side_results['Divine 9']
                payouts += divine_bet * (odds + 1)

            # Panda 8
            panda_bet = self.current_bets.get('Panda 8', 0)
            if 'Panda 8' in side_results:
                payouts += panda_bet * 26

            # Monkey 6
            monkey_bet = self.current_bets.get('Monkey 6', 0)
            if 'Monkey 6' in side_results:
                payouts += monkey_bet * 13
                
            # Monkey Tie
            Monkey_Tie_bet = self.current_bets.get('Monkey Tie', 0)
            if 'Monkey Tie' in side_results:
                payouts += Monkey_Tie_bet * 151
                
            # Big Monkey
            BMonkey_bet = self.current_bets.get('Big Monkey', 0)
            if 'Big Monkey' in side_results:
                payouts += BMonkey_bet * 5001

        if self.game_mode == "classic" or self.game_mode == "2to1":
            #Player Pair
            ppair = self.current_bets.get('Pair Player', 0)
            if 'Pair Player' in side_results:
                payouts +=  ppair * 12

            #Banker Pair
            bpair = self.current_bets.get('Pair Banker', 0)
            if 'Pair Banker' in side_results:
                payouts +=  bpair * 12

            #Any Pair
            apair = self.current_bets.get('Any Pair', 0)
            if 'Any Pair' in side_results:
                payouts +=  apair * 6

            #Player Dragon
            pdragon = self.current_bets.get('Dragon P', 0)
            if 'Dragon P' in side_results:
                odds = side_results['Dragon P']
                payouts += pdragon * odds

            #Quik
            quik = self.current_bets.get('Quik', 0)
            if 'Quik' in side_results:
                odds = side_results['Quik']
                payouts += quik * odds

            #Banker Dragon
            bdragon = self.current_bets.get('Dragon B', 0)
            if 'Dragon B' in side_results:
                odds = side_results['Dragon B']
                payouts += bdragon * odds

        if self.game_mode == "fabulous4":
            # Player Fab Pair
            fab_pair_p = self.current_bets.get('P Fab Pair', 0)
            if 'P Fab Pair' in side_results:
                odds = side_results['P Fab Pair']
                payouts += fab_pair_p * (odds + 1)
                
            # Banker Fab Pair
            fab_pair_b = self.current_bets.get('B Fab Pair', 0)
            if 'B Fab Pair' in side_results:
                odds = side_results['B Fab Pair']
                payouts += fab_pair_b * (odds + 1)
                
            # P Fabulous 4
            fab4_p = self.current_bets.get('P Fabulous 4', 0)
            if 'P Fabulous 4' in side_results:
                payouts += fab4_p * 51
                
            # B Fabulous 4
            fab4_b = self.current_bets.get('B Fabulous 4', 0)
            if 'B Fabulous 4' in side_results:
                payouts += fab4_b * 26

        self.balance += payouts
        self.current_bets.clear()
        self.update_balance()
        self.after(1000, self._animate_result_cards)
        self.update_balance()

        for btn in self.bet_buttons:
            if hasattr(btn, 'bet_type'):
                original_text = btn.cget("text").split('\n')
                new_text = f"{original_text[0]}\n{original_text[1]}\n~~"
                btn.config(text=new_text)

        # 修复1：立即重置当前总下注
        self.current_bet = 0  # 新增这行
        self.current_bet_label.config(text="$0")

        # 修复2：正确更新last_win
        self.last_win = payouts  # 计算净盈利
        self.last_win_label.config(text=f"${max(self.last_win, 0):,}")  # 新增这行

        if self.game.winner == 'Tie':
            self.last_win = payouts  # 显示总赔付金额（包含本金）
        else:
            self.last_win = max(payouts, 0) 

        # 判断显示条件（保持原逻辑）
        winner = self.game.winner
        p_score = self.game.player_score
        b_score = self.game.banker_score
        b_hand_len = len(self.game.banker_hand)

        def enable_buttons():
            for btn in self.bet_buttons:
                btn.config(state=tk.NORMAL)
            self.deal_button.config(state=tk.NORMAL)
            self.reset_button.config(state=tk.NORMAL)
            self.bind('<Return>', lambda e: self.start_game())
            self.mode_combo.config(state='readonly')
                
        self.after(1000, enable_buttons)
        time.sleep(1)
        
        text = ""
        text_color = "black"
        bg_color = "#35654d"
        
        # 条件判断逻辑
        if winner == 'Player':
            if self.game_mode == "fabulous4":
                if p_score == 1:
                    text = "PLAYER WIN ON 1 (PAY 2:1)"
                elif p_score == 4:
                    text = "PLAYER WIN ON 4 (PAY 0.5:1)"
                else:
                    text = "PLAYER WIN"
            else:
                text = "PLAYER WIN"
            bg_color = '#4444ff'
            text_color = 'white'
        elif winner == 'Banker':
            if b_score == 6 and self.game_mode == "tiger":
                text = "SMALL TIGER" if b_hand_len == 2 else "BIG TIGER"
            elif b_score == 7 and b_hand_len == 3 and self.game_mode == "ez":
                text = "BANKER WIN AND PUSH ON 7"
            elif self.game_mode == "fabulous4":
                if b_score == 1:
                    text = "BANKER WIN ON 1 (PAY 2:1)"
                elif b_score == 4:
                    text = "BANKER WIN AND PUSH ON 4"
                else:
                    text = "BANKER WIN"
            else:
                text = "BANKER WIN"
            bg_color = '#ff4444'
            text_color = 'black'
        elif winner == 'Tie':
            if b_score == 6 and self.game_mode == "tiger":
                text = "TIGER TIE"
            else:
                text = "TIE WIN"
            bg_color = '#44ff44'
            text_color = 'black'

        # 更新文字
        self.table_canvas.itemconfig(
            self.result_text_id,
            text=text,
            fill=text_color
        )
        
        # 强制Canvas更新布局
        self.table_canvas.update_idletasks()

        # 结算音效
        if self.game.winner == 'Player':
            self.play_sound("Player_win.mp3")
        elif self.game.winner == 'Banker':
            if self.game_mode == "tiger":
                if self.game.banker_score == 6:
                    if len(self.game.banker_hand) == 2:
                        self.play_sound("Banker_s6_win.mp3")
                    else:
                        self.play_sound("Banker_b6_win.mp3")
                else:
                    self.play_sound("Banker_win.mp3" )
            elif self.game_mode == "ez":
                if self.game.banker_score == 7 and len(self.game.banker_hand) == 3:
                    self.play_sound("Banker_push7.mp3")
                else:
                    self.play_sound("Banker_win.mp3" )
            elif self.game_mode == "classic" or self.game_mode == "2to1" or self.game_mode == "fabulous4":
                self.play_sound("Banker_win.mp3" )
        elif self.game.winner == 'Tie':
            if self.game.player_score == 6 and self.game_mode == "tiger":
                self.play_sound("Tie_6_win.mp3")
            else:
                self.play_sound("Tie_win.mp3")

        is_natural = False
        is_stiger = False
        is_btiger = False
        if self.game.winner != 'Tie':
            # 检查是否为例牌(2张牌8或9点)
            if self.game.winner == 'Player':
                is_natural = len(self.game.player_hand) == 2 and self.game.player_score >= 8
            else:  # Banker
                is_natural = len(self.game.banker_hand) == 2 and self.game.banker_score >= 8
                is_stiger = len(self.game.banker_hand) == 2 and self.game.banker_score == 6
                is_btiger = len(self.game.banker_hand) == 3 and self.game.banker_score == 6

        if self.game.winner == 'Tie' and self.game.banker_score == 6:
            is_stiger = True

        # 添加珠路图结果
        player_hand_len = len(self.game.player_hand)
        banker_hand_len = len(self.game.banker_hand)
        player_score = self.game.player_score
        banker_score = self.game.banker_score

        self.add_marker_result(
            self.game.winner, is_natural, is_stiger, is_btiger,
            player_hand_len, banker_hand_len,
            player_score, banker_score
        )

        # 保存结果到数据文件
        result_char = ''
        if self.game.winner == 'Player':
            result_char = 'P'
        elif self.game.winner == 'Banker':
            result_char = 'B'
        elif self.game.winner == 'Tie':
            result_char = 'T'
        
        if result_char:
            self.save_game_result(result_char)
        
        # 获取文字边界并更新背景框
        text_bbox = self.table_canvas.bbox(self.result_text_id)
        if text_bbox:
            # 扩展边界增加内边距
            padding = 10
            expanded_bbox = (
                text_bbox[0]-padding, 
                text_bbox[1]-padding,
                text_bbox[2]+padding, 
                text_bbox[3]+padding
            )
            
            # 更新背景框
            self.table_canvas.coords(self.result_bg_id, expanded_bbox)
            self.table_canvas.itemconfig(
                self.result_bg_id,
                fill=bg_color,
                outline=bg_color
            )
            
            # 确保层级顺序
            self.table_canvas.tag_raise(self.result_text_id)  # 文字置顶
            self.table_canvas.tag_lower(self.result_bg_id)   # 背景置底

        # 添加到大路结果
        tie_count = 1 if self.game.winner == 'Tie' else 0
        self.bigroad_results.append({
            'winner': self.game.winner,
            'tie_count': tie_count
        })
        self._update_bigroad()
        self.update_pie_chart()
        
        # 更新連勝記錄
        winner = self.game.winner
        if winner == self.current_streak_type:
            self.current_streak += 1
        else:
            self.current_streak = 1
            self.current_streak_type = winner
        
        # 更新最長連勝記錄
        if self.current_streak > self.longest_streaks.get(winner, 0):
            self.longest_streaks[winner] = self.current_streak
        self.update_streak_labels()

    def _update_bigroad(self):
        """
        更新“大路” (3 行测试版)：
        • 先向下；如果向下越界或目标被占，则保持行不变、向右一格。
        • 新跑道 (胜方切换时)：起始列 = last_run_start_col + 1，在 row=0 放；若(0,col)被占则向右依次找。
        • 连胜时：只有当当前 winner == last_winner（都为非 Tie）才绘制连线。
        • Tie(和局)不占新格，在“最后一次非 Tie”所在格子累加：若整个开局都 Tie，则把(0,0)当隐形锚点，先画斜线再累加数字。
        """
        # 如果画布不存在，直接 return
        if not hasattr(self, 'bigroad_canvas'):
            return

        # 单元格与间距设置
        cell    = 25      # 每个格子的宽/高
        pad     = 2       # 格子之间的间距
        label_w = 30      # 左侧留给行号的宽度
        label_h = 20      # 顶部留给列号的高度

        # 1. 清空上一轮绘制的“data”层：删除 tags=('data',) 的所有元素
        self.bigroad_canvas.delete('data')

        # 2. 重置占用矩阵 (重新标记哪些格子已被占)
        self._bigroad_occupancy = [
            [False] * self._max_cols for _ in range(self._max_rows)
        ]

        # 3. 用于追踪“最后一次非 Tie” 的信息
        last_winner = None         # 上一次胜方 ('Player' / 'Banker')
        last_run_start_col = -1    # 上一次跑道的起始列 (初值 -1)
        prev_row, prev_col = None, None   # 上一次非 Tie 所占用的 (row, col)
        prev_cx, prev_cy = None, None     # 上一次非 Tie 圆点在 Canvas 上的中心

        # 4. Tie 累计字典：key=(row, col), value=已经累积的 Tie 次数
        tie_tracker = {}

        # 5. 遍历所有结果，逐局绘制
        for res in self.bigroad_results:
            winner = res.get('winner')  # 'Player', 'Banker' 或 'Tie'

            # —— A. 处理 Tie (和局) —— 
            if winner == 'Tie':
                # A.1 如果此前“从没出现过非 Tie” (prev_row / prev_col 皆为 None)，
                #     就把 (0,0) 当作“隐形锚点”并绘制第一条斜线
                if prev_row is None and prev_col is None:
                    r0, c0 = 0, 0
                    # 标记(0,0)被占
                    self._bigroad_occupancy[r0][c0] = True

                    # 计算 (0,0) 在 Canvas 上的中心坐标
                    x0 = label_w + pad + c0 * (cell + pad)
                    y0 = label_h + pad + r0 * (cell + pad)
                    cx0 = x0 + cell / 2
                    cy0 = y0 + cell / 2

                    # 更新“最后一次非 Tie” 指向 (0,0)，用于后续连线与 Tie 累加
                    prev_row, prev_col = r0, c0
                    prev_cx, prev_cy = cx0, cy0

                    # 记录这是第 1 次 Tie 并画绿色斜线
                    tie_tracker[(r0, c0)] = 1
                    self.bigroad_canvas.create_line(
                        cx0 - 6, cy0 + 6, cx0 + 6, cy0 - 6,
                        width=2, fill='#00AA00', tags=('data',)
                    )
                    continue  # 跳过本手圆点放置

                # A.2 已经出现过非 Tie，则把本局 Tie 累加到上一次非 Tie 所在格
                r0, c0 = prev_row, prev_col
                tie_tracker[(r0, c0)] = tie_tracker.get((r0, c0), 0) + 1
                cnt = tie_tracker[(r0, c0)]

                # 计算该格在 Canvas 上中心
                x0 = label_w + pad + c0 * (cell + pad)
                y0 = label_h + pad + r0 * (cell + pad)
                cx0 = x0 + cell / 2
                cy0 = y0 + cell / 2

                # 绘制绿色斜线
                self.bigroad_canvas.create_line(
                    cx0 - 10, cy0 + 10,  # 起点坐标
                    cx0 + 10, cy0 - 10,  # 终点坐标
                    width=4,             # 宽度从2增加到4
                    fill='#00AA00', 
                    tags=('data',)
                )
                # 如果 Tie 次数 > 1，再在中央画数字
                if cnt > 1:
                    self.bigroad_canvas.create_text(
                        cx0, cy0, text=str(cnt),
                        font=('Arial', 8, 'bold'), fill='#00AA00',
                        tags=('data',)
                    )
                continue  # 本局仅是叠加 Tie，不放新圆点

            # —— B. 处理非 Tie (庄家 or 闲家) —— 

            # B.1 判断是否“新的跑道”（胜方切换，或之前尚未出现任何非 Tie）
            if last_winner is None or winner != last_winner:
                # 新跑道：跑道起始列 = 上一次跑道起始列 + 1
                run_start_col = last_run_start_col + 1
                last_run_start_col = run_start_col

                # 从 (row=0, col=run_start_col) 开始尝试放置；如果(0, run_start_col)已被占，就向右查找第一个未占列
                col0 = run_start_col
                while col0 < self._max_cols and self._bigroad_occupancy[0][col0]:
                    col0 += 1
                if col0 >= self._max_cols:
                    # 若找不到可用列，就跳出，不再绘制后续
                    break
                row0 = 0

                row, col = row0, col0

            else:
                # 同一跑道内连胜：优先“向下” -> (row = prev_row + 1, col = prev_col)
                # 如果“向下”越界或被占，就改为“行不变，列 + 1”
                nr = prev_row + 1
                nc = prev_col
                if nr < self._max_rows and not self._bigroad_occupancy[nr][nc]:
                    row, col = nr, nc
                else:
                    row = prev_row
                    col = prev_col + 1

            # B.2 如果计算出的 col >= 最大列数，就直接退出循环
            if col >= self._max_cols:
                break

            # 标记此 (row, col) 已被占
            self._bigroad_occupancy[row][col] = True

            # 计算此格在 Canvas 上的中心 (cx, cy)
            x0 = label_w + pad + col * (cell + pad)
            y0 = label_h + pad + row * (cell + pad)
            cx = x0 + cell / 2
            cy = y0 + cell / 2

            # B.3 如果是连胜 (winner == last_winner)，并且 prev_cx/prev_cy 已初始化，就画连线
            if prev_cx is not None and prev_cy is not None and winner == last_winner:
                line_color = "#FF3C00" if winner == 'Banker' else "#0091FF"
                self.bigroad_canvas.create_line(
                    prev_cx, prev_cy, cx, cy,
                    width=2, fill=line_color, tags=('data',)
                )

            # B.4 绘制圆点：庄家用红 (#FF3C00)，闲家用蓝 (#0091FF)
            dot_color = "#FF3C00" if winner == 'Banker' else "#0091FF"
            self.bigroad_canvas.create_oval(
                cx - 8, cy - 8, cx + 8, cy + 8,
                fill=dot_color, outline='', tags=('data',)
            )

            # B.5 如果该 (row, col) 之前已有 Tie 次数，就在圆点上叠加斜线与数字
            if (row, col) in tie_tracker:
                tcnt = tie_tracker[(row, col)]
                # 修改点2：增加斜杠宽度和长度
                self.bigroad_canvas.create_line(
                    cx - 10, cy + 10,  # 起点坐标
                    cx + 10, cy - 10,  # 终点坐标
                    width=2,           # 宽度从2增加到4
                    fill='#00AA00', 
                    tags=('data',)
                )
                if tcnt > 1:
                    self.bigroad_canvas.create_text(
                        cx, cy, text=str(tcnt),
                        font=('Arial', 12, 'bold'), fill="#FFFFFF",
                        tags=('data',)
                    )

            # B.6 更新“最后一次非 Tie”的各项信息，以便下一局画连线或累计 Tie
            prev_row, prev_col = row, col
            prev_cx, prev_cy = cx, cy
            last_winner = winner

    def _animate_result_cards(self):
        offset = 25
        # 显式获取需要移动的卡片ID
        self.cards_to_move = {
            'player': [cid for htype, cid in self.initial_card_ids if htype == 'player'],
            'banker': [cid for htype, cid in self.initial_card_ids if htype == 'banker']
        }
        
        if self.game.winner == 'Player':
            self._move_cards('player', 0, offset)
        elif self.game.winner == 'Banker':
            self._move_cards('banker', 0, offset)
        elif self.game.winner == 'Tie':
            self._move_cards('player', offset, 0)
            self._move_cards('banker', -offset, 0)

    # 在类中添加这个方法
    def _move_cards(self, hand_type, dx, dy):
        """移动卡片动画效果"""
        # 获取所有卡片的最终位置（包含补牌）
        final_positions = self._get_card_positions(hand_type)
        
        # 确保有卡片需要移动
        if hand_type not in self.cards_to_move:
            return
            
        card_ids = self.cards_to_move[hand_type]
        
        # 确保卡片数量和位置数量匹配
        if len(card_ids) != len(final_positions):
            # 使用安全的方式处理
            n = min(len(card_ids), len(final_positions))
            card_ids = card_ids[:n]
            final_positions = final_positions[:n]
        
        # 建立卡片ID与最终位置的映射
        card_positions = {}
        for i, cid in enumerate(card_ids):
            if i < len(final_positions):
                card_positions[cid] = final_positions[i]
        
        # 执行同步动画
        for step in range(10):  # 10步动画
            for cid in card_ids:
                if cid in card_positions:  # 确保有位置信息
                    orig_x, orig_y = card_positions[cid]
                    new_x = orig_x + dx * (step/10)
                    new_y = orig_y + dy * (step/10)
                    self.table_canvas.coords(cid, new_x, new_y)
            self.update()
            self.after(30)

    def _check_side_bets(self):
        results = {}
        p = self.game.player_hand
        b = self.game.banker_hand
        p0, p1 = self.game.player_hand[:2]
        b0, b1 = self.game.banker_hand[:2]
        player_pair = (p0[1] == p1[1])
        banker_pair = (b0[1] == b1[1])

        if self.game_mode == "tiger":
            # 老虎百家乐边注检查
            # Any‐side pair (exactly one side)
            if player_pair ^ banker_pair:
                results['Tiger Pair'] = 4  # win 4:1
            # Both sides pair but different ranks
            elif player_pair and banker_pair and p0[1] != b0[1]:
                results['Tiger Pair'] = 20  # win 20:1
            # Both sides the same pair rank (rare)
            elif player_pair and banker_pair and p0[1] == b0[1]:
                results['Tiger Pair'] = 100  # win 100:1

            # 新的Tiger逻辑
            if self.game.winner == 'Banker' and self.game.banker_score == 6:
                if len(b) == 2:  # 两张牌
                    results['Tiger'] = 12  # 12:1
                else:  # 三张牌
                    results['Tiger'] = 20  # 20:1

            # now Small/Big Tiger
            # “Banker wins on a 6”:
            if self.game.winner == 'Banker' and self.game.banker_score == 6:
                # length 2 ⇒ no third card dealt ⇒ Small Tiger
                if len(b) == 2:
                    results['Small Tiger'] = 22   # pays 22:1
                # length 3 ⇒ Banker drew third card ⇒ Big Tiger
                elif len(b) == 3:
                    results['Big Tiger'] = 50    # pays 50:1

            # “Player and Banker tie on a 6”:
            if self.game.winner == 'Tie' and self.game.player_score == 6 and self.game.banker_score == 6:
                results['Tiger Tie'] = 35

        elif self.game_mode == "ez":
            # EZ百家乐边注检查
            # 1. Monkey 6: 需要6张牌，第5张不是J/Q/K，第6张是J/Q/K
            if len(p) == 3 and len(b) == 3:
                # 检查第5张牌（玩家第三张）
                fifth_card = p[2] if len(p) > 2 else None
                # 检查第6张牌（庄家第三张）
                sixth_card = b[2] if len(b) > 2 else None
                
                # Monkey代表J、Q、K（点数为0）
                is_monkey = lambda card: card[1] in ['J', 'Q', 'K']
                
                if fifth_card and sixth_card:
                    if not is_monkey(fifth_card) and is_monkey(sixth_card):
                        results['Monkey 6'] = 12
                        
                        # 如果同时是和局
                        if self.game.winner == 'Tie':
                            results['Monkey Tie'] = 150
                    
                    # 检查是否所有牌都是Monkey
                    all_monkey = all(is_monkey(card) for card in p + b)
                    if all_monkey:
                        results['Big Monkey'] = 5000
            
            # 2. Panda 8: 玩家三张牌刚好8点并获胜
            if len(p) == 3 and self.game.player_score == 8 and self.game.winner == 'Player':
                results['Panda 8'] = 25
            
            # 3. Divine 9: 任意一方以三张牌9点获胜
            player_divine = len(p) == 3 and self.game.player_score == 9
            banker_divine = len(b) == 3 and self.game.banker_score == 9
            
            if player_divine and banker_divine:
                results['Divine 9'] = 75
            elif player_divine and self.game.winner == 'Player':
                results['Divine 9'] = 10
            elif banker_divine and self.game.winner == 'Banker':
                results['Divine 9'] = 10
            
            # 4. Dragon 7: 庄家以三张牌7点获胜
            if len(b) == 3 and self.game.banker_score == 7 and self.game.winner == 'Banker':
                results['Dragon 7'] = 40

        elif self.game_mode == "classic" or self.game_mode == "2to1":
            p_score = self.game.player_score
            b_score = self.game.banker_score
            # 1. 龙奖金 - Player
            if 'Dragon P' in self.current_bets:
                # 例牌赢（两张牌8或9点）
                if len(p) == 2 and p_score >= 8 and self.game.winner == 'Player':
                    results['Dragon P'] = 2  
                if len(p) == 2 and p_score >= 8 and self.game.winner == 'Tie':
                    results['Dragon P'] = 1
                
                # 非例牌赢（三张牌以上）
                elif self.game.winner == 'Player':
                    point_diff = abs(p_score - b_score)
                    if point_diff >= 9:
                        results['Dragon P'] = 31
                    elif point_diff == 8:
                        results['Dragon P'] = 11
                    elif point_diff == 7:
                        results['Dragon P'] = 7
                    elif point_diff == 6:
                        results['Dragon P'] = 5
                    elif point_diff == 5:
                        results['Dragon P'] = 3
                    elif point_diff == 4:
                        results['Dragon P'] = 2
            
            # 2. Quik
            if 'Quik' in self.current_bets:
                t_score = p_score + b_score
                if t_score == 0:
                    results['Quik'] = 51
                elif t_score == 18:
                    results['Quik'] = 26
                elif t_score in [1, 2, 3, 15, 16, 17]:
                    results['Quik'] = 2
            
            # 3. 龙奖金 - Banker
            if 'Dragon B' in self.current_bets:
                # 例牌赢（两张牌8或9点）
                if len(b) == 2 and b_score >= 8 and self.game.winner == 'Banker':
                    results['Dragon B'] = 2
                elif len(b) == 2 and b_score >= 8 and self.game.winner == 'Tie':
                    results['Dragon B'] = 1
                
                # 非例牌赢（三张牌以上）
                elif self.game.winner == 'Banker':
                    point_diff = abs(b_score - p_score)
                    if point_diff >= 9:
                        results['Dragon B'] = 31
                    elif point_diff == 8:
                        results['Dragon B'] = 11
                    elif point_diff == 7:
                        results['Dragon B'] = 7
                    elif point_diff == 6:
                        results['Dragon B'] = 5
                    elif point_diff == 5:
                        results['Dragon B'] = 3
                    elif point_diff == 4:
                        results['Dragon B'] = 2
        
            # 4. 对子 - Player
            if 'Pair Player' in self.current_bets:
                # 检查前两张牌是否同点数
                if player_pair:
                    results['Pair Player'] = 11  # 11:1
            
            # 5. 对子 - Banker
            if 'Pair Banker' in self.current_bets:
                # 检查前两张牌是否同点数
                if banker_pair:
                    results['Pair Banker'] = 11  # 11:1
            
            # 6. 对子 - Both
            if 'Any Pair' in self.current_bets:
                if player_pair or banker_pair:
                    results['Any Pair'] = 5
                if banker_pair:
                    results['Any Pair'] = 5
                if player_pair:
                    results['Any Pair'] = 5

        elif self.game_mode == "fabulous4":
            # 1. 閒家神奇對子
            if p0 and p1:
                same_rank = p0[1] == p1[1]
                same_suit = p0[0] == p1[0]
                
                if same_rank and same_suit:
                    results['P Fab Pair'] = 7  # 同花對子 7:1
                elif same_rank:
                    results['P Fab Pair'] = 4  # 非同花對子 4:1
                elif same_suit:
                    results['P Fab Pair'] = 1  # 同花非對子 1:1
            
            # 2. 莊家神奇對子
            if b0 and b1:
                same_rank = b0[1] == b1[1]
                same_suit = b0[0] == b1[0]
                
                if same_rank and same_suit:
                    results['B Fab Pair'] = 7  # 同花對子 7:1
                elif same_rank:
                    results['B Fab Pair'] = 4  # 非同花對子 4:1
                elif same_suit:
                    results['B Fab Pair'] = 1  # 同花非對子 1:1
            
            # 3. 閒家神奇4點
            if self.game.winner == 'Player' and self.game.player_score == 4:
                results['P Fabulous 4'] = 50  # 50:1
            
            # 4. 莊家神奇4點
            if self.game.winner == 'Banker' and self.game.banker_score == 4:
                results['B Fabulous 4'] = 25  # 25:1

        return results

    def update_balance(self):
        self.balance_label.config(text=f"Balance: ${self.balance:,}")
        if self.username != 'Guest':
            update_balance_in_json(self.username, self.balance)
        return self.balance

# 在Baccarat.py中的main函数
def main(initial_balance=10000, username="Guest"):
    app = BaccaratGUI(initial_balance, username)
    app.mainloop()
    return app.balance  # 正确返回数值

if __name__ == "__main__":
    # 独立运行时的示例调用
    final_balance = main()
    print(f"Final balance: {final_balance}")